# o "meio" do diagrama: aplica o ruido e faz o transporte por socket.

import random
import struct

import log


def aplicar_ruido_gaussiano(sinal, sigma, media=0.0):
    if sigma <= 0:
        log.registrar(f"  Meio · sem ruído (σ=0): {len(sinal)} amostras passam intactas")
        return list(sinal)
    ruidoso = [v + random.gauss(media, sigma) for v in sinal]
    log.registrar(f"  Meio · ruído gaussiano σ={sigma} somado a {len(sinal)} amostras")
    return ruidoso


def _receber_exato(conexao, n):
    # recv pode vir picado; insiste ate juntar n bytes
    dados = bytearray()
    while len(dados) < n:
        parte = conexao.recv(n - len(dados))
        if not parte:
            raise ConnectionError("conexão fechada no meio do envio")
        dados.extend(parte)
    return bytes(dados)


def enviar_bytes(conexao, dados):
    # manda o tamanho antes do conteudo (tcp e fluxo continuo, sem fronteira de mensagem)
    conexao.sendall(struct.pack(">I", len(dados)) + dados)


def receber_bytes(conexao):
    (tamanho,) = struct.unpack(">I", _receber_exato(conexao, 4))
    return _receber_exato(conexao, tamanho)


def enviar_sinal(conexao, sinal):
    corpo = struct.pack(">I", len(sinal)) + struct.pack(">%dd" % len(sinal), *sinal)
    enviar_bytes(conexao, corpo)
    log.registrar(f"  Socket · sinal enviado pela rede ({len(sinal)} amostras)")


def receber_sinal(conexao):
    corpo = receber_bytes(conexao)
    (n,) = struct.unpack(">I", corpo[:4])
    sinal = list(struct.unpack(">%dd" % n, corpo[4:]))
    log.registrar(f"  Socket · sinal recebido da rede ({n} amostras)")
    return sinal
