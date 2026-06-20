"""
Camada Física do simulador.

Transforma bits em sinal elétrico (lista de tensões em Volts) e faz o caminho
de volta no receptor. São dois grupos de técnicas:

  - Modulação em banda-base: o próprio bit vira nível de tensão (NRZ, Manchester,
    Bipolar). Não há portadora, é o "sinal cru".
  - Modulação por portadora: os bits modulam uma senoide (ASK, FSK, QPSK, 16-QAM).
    É o que de fato vai para o ar / cabo em sistemas reais.

A demodulação por portadora usa correlação: multiplicamos o trecho recebido pela
mesma senoide usada na transmissão e somamos. Se o trecho "parece" com a senoide,
a soma dá um valor grande; se não, dá perto de zero. É assim que decidimos o bit
mesmo com algum ruído por cima.

O ruído do meio NÃO entra aqui — ele é responsabilidade do canal (canal.py),
seguindo o diagrama do enunciado (o ruído pertence ao "meio de comunicação").
"""

import math

# Parâmetros das portadoras. AMOSTRAS_POR_SIMBOLO é quantos pontos usamos para
# desenhar um período de símbolo — quanto maior, mais "redonda" fica a senoide.
AMOSTRAS_POR_SIMBOLO = 100
FREQUENCIA_PORTADORA = 1.0   # ciclos por símbolo (ASK, PSK, QAM)
FREQ_FSK_0 = 1.0             # frequência que representa o bit 0 no FSK
FREQ_FSK_1 = 2.0             # frequência que representa o bit 1 no FSK
AMPLITUDE = 1.0             # amplitude da portadora, em Volts


# ---- Banda-base -----------------------------------------------------------

def codificar_nrz_polar(bits):
    """NRZ-Polar: bit 1 vira +1V e bit 0 vira -1V. Um nível por bit."""
    return [1.0 if bit == 1 else -1.0 for bit in bits]


def decodificar_nrz_polar(sinal):
    return [1 if v > 0 else 0 for v in sinal]


def codificar_manchester(bits):
    """
    Manchester: cada bit vira uma transição no meio do tempo de bit.
    Usamos a convenção: 1 = descida (+1 depois -1), 0 = subida (-1 depois +1).
    Por isso cada bit gera DOIS níveis de tensão.
    """
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal += [1.0, -1.0]
        else:
            sinal += [-1.0, 1.0]
    return sinal


def decodificar_manchester(sinal):
    bits = []
    # Lemos de dois em dois, porque cada bit ocupou duas amostras na codificação.
    for i in range(0, len(sinal) - 1, 2):
        bits.append(1 if sinal[i] > sinal[i + 1] else 0)
    return bits


def codificar_bipolar(bits):
    """
    Bipolar AMI: bit 0 fica em 0V e bit 1 alterna entre +1V e -1V a cada
    ocorrência. Essa alternância é o truque do AMI: dois pulsos seguidos de
    mesma polaridade indicariam erro, o que ajuda a detectar problemas.
    """
    sinal = []
    ultimo = -1.0  # começa em -1 para o primeiro 1 sair como +1
    for bit in bits:
        if bit == 0:
            sinal.append(0.0)
        else:
            ultimo = -ultimo
            sinal.append(ultimo)
    return sinal


def decodificar_bipolar(sinal):
    # Perto de zero é bit 0; qualquer pulso (positivo ou negativo) é bit 1.
    # O limiar de 0.5V dá uma folga para tolerar ruído.
    return [0 if abs(v) < 0.5 else 1 for v in sinal]


# ---- ASK ------------------------------------------------------------------

def codificar_ask(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    """ASK: bit 1 liga a portadora (amplitude A), bit 0 desliga (0V)."""
    sinal = []
    for bit in bits:
        a = AMPLITUDE if bit == 1 else 0.0
        for n in range(amostras):
            sinal.append(a * math.cos(2 * math.pi * FREQUENCIA_PORTADORA * n / amostras))
    return sinal


def decodificar_ask(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    limiar = AMPLITUDE / 2
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        energia = _correlacao(bloco, FREQUENCIA_PORTADORA, amostras)
        bits.append(1 if energia > limiar else 0)
    return bits


# ---- FSK ------------------------------------------------------------------

def codificar_fsk(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    """FSK: o bit escolhe a frequência da portadora (f0 para 0, f1 para 1)."""
    sinal = []
    for bit in bits:
        f = FREQ_FSK_1 if bit == 1 else FREQ_FSK_0
        for n in range(amostras):
            sinal.append(AMPLITUDE * math.cos(2 * math.pi * f * n / amostras))
    return sinal


def decodificar_fsk(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        # Testamos as duas frequências; vence a que tiver maior correlação.
        c0 = _correlacao(bloco, FREQ_FSK_0, amostras)
        c1 = _correlacao(bloco, FREQ_FSK_1, amostras)
        bits.append(1 if c1 > c0 else 0)
    return bits


# ---- QPSK -----------------------------------------------------------------

# QPSK manda 2 bits por símbolo escolhendo a fase da portadora. Cada par de bits
# (dibit) vira um ponto (I, Q) na constelação. A codificação Gray garante que
# pontos vizinhos diferem em só 1 bit, reduzindo erros.
_QPSK = {
    (0, 0): (1, 1),
    (0, 1): (-1, 1),
    (1, 1): (-1, -1),
    (1, 0): (1, -1),
}
_QPSK_INV = {v: k for k, v in _QPSK.items()}


def codificar_qpsk(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = _completar(bits, 2)  # QPSK consome bits de 2 em 2
    fator = AMPLITUDE / math.sqrt(2)
    sinal = []
    for i in range(0, len(bits), 2):
        I, Q = _QPSK[(bits[i], bits[i + 1])]
        for n in range(amostras):
            t = n / amostras
            sinal.append(fator * (I * math.cos(2 * math.pi * FREQUENCIA_PORTADORA * t)
                                  - Q * math.sin(2 * math.pi * FREQUENCIA_PORTADORA * t)))
    return sinal


def decodificar_qpsk(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        # Projetamos o sinal nos eixos cosseno (I) e -seno (Q).
        I = _correlacao(bloco, FREQUENCIA_PORTADORA, amostras)
        Q = -_correlacao_seno(bloco, FREQUENCIA_PORTADORA, amostras)
        ponto = (1 if I >= 0 else -1, 1 if Q >= 0 else -1)
        bits += list(_QPSK_INV[ponto])
    return bits


# ---- 16-QAM ---------------------------------------------------------------

# 16-QAM manda 4 bits por símbolo: 2 bits escolhem o nível de I e 2 o nível de Q.
# Os níveis -3,-1,1,3 formam uma grade 4x4 de 16 pontos. Mapeamento Gray também.
_QAM_GRAY = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}
_QAM_GRAY_INV = {v: k for k, v in _QAM_GRAY.items()}
_QAM_NIVEIS = sorted(_QAM_GRAY_INV)  # [-3, -1, 1, 3]


def codificar_16qam(bits, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = _completar(bits, 4)  # 4 bits por símbolo
    sinal = []
    for i in range(0, len(bits), 4):
        I = _QAM_GRAY[(bits[i], bits[i + 1])]
        Q = _QAM_GRAY[(bits[i + 2], bits[i + 3])]
        for n in range(amostras):
            t = n / amostras
            sinal.append(I * math.cos(2 * math.pi * FREQUENCIA_PORTADORA * t)
                         - Q * math.sin(2 * math.pi * FREQUENCIA_PORTADORA * t))
    return sinal


def decodificar_16qam(sinal, amostras=AMOSTRAS_POR_SIMBOLO):
    bits = []
    for i in range(0, len(sinal), amostras):
        bloco = sinal[i:i + amostras]
        I = _correlacao(bloco, FREQUENCIA_PORTADORA, amostras)
        Q = -_correlacao_seno(bloco, FREQUENCIA_PORTADORA, amostras)
        # Arredonda cada componente para o nível mais próximo da grade.
        I_nivel = min(_QAM_NIVEIS, key=lambda nivel: abs(nivel - I))
        Q_nivel = min(_QAM_NIVEIS, key=lambda nivel: abs(nivel - Q))
        bits += list(_QAM_GRAY_INV[I_nivel]) + list(_QAM_GRAY_INV[Q_nivel])
    return bits


# ---- Apoio interno --------------------------------------------------------

def _correlacao(bloco, freq, amostras):
    """Correlação do bloco com cos(2*pi*freq*t). Mede 'quanto' de cosseno tem."""
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
    """Completa a lista com zeros até o tamanho ser múltiplo de 'multiplo'."""
    falta = (-len(bits)) % multiplo
    return list(bits) + [0] * falta
