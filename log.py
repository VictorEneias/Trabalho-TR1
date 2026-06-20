"""
Log do simulador — acompanha a mensagem do transmissor até o receptor.

Cada mensagem enviada gera DOIS registros ao mesmo tempo: as linhas aparecem no
terminal E são gravadas em um arquivo .txt dentro da pasta `logs/` (criada
automaticamente). Assim dá para abrir o arquivo depois e reler, passo a passo,
tudo o que aconteceu com aquela mensagem.

Como o receptor pode atender vários transmissores ao mesmo tempo (uma thread por
conexão), cada thread tem o seu próprio arquivo de log. Por isso guardamos o
arquivo atual em um armazenamento "por thread" (`threading.local`) — os logs de
conexões diferentes não se misturam.

O log só funciona dentro de uma sessão (depois de `iniciar()`). Fora disso, as
chamadas a `registrar()` são ignoradas, o que mantém os testes silenciosos.
"""

import datetime
import os
import threading

_local = threading.local()
PASTA = os.path.join(os.path.dirname(__file__), "logs")


def iniciar(nome):
    """Abre um arquivo de log novo (por thread) e devolve o caminho dele."""
    os.makedirs(PASTA, exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    caminho = os.path.join(PASTA, f"{nome}_{carimbo}.txt")
    _local.arquivo = open(caminho, "w", encoding="utf-8")
    _local.nome = nome
    registrar(f"===== sessão '{nome}' iniciada =====")
    return caminho


def registrar(mensagem):
    """Escreve uma linha no terminal e no arquivo, se houver sessão aberta."""
    arquivo = getattr(_local, "arquivo", None)
    if arquivo is None:
        return
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    linha = f"[{hora}] [{getattr(_local, 'nome', '?')}] {mensagem}"
    print(linha)
    arquivo.write(linha + "\n")
    arquivo.flush()


def encerrar():
    """Fecha a sessão atual (e o arquivo) da thread."""
    arquivo = getattr(_local, "arquivo", None)
    if arquivo is not None:
        registrar("===== sessão encerrada =====")
        arquivo.close()
        _local.arquivo = None


def previa_bits(bits, n=24):
    """Mostra os primeiros bits e o total, para o log não ficar gigante."""
    corpo = "".join(str(b) for b in bits[:n])
    return f"{corpo}{'…' if len(bits) > n else ''} ({len(bits)} bits)"


def previa_bytes(dados, n=12):
    corpo = " ".join(f"{b:02x}" for b in dados[:n])
    return f"{corpo}{' …' if len(dados) > n else ''} ({len(dados)} bytes)"
