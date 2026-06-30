# logs do simulador: imprime no terminal e salva um .txt em logs/.
# cada execucao/conexao tem seu proprio arquivo (guardado por thread, pra nao misturar).

import datetime
import os
import threading

_local = threading.local()
PASTA = os.path.join(os.path.dirname(__file__), "logs")


def iniciar(nome):
    os.makedirs(PASTA, exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    caminho = os.path.join(PASTA, f"{nome}_{carimbo}.txt")
    _local.arquivo = open(caminho, "w", encoding="utf-8")
    _local.nome = nome
    registrar(f"===== sessão '{nome}' iniciada =====")
    return caminho


def registrar(mensagem):
    arquivo = getattr(_local, "arquivo", None)
    if arquivo is None:        # sem sessao aberta nao faz nada (deixa os testes quietos)
        return
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    linha = f"[{hora}] [{getattr(_local, 'nome', '?')}] {mensagem}"
    print(linha)
    arquivo.write(linha + "\n")
    arquivo.flush()


def encerrar():
    arquivo = getattr(_local, "arquivo", None)
    if arquivo is not None:
        registrar("===== sessão encerrada =====")
        arquivo.close()
        _local.arquivo = None


def previa_bits(bits, n=24):
    # mostra so o comeco pro log nao ficar gigante
    corpo = "".join(str(b) for b in bits[:n])
    return f"{corpo}{'…' if len(bits) > n else ''} ({len(bits)} bits)"


def previa_bytes(dados, n=12):
    corpo = " ".join(f"{b:02x}" for b in dados[:n])
    return f"{corpo}{' …' if len(dados) > n else ''} ({len(dados)} bytes)"
