"""
Canal de comunicação — o "meio" do diagrama do enunciado.

Tem duas funções bem distintas:

  1. O ruído: o meio nunca é perfeito. Somamos a cada amostra do sinal um valor
     sorteado de uma gaussiana n(media, sigma). Quanto maior o sigma, mais o
     sinal chega "tremido" no receptor. É aqui que mora a graça do trabalho:
     ver até onde cada modulação/EDC aguenta antes de errar.

  2. O transporte por socket: como o transmissor e o receptor podem ser dois
     programas separados (até em máquinas diferentes), precisamos enviar o sinal
     pela rede. Como TCP é um fluxo contínuo de bytes, sempre mandamos primeiro
     o TAMANHO e depois o conteúdo, para o outro lado saber onde uma mensagem
     termina e a próxima começa.
"""

import random
import struct


def aplicar_ruido_gaussiano(sinal, sigma, media=0.0):
    """Soma ruído gaussiano n(media, sigma) a cada amostra (Volts)."""
    if sigma <= 0:
        return list(sinal)
    return [v + random.gauss(media, sigma) for v in sinal]


def _receber_exato(conexao, n):
    # recv() pode devolver menos bytes do que pedimos; insistimos até juntar n.
    dados = bytearray()
    while len(dados) < n:
        parte = conexao.recv(n - len(dados))
        if not parte:
            raise ConnectionError("conexão fechada no meio do envio")
        dados.extend(parte)
    return bytes(dados)


def enviar_bytes(conexao, dados):
    """Envia [4 bytes de tamanho][conteúdo]."""
    conexao.sendall(struct.pack(">I", len(dados)) + dados)


def receber_bytes(conexao):
    (tamanho,) = struct.unpack(">I", _receber_exato(conexao, 4))
    return _receber_exato(conexao, tamanho)


def enviar_sinal(conexao, sinal):
    """Empacota a lista de tensões como doubles e envia."""
    corpo = struct.pack(">I", len(sinal)) + struct.pack(">%dd" % len(sinal), *sinal)
    enviar_bytes(conexao, corpo)


def receber_sinal(conexao):
    corpo = receber_bytes(conexao)
    (n,) = struct.unpack(">I", corpo[:4])
    return list(struct.unpack(">%dd" % n, corpo[4:]))
