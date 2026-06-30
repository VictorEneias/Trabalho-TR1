# conversoes texto <-> bytes <-> bits, usadas pelas duas camadas


def texto_para_bytes(texto):
    return texto.encode("utf-8")


def bytes_para_texto(dados):
    # replace: um byte estragado pelo ruido vira "?" em vez de quebrar tudo
    return bytes(dados).decode("utf-8", errors="replace")


def bytes_para_bits(dados):
    bits = []
    for byte in dados:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_para_bytes(bits):
    dados = bytearray()
    for i in range(0, len(bits) - len(bits) % 8, 8):   # bits que sobram sao descartados
        byte = 0
        for bit in bits[i:i + 8]:
            byte = (byte << 1) | bit
        dados.append(byte)
    return bytes(dados)


def texto_para_bits(texto):
    return bytes_para_bits(texto_para_bytes(texto))


def bits_para_texto(bits):
    return bytes_para_texto(bits_para_bytes(bits))
