# lado TX: monta o sinal, aplica o ruido do meio e manda pro receptor por socket.
# manda a config (json) primeiro e depois o sinal.
#
# uso:
#   python3 Transmissor.py "mensagem"        config padrao
#   python3 Transmissor.py "mensagem" 1.5    com sigma de ruido 1.5

import json
import socket
import sys

import canal
import log
import Simulador


def enviar(texto, cfg, host="127.0.0.1", porta=5000):
    log.iniciar("transmissor")
    log.registrar(f"TX » configuração: {cfg.como_dicionario()}")

    sinal = Simulador.transmitir(texto, cfg)
    sinal = canal.aplicar_ruido_gaussiano(sinal, cfg.sigma)   # o ruido entra aqui, antes de ir pra rede

    log.registrar(f"TX » conectando ao receptor em {host}:{porta}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexao:
        conexao.connect((host, porta))
        canal.enviar_bytes(conexao, json.dumps(cfg.como_dicionario()).encode())
        canal.enviar_sinal(conexao, sinal)

    log.registrar(f"TX » mensagem {texto!r} enviada ({len(sinal)} amostras, sigma={cfg.sigma})")
    log.encerrar()


def main():
    texto = sys.argv[1] if len(sys.argv) > 1 else "Mensagem de teste do transmissor"
    sigma = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    cfg = Simulador.Config(modulacao="nrz", enquadramento="flag_bytes",
                           edc="crc", sigma=sigma)
    enviar(texto, cfg)


if __name__ == "__main__":
    main()
