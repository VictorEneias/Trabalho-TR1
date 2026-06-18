# CamadaFisica.py

"""
Implementação da camada física.

Modulações digitais (banda-base):
- NRZ-Polar
- Manchester
- Bipolar

Modulações por portadora:
- ASK (Amplitude Shift Keying)
- FSK (Frequency Shift Keying)
- QPSK (Quadrature Phase Shift Keying)
- 16-QAM (16-Quadrature Amplitude Modulation)

Meio de comunicação com ruído gaussiano n(x, σ).
Os sinais são representados por valores elétricos em Volts.
"""

import math
import random


def texto_para_bits(texto):
    """
    Converte uma string de texto em uma lista de bits.

    Cada caractere é convertido para seu valor ASCII de 8 bits.
    Exemplo:
    'A' -> 01000001
    """

    bits = []

    for caractere in texto:
        valor_ascii = ord(caractere)
        binario = format(valor_ascii, "08b")

        for bit in binario:
            bits.append(int(bit))

    return bits


def bits_para_texto(bits):
    """
    Converte uma lista de bits de volta para texto.

    A cada 8 bits, formamos um caractere ASCII.
    """

    texto = ""

    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]

        if len(byte) < 8:
            break

        valor_binario = "".join(str(bit) for bit in byte)
        valor_ascii = int(valor_binario, 2)
        texto += chr(valor_ascii)

    return texto


def codificar_nrz_polar(bits):
    """
    Codificação NRZ-Polar.

    Convenção usada:
    bit 1 -> +1V
    bit 0 -> -1V
    """

    sinal = []

    for bit in bits:
        if bit == 1:
            sinal.append(1.0)
        else:
            sinal.append(-1.0)

    return sinal


def decodificar_nrz_polar(sinal):
    """
    Decodificação NRZ-Polar.

    Valores positivos são interpretados como 1.
    Valores negativos são interpretados como 0.
    """

    bits = []

    for valor in sinal:
        if valor > 0:
            bits.append(1)
        else:
            bits.append(0)

    return bits


def codificar_manchester(bits):
    """
    Codificação Manchester.

    Cada bit é representado por dois níveis de tensão.

    Convenção usada:
    bit 1 -> +1V seguido de -1V
    bit 0 -> -1V seguido de +1V
    """

    sinal = []

    for bit in bits:
        if bit == 1:
            sinal.append(1.0)
            sinal.append(-1.0)
        else:
            sinal.append(-1.0)
            sinal.append(1.0)

    return sinal


def decodificar_manchester(sinal):
    """
    Decodificação Manchester.

    Lê o sinal de dois em dois valores.
    """

    bits = []

    for i in range(0, len(sinal), 2):
        par = sinal[i:i + 2]

        if len(par) < 2:
            break

        primeiro = par[0]
        segundo = par[1]

        if primeiro > 0 and segundo < 0:
            bits.append(1)
        elif primeiro < 0 and segundo > 0:
            bits.append(0)
        else:
            raise ValueError("Sinal Manchester inválido encontrado.")

    return bits


def codificar_bipolar(bits):
    """
    Codificação Bipolar AMI.

    Convenção usada:
    bit 0 -> 0V
    bit 1 -> alterna entre +1V e -1V
    """

    sinal = []
    ultimo_pulso = -1.0

    for bit in bits:
        if bit == 0:
            sinal.append(0.0)
        else:
            ultimo_pulso *= -1
            sinal.append(ultimo_pulso)

    return sinal


def decodificar_bipolar(sinal):
    """
    Decodificação Bipolar.

    0V representa bit 0.
    Qualquer pulso positivo ou negativo representa bit 1.
    Usa limiar de 0.5V para tolerar ruído.
    """

    bits = []

    for valor in sinal:
        if abs(valor) < 0.5:
            bits.append(0)
        else:
            bits.append(1)

    return bits


# ---------------------------------------------------------------------------
# Parâmetros da modulação por portadora
# ---------------------------------------------------------------------------

AMOSTRAS_POR_SIMBOLO = 100  # amostras por período de símbolo
FREQUENCIA_PORTADORA = 1.0  # ciclos por período de símbolo
FREQUENCIA_FSK_0 = 1.0      # frequência do bit 0 no FSK
FREQUENCIA_FSK_1 = 2.0      # frequência do bit 1 no FSK
AMPLITUDE = 1.0             # amplitude da portadora em Volts


# ---------------------------------------------------------------------------
# Ruído gaussiano (meio de comunicação)
# ---------------------------------------------------------------------------

def adicionar_ruido_gaussiano(sinal, media=0.0, desvio_padrao=0.1):
    """
    Simula o meio de comunicação acrescentando ruído gaussiano n(media, desvio_padrao)
    a cada amostra do sinal (valores em V).
    """
    return [v + random.gauss(media, desvio_padrao) for v in sinal]


# ---------------------------------------------------------------------------
# ASK – Amplitude Shift Keying
# ---------------------------------------------------------------------------

def codificar_ask(bits, amplitude=AMPLITUDE, frequencia=FREQUENCIA_PORTADORA,
                  amostras=AMOSTRAS_POR_SIMBOLO):
    """
    ASK binário:
    bit 1 → A·cos(2π·f·t)
    bit 0 → 0 V
    """
    sinal = []
    for bit in bits:
        A = amplitude if bit == 1 else 0.0
        for n in range(amostras):
            sinal.append(A * math.cos(2 * math.pi * frequencia * n / amostras))
    return sinal


def decodificar_ask(sinal, amplitude=AMPLITUDE, frequencia=FREQUENCIA_PORTADORA,
                    amostras=AMOSTRAS_POR_SIMBOLO):
    """
    Demodulação ASK por correlação com a portadora.
    Decisão pelo limiar amplitude/2.
    """
    bits = []
    limiar = amplitude / 2
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        corr = (2 / amostras) * sum(
            bloco[n] * math.cos(2 * math.pi * frequencia * n / amostras)
            for n in range(len(bloco))
        )
        bits.append(1 if corr > limiar else 0)
    return bits


# ---------------------------------------------------------------------------
# FSK – Frequency Shift Keying
# ---------------------------------------------------------------------------

def codificar_fsk(bits, amplitude=AMPLITUDE, f0=FREQUENCIA_FSK_0, f1=FREQUENCIA_FSK_1,
                  amostras=AMOSTRAS_POR_SIMBOLO):
    """
    FSK binário:
    bit 0 → A·cos(2π·f0·t)
    bit 1 → A·cos(2π·f1·t)
    """
    sinal = []
    for bit in bits:
        f = f1 if bit == 1 else f0
        for n in range(amostras):
            sinal.append(amplitude * math.cos(2 * math.pi * f * n / amostras))
    return sinal


def decodificar_fsk(sinal, amplitude=AMPLITUDE, f0=FREQUENCIA_FSK_0, f1=FREQUENCIA_FSK_1,
                    amostras=AMOSTRAS_POR_SIMBOLO):
    """
    Demodulação FSK por correlação com f0 e f1 — vence a frequência de maior correlação.
    """
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        cor0 = sum(bloco[n] * math.cos(2 * math.pi * f0 * n / amostras) for n in range(len(bloco)))
        cor1 = sum(bloco[n] * math.cos(2 * math.pi * f1 * n / amostras) for n in range(len(bloco)))
        bits.append(1 if cor1 > cor0 else 0)
    return bits


# ---------------------------------------------------------------------------
# QPSK – Quadrature Phase Shift Keying
# ---------------------------------------------------------------------------

# Constelação Gray-coded: dibit (b0, b1) → (componente I, componente Q)
_QPSK_CONSTELACAO = {
    (0, 0): ( 1,  1),   # 45°
    (0, 1): (-1,  1),   # 135°
    (1, 1): (-1, -1),   # 225°
    (1, 0): ( 1, -1),   # 315°
}
_QPSK_CONSTELACAO_INV = {v: k for k, v in _QPSK_CONSTELACAO.items()}


def codificar_qpsk(bits, amplitude=AMPLITUDE, frequencia=FREQUENCIA_PORTADORA,
                   amostras=AMOSTRAS_POR_SIMBOLO):
    """
    QPSK: processa 2 bits por símbolo.
    s(t) = (A/√2) · [I·cos(2π·f·t) − Q·sin(2π·f·t)]
    """
    if len(bits) % 2 != 0:
        bits = bits + [0]

    fator = amplitude / math.sqrt(2)
    sinal = []
    for i in range(0, len(bits), 2):
        I, Q = _QPSK_CONSTELACAO[(bits[i], bits[i + 1])]
        for n in range(amostras):
            t = n / amostras
            sinal.append(fator * (I * math.cos(2 * math.pi * frequencia * t)
                                - Q * math.sin(2 * math.pi * frequencia * t)))
    return sinal


def decodificar_qpsk(sinal, amplitude=AMPLITUDE, frequencia=FREQUENCIA_PORTADORA,
                     amostras=AMOSTRAS_POR_SIMBOLO):
    """
    Demodulação coerente QPSK.
    Correlaciona com cos (canal I) e -sin (canal Q); decide pelo sinal de cada componente.
    """
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        I_r = (2 / amostras) * sum(
            bloco[n] * math.cos(2 * math.pi * frequencia * n / amostras)
            for n in range(len(bloco))
        )
        Q_r = -(2 / amostras) * sum(
            bloco[n] * math.sin(2 * math.pi * frequencia * n / amostras)
            for n in range(len(bloco))
        )
        I_dec = 1 if I_r >= 0 else -1
        Q_dec = 1 if Q_r >= 0 else -1
        bits.extend(_QPSK_CONSTELACAO_INV[(I_dec, Q_dec)])
    return bits


# ---------------------------------------------------------------------------
# 16-QAM – 16-Quadrature Amplitude Modulation
# ---------------------------------------------------------------------------

# Mapeamento Gray-coded: par de bits → nível de amplitude (I ou Q)
_QAM16_GRAY = {
    (0, 0): -3,
    (0, 1): -1,
    (1, 1):  1,
    (1, 0):  3,
}
_QAM16_GRAY_INV = {v: k for k, v in _QAM16_GRAY.items()}
_QAM16_NIVEIS = sorted(_QAM16_GRAY_INV.keys())  # [-3, -1, 1, 3]


def codificar_16qam(bits, frequencia=FREQUENCIA_PORTADORA, amostras=AMOSTRAS_POR_SIMBOLO):
    """
    16-QAM: processa 4 bits por símbolo (bits 0-1 → I, bits 2-3 → Q).
    s(t) = I·cos(2π·f·t) − Q·sin(2π·f·t)
    """
    while len(bits) % 4 != 0:
        bits = bits + [0]

    sinal = []
    for i in range(0, len(bits), 4):
        I = _QAM16_GRAY[(bits[i], bits[i + 1])]
        Q = _QAM16_GRAY[(bits[i + 2], bits[i + 3])]
        for n in range(amostras):
            t = n / amostras
            sinal.append(I * math.cos(2 * math.pi * frequencia * t)
                       - Q * math.sin(2 * math.pi * frequencia * t))
    return sinal


def decodificar_16qam(sinal, frequencia=FREQUENCIA_PORTADORA, amostras=AMOSTRAS_POR_SIMBOLO):
    """
    Demodulação coerente 16-QAM.
    Correlaciona com I e Q; quantiza cada componente para o nível mais próximo.
    """
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        I_r = (2 / amostras) * sum(
            bloco[n] * math.cos(2 * math.pi * frequencia * n / amostras)
            for n in range(len(bloco))
        )
        Q_r = -(2 / amostras) * sum(
            bloco[n] * math.sin(2 * math.pi * frequencia * n / amostras)
            for n in range(len(bloco))
        )
        I_dec = min(_QAM16_NIVEIS, key=lambda x: abs(x - I_r))
        Q_dec = min(_QAM16_NIVEIS, key=lambda x: abs(x - Q_r))
        bits.extend(_QAM16_GRAY_INV[I_dec] + _QAM16_GRAY_INV[Q_dec])
    return bits