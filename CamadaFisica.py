# camada fisica: bits <-> sinal (lista de tensoes em V).
# banda-base (nrz, manchester, bipolar) e portadora (ask, fsk, qpsk, 16qam).
# a demodulacao da portadora usa correlacao; o ruido fica no canal.py, nao aqui.

import math

import log

AMOSTRAS_POR_SIMBOLO = 100   # amostras por simbolo nas portadoras
FREQUENCIA_PORTADORA = 1.0
FREQ_FSK_0 = 1.0
FREQ_FSK_1 = 2.0
AMPLITUDE = 1.0


def codificar_nrz_polar(bits):
    # 1 -> +1V, 0 -> -1V
    sinal = [1.0 if bit == 1 else -1.0 for bit in bits]
    log.registrar(f"  Física · modulação NRZ-Polar: {len(bits)} bits → {len(sinal)} amostras (V)")
    return sinal


def decodificar_nrz_polar(sinal):
    bits = [1 if v > 0 else 0 for v in sinal]
    log.registrar(f"  Física · demodulação NRZ-Polar: {len(sinal)} amostras → {len(bits)} bits")
    return bits


def codificar_manchester(bits):
    # 1 desce (+1,-1) e 0 sobe (-1,+1): dois niveis por bit
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal += [1.0, -1.0]
        else:
            sinal += [-1.0, 1.0]
    log.registrar(f"  Física · modulação Manchester: {len(bits)} bits → {len(sinal)} amostras (V)")
    return sinal


def decodificar_manchester(sinal):
    bits = []
    for i in range(0, len(sinal) - 1, 2):   # le de dois em dois
        bits.append(1 if sinal[i] > sinal[i + 1] else 0)
    log.registrar(f"  Física · demodulação Manchester: {len(sinal)} amostras → {len(bits)} bits")
    return bits


def codificar_bipolar(bits):
    # 0 -> 0V; os 1 alternam +1/-1 (AMI). comeca em -1 pro primeiro 1 sair +1
    sinal = []
    ultimo = -1.0
    for bit in bits:
        if bit == 0:
            sinal.append(0.0)
        else:
            ultimo = -ultimo
            sinal.append(ultimo)
    log.registrar(f"  Física · modulação Bipolar (AMI): {len(bits)} bits → {len(sinal)} amostras (V)")
    return sinal


def decodificar_bipolar(sinal):
    # perto de zero = 0; qualquer pulso = 1. limiar 0.5 da folga pro ruido
    bits = [0 if abs(v) < 0.5 else 1 for v in sinal]
    log.registrar(f"  Física · demodulação Bipolar (AMI): {len(sinal)} amostras → {len(bits)} bits")
    return bits


def codificar_ask(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    # 1 liga a portadora, 0 desliga (0V)
    sinal = []
    for bit in bits:
        a = AMPLITUDE if bit == 1 else 0.0
        for n in range(amostras):
            sinal.append(a * math.cos(2 * math.pi * FREQUENCIA_PORTADORA * n / amostras))
    log.registrar(f"  Física · modulação ASK: {len(bits)} bits → {len(sinal)} amostras (V)")
    return sinal


def decodificar_ask(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    limiar = AMPLITUDE / 2
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        energia = _correlacao(bloco, FREQUENCIA_PORTADORA, amostras)
        bits.append(1 if energia > limiar else 0)   # correlacao acima do limiar = 1
    log.registrar(f"  Física · demodulação ASK: {len(sinal)} amostras → {len(bits)} bits")
    return bits


def codificar_fsk(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    # o bit escolhe a frequencia (f0 para 0, f1 para 1)
    sinal = []
    for bit in bits:
        f = FREQ_FSK_1 if bit == 1 else FREQ_FSK_0
        for n in range(amostras):
            sinal.append(AMPLITUDE * math.cos(2 * math.pi * f * n / amostras))
    log.registrar(f"  Física · modulação FSK: {len(bits)} bits → {len(sinal)} amostras (V)")
    return sinal


def decodificar_fsk(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        c0 = _correlacao(bloco, FREQ_FSK_0, amostras)
        c1 = _correlacao(bloco, FREQ_FSK_1, amostras)
        bits.append(1 if c1 > c0 else 0)   # vence a frequencia de maior correlacao
    log.registrar(f"  Física · demodulação FSK: {len(sinal)} amostras → {len(bits)} bits")
    return bits


# qpsk: 2 bits por simbolo (4 fases). gray pra pontos vizinhos diferirem 1 bit
_QPSK = {
    (0, 0): (1, 1),
    (0, 1): (-1, 1),
    (1, 1): (-1, -1),
    (1, 0): (1, -1),
}
_QPSK_INV = {v: k for k, v in _QPSK.items()}


def codificar_qpsk(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = _completar(bits, 2)   # consome de 2 em 2
    fator = AMPLITUDE / math.sqrt(2)
    sinal = []
    for i in range(0, len(bits), 2):
        I, Q = _QPSK[(bits[i], bits[i + 1])]
        for n in range(amostras):
            t = n / amostras
            sinal.append(fator * (I * math.cos(2 * math.pi * FREQUENCIA_PORTADORA * t)
                                  - Q * math.sin(2 * math.pi * FREQUENCIA_PORTADORA * t)))
    log.registrar(f"  Física · modulação QPSK: {len(bits)} bits → {len(sinal)} amostras (V)")
    return sinal


def decodificar_qpsk(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        I = _correlacao(bloco, FREQUENCIA_PORTADORA, amostras)       # eixo cosseno
        Q = -_correlacao_seno(bloco, FREQUENCIA_PORTADORA, amostras)  # eixo -seno
        ponto = (1 if I >= 0 else -1, 1 if Q >= 0 else -1)
        bits += list(_QPSK_INV[ponto])
    log.registrar(f"  Física · demodulação QPSK: {len(sinal)} amostras → {len(bits)} bits")
    return bits


# 16qam: 4 bits por simbolo. niveis -3,-1,1,3 em I e Q, com gray
_QAM_GRAY = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}
_QAM_GRAY_INV = {v: k for k, v in _QAM_GRAY.items()}
_QAM_NIVEIS = sorted(_QAM_GRAY_INV)


def codificar_16qam(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = _completar(bits, 4)   # consome de 4 em 4
    sinal = []
    for i in range(0, len(bits), 4):
        I = _QAM_GRAY[(bits[i], bits[i + 1])]
        Q = _QAM_GRAY[(bits[i + 2], bits[i + 3])]
        for n in range(amostras):
            t = n / amostras
            sinal.append(I * math.cos(2 * math.pi * FREQUENCIA_PORTADORA * t)
                         - Q * math.sin(2 * math.pi * FREQUENCIA_PORTADORA * t))
    log.registrar(f"  Física · modulação 16-QAM: {len(bits)} bits → {len(sinal)} amostras (V)")
    return sinal


def decodificar_16qam(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        I = _correlacao(bloco, FREQUENCIA_PORTADORA, amostras)
        Q = -_correlacao_seno(bloco, FREQUENCIA_PORTADORA, amostras)
        I_nivel = min(_QAM_NIVEIS, key=lambda nivel: abs(nivel - I))   # nivel mais proximo
        Q_nivel = min(_QAM_NIVEIS, key=lambda nivel: abs(nivel - Q))
        bits += list(_QAM_GRAY_INV[I_nivel]) + list(_QAM_GRAY_INV[Q_nivel])
    log.registrar(f"  Física · demodulação 16-QAM: {len(sinal)} amostras → {len(bits)} bits")
    return bits


def _correlacao(bloco, freq, amostras):
    # quanto o bloco "parece" com cos(2pi f t)
    return (2 / amostras) * sum(
        bloco[n] * math.cos(2 * math.pi * freq * n / amostras)
        for n in range(len(bloco))
    )


def _correlacao_seno(bloco, freq, amostras):
    return (2 / amostras) * sum(
        bloco[n] * math.sin(2 * math.pi * freq * n / amostras)
        for n in range(len(bloco))
    )


def _completar(bits, multiplo):
    falta = (-len(bits)) % multiplo
    return list(bits) + [0] * falta
