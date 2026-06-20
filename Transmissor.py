"""
Programa Transmissor (lado TX).

Monta o sinal a partir do texto, adiciona o ruído do meio e envia para o
receptor por um socket TCP. Manda primeiro a configuração (em JSON) para o
receptor saber como demodular, e depois o sinal.

Uso:
    python3 Transmissor.py "mensagem"           # usa a config padrão
    python3 Transmissor.py "mensagem" 1.5       # com sigma de ruído = 1.5
"""

import json
import socket
import sys

import canal
import Simulador


def enviar(texto, cfg, host="127.0.0.1", porta=5000):
    sinal = Simulador.transmitir(texto, cfg)
    # O ruído pertence ao meio; aplicamos aqui, logo antes de "soltar na rede".
    sinal = canal.aplicar_ruido_gaussiano(sinal, cfg.sigma)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexao:
        conexao.connect((host, porta))
        canal.enviar_bytes(conexao, json.dumps(cfg.como_dicionario()).encode())
        canal.enviar_sinal(conexao, sinal)

    print(f"Enviado: {texto!r}  ({len(sinal)} amostras, sigma={cfg.sigma})")


def main():
    texto = sys.argv[1] if len(sys.argv) > 1 else "Mensagem de teste do transmissor"
    sigma = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    cfg = Simulador.Config(modulacao="nrz", enquadramento="flag_bytes",
                           edc="crc", sigma=sigma)
    enviar(texto, cfg)


if __name__ == "__main__":
    main()
