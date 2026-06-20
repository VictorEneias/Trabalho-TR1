"""
Programa Receptor (lado RX).

Fica ouvindo em uma porta TCP. A cada conexão, lê a configuração e o sinal,
demodula/desenquadra/verifica e mostra o texto recuperado. Cada conexão é
tratada em uma thread, então mais de um transmissor pode se conectar ao mesmo
tempo (foi o que o professor pediu em aula).

Uso:
    python3 Receptor.py            # ouve em 127.0.0.1:5000
"""

import json
import socket
import threading

import canal
import Simulador


def atender(conexao, origem):
    with conexao:
        cfg = Simulador.Config(**json.loads(canal.receber_bytes(conexao)))
        sinal = canal.receber_sinal(conexao)
        texto, status = Simulador.receber(sinal, cfg)
        print(f"[{origem[0]}:{origem[1]}] {texto!r}  -> {status}")


def main(host="127.0.0.1", porta=5000):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, porta))
    servidor.listen()
    print(f"Receptor ouvindo em {host}:{porta} (Ctrl+C para sair)")

    try:
        while True:
            conexao, origem = servidor.accept()
            # uma thread por conexão -> aceita vários transmissores juntos
            threading.Thread(target=atender, args=(conexao, origem), daemon=True).start()
    except KeyboardInterrupt:
        print("\nReceptor encerrado.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
