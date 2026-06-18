"""
Implementação inicial da camada física.

Nesta etapa, simulamos a modulação digital banda-base:
- NRZ-Polar
- Manchester
- Bipolar

Os sinais são representados por valores elétricos em volts.
"""

# ----------------------------------------------------------------------
# ---------------------------- Funções de conversão ----------------------------
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# ---------------------------- Códigos de banda base ----------------------------
# ----------------------------------------------------------------------


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
    """

    bits = []

    for valor in sinal:
        if valor == 0:
            bits.append(0)
        else:
            bits.append(1)

    return bits

# ----------------------------------------------------------------------
# ---------------------------- Modulações ----------------------------
# ----------------------------------------------------------------------

def modular_amplitude_shift(bits):
    """
    Modulação ASK: "transforma os 0s e 1s em pulsos elétricos"

    Convenção usada:
    bit 1 -> +5V
    bit 0 -> 0V
    """
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal.append(5.0)
        else:
            sinal.append(0.0)
    return sinal

def demodular_amplitude_shift(sinal):
    """
    Decodificação ASK. 

    0V representa bit 0.
    Qualquer pulso positivo representa bit 1.
    """
    bits = []
    for valor in sinal:
        if valor > 0:
            bits.append(1)
        else:
            bits.append(0)
    return bits

def modular_frequencia_shift(bits):
    """
    Modulação FSK: "transforma os 0s e 1s em pulsos elétricos de diferentes frequências"

    Convenção usada:
    bit 1 -> +5V com frequência X
    bit 0 -> 0V com frequência Y
    """
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal.append(5.0)
        else:
            sinal.append(0.0)
    return sinal

def demodular_frequencia_shift(sinal):
    """
    Decodificação FSK. 

    0V representa bit 0.
    Qualquer pulso positivo representa bit 1.
    """
    bits = []
    for valor in sinal:
        if valor > 0:
            bits.append(1)
        else:
            bits.append(0)
    return bits

def modular_fase_shift(bits):
    """
    Modulação PSK: "transforma os 0s e 1s em pulsos elétricos de diferentes fases"

    Convenção usada:
    bit 1 -> +5V com fase X
    bit 0 -> 0V com fase Y
    """
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal.append(5.0)
        else:
            sinal.append(0.0)
    return sinal

def demodular_fase_shift(sinal):
    """
    Decodificação PSK. 

    0V representa bit 0.
    Qualquer pulso positivo representa bit 1.
    """
    bits = []
    for valor in sinal:
        if valor > 0:
            bits.append(1)
        else:
            bits.append(0)
    return bits

def modular_16_qam(bits):
    """
    Modulação 16-QAM: "transforma os 0s e 1s em pulsos elétricos"

    Convenção usada:
    bit 1 -> +5V
    bit 0 -> 0V
    """
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal.append(5.0)
        else:
            sinal.append(0.0)
    return sinal

def demodular_16_qam(sinal):
    """
    Decodificação 16-QAM. 

    0V representa bit 0.
    Qualquer pulso positivo representa bit 1.
    """
    bits = []
    for valor in sinal:
        if valor > 0:
            bits.append(1)
        else:
            bits.append(0)
    return bits