"""
Utilidades compartilhadas pelas duas camadas.

Aqui ficam só as conversões básicas entre texto, bytes e bits. Quase tudo
no simulador trabalha com listas de bits (0s e 1s), então é prático ter um
lugar único para ir e voltar entre "texto que a pessoa digita" e "bits que
trafegam na rede".
"""


def texto_para_bytes(texto):
    """Converte o texto em bytes usando UTF-8 (suporta acentos)."""
    return texto.encode("utf-8")


def bytes_para_texto(dados):
    # 'replace' evita que um byte estragado pelo ruído derrube tudo:
    # ele vira o caractere de substituição em vez de lançar exceção.
    return bytes(dados).decode("utf-8", errors="replace")


def bytes_para_bits(dados):
    """Quebra cada byte em 8 bits, do mais significativo para o menos."""
    bits = []
    for byte in dados:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_para_bytes(bits):
    """Reagrupa os bits de 8 em 8. Bits sobrando no final são descartados."""
    dados = bytearray()
    for i in range(0, len(bits) - len(bits) % 8, 8):
        byte = 0
        for bit in bits[i:i + 8]:
            byte = (byte << 1) | bit
        dados.append(byte)
    return bytes(dados)


def texto_para_bits(texto):
    return bytes_para_bits(texto_para_bytes(texto))


def bits_para_texto(bits):
    return bytes_para_texto(bits_para_bytes(bits))
