# camada de enlace: enquadramento, deteccao e correcao de erro.
# contagem e byte stuffing trabalham com bytes; bit stuffing, paridade e hamming
# trabalham com listas de bits. o Simulador faz as conversoes.

import log

FLAG = 0x7E   # 0111 1110, delimitador de quadro
ESC = 0x7D    # escape do byte stuffing
FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]


# --- enquadramento ---

def enquadrar_contagem(dados, tam_max=255):
    # cada quadro comeca com um byte dizendo o proprio tamanho
    quadro = bytearray()
    for i in range(0, len(dados), tam_max - 1):
        bloco = dados[i:i + tam_max - 1]
        quadro.append(len(bloco) + 1)
        quadro.extend(bloco)
    log.registrar(f"  Enlace · enquadramento (contagem): {len(dados)} bytes → {len(quadro)} bytes")
    return bytes(quadro)


def desenquadrar_contagem(quadro):
    dados = bytearray()
    i = 0
    while i < len(quadro):
        n = quadro[i]
        if n == 0:        # se o ruido zera a contagem, para (senao trava em loop)
            break
        dados.extend(quadro[i + 1:i + n])
        i += n
    log.registrar(f"  Enlace · desenquadramento (contagem): {len(quadro)} bytes → {len(dados)} bytes")
    return bytes(dados)


def _inserir_bytes(bloco):
    # escapa com ESC todo byte de dado que seja igual a FLAG ou ESC
    saida = bytearray()
    for b in bloco:
        if b in (FLAG, ESC):
            saida.append(ESC)
        saida.append(b)
    return saida


def enquadrar_flag_bytes(dados, tam_max=255):
    quadro = bytearray()
    for i in range(0, len(dados), tam_max):
        quadro.append(FLAG)
        quadro.extend(_inserir_bytes(dados[i:i + tam_max]))
        quadro.append(FLAG)
    log.registrar(f"  Enlace · enquadramento (flag+byte stuffing): {len(dados)} bytes → {len(quadro)} bytes")
    return bytes(quadro)


def desenquadrar_flag_bytes(quadro):
    dados = bytearray()
    dentro = False
    escapado = False
    for b in quadro:
        if not dentro:
            if b == FLAG:
                dentro = True
            continue
        if escapado:            # veio depois de um ESC, entao e dado literal
            dados.append(b)
            escapado = False
        elif b == ESC:
            escapado = True
        elif b == FLAG:         # fecha o quadro
            dentro = False
        else:
            dados.append(b)
    log.registrar(f"  Enlace · desenquadramento (flag+byte stuffing): {len(quadro)} bytes → {len(dados)} bytes")
    return bytes(dados)


def _inserir_bits(bits):
    # insere um 0 depois de cinco 1s pra os dados nao imitarem a flag (seis 1s)
    saida = []
    seguidos = 0
    for bit in bits:
        saida.append(bit)
        if bit == 1:
            seguidos += 1
            if seguidos == 5:
                saida.append(0)
                seguidos = 0
        else:
            seguidos = 0
    return saida


def enquadrar_flag_bits(bits, tam_max=None):
    if tam_max:
        blocos = [bits[i:i + tam_max] for i in range(0, len(bits), tam_max)]
    else:
        blocos = [list(bits)]
    quadro = []
    for bloco in blocos:
        quadro += FLAG_BITS + _inserir_bits(bloco) + FLAG_BITS
    log.registrar(f"  Enlace · enquadramento (flag+bit stuffing): {len(bits)} bits → {len(quadro)} bits")
    return quadro


def desenquadrar_flag_bits(bits):
    dados = []
    i = 0
    n = len(bits)
    while i + 8 <= n:
        if bits[i:i + 8] != FLAG_BITS:   # procura a flag de abertura
            i += 1
            continue
        i += 8
        seguidos = 0
        while i < n:
            if bits[i:i + 8] == FLAG_BITS:   # flag de fechamento
                i += 8
                break
            bit = bits[i]
            i += 1
            dados.append(bit)
            if bit == 1:
                seguidos += 1
                if seguidos == 5:
                    i += 1            # pula o 0 que foi inserido no stuffing
                    seguidos = 0
            else:
                seguidos = 0
    log.registrar(f"  Enlace · desenquadramento (flag+bit stuffing): {len(bits)} bits → {len(dados)} bits")
    return dados


# --- deteccao de erro ---

def paridade_par(bits):
    return sum(bits) % 2   # bit que deixa a contagem de 1s par


def adicionar_paridade(dados):
    from Utils import bytes_para_bits
    p = paridade_par(bytes_para_bits(dados))
    log.registrar(f"  Enlace · paridade par: bit de paridade = {p}")
    return dados + bytes([p])


def verificar_paridade(dados_com_paridade):
    from Utils import bytes_para_bits
    if len(dados_com_paridade) < 2:      # quadro destruido pelo ruido
        log.registrar("  Enlace · verificação paridade: quadro curto demais → inválido")
        return b"", False
    dados, recebido = dados_com_paridade[:-1], dados_com_paridade[-1]
    calculado = paridade_par(bytes_para_bits(dados))
    ok = calculado == recebido
    log.registrar(f"  Enlace · verificação paridade: recebido={recebido}, calculado={calculado} → {'OK' if ok else 'ERRO'}")
    return dados, ok


def checksum_internet(dados):
    # soma palavras de 16 bits com vai-um circular e devolve o complemento de 1
    if len(dados) % 2:
        dados = dados + b"\x00"
    soma = 0
    for i in range(0, len(dados), 2):
        soma += (dados[i] << 8) | dados[i + 1]
        soma = (soma & 0xFFFF) + (soma >> 16)
    return (~soma) & 0xFFFF


def adicionar_checksum(dados):
    c = checksum_internet(dados)
    log.registrar(f"  Enlace · checksum: 0x{c:04x} anexado")
    return dados + bytes([c >> 8, c & 0xFF])


def verificar_checksum(dados_com_checksum):
    if len(dados_com_checksum) < 3:      # quadro destruido pelo ruido
        log.registrar("  Enlace · verificação checksum: quadro curto demais → inválido")
        return b"", False
    dados, recebido = dados_com_checksum[:-2], dados_com_checksum[-2:]
    valor = (recebido[0] << 8) | recebido[1]
    calculado = checksum_internet(dados)
    ok = calculado == valor
    log.registrar(f"  Enlace · verificação checksum: recebido=0x{valor:04x}, calculado=0x{calculado:04x} → {'OK' if ok else 'ERRO'}")
    return dados, ok


def crc32(dados):
    # crc-32 ieee 802 (mesmo do ethernet/zip), bit a bit, sem biblioteca.
    # e o resto da divisao polinomial em GF(2); 0xEDB88320 e o polinomio refletido
    crc = 0xFFFFFFFF
    for byte in dados:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF


def adicionar_crc(dados):
    c = crc32(dados)
    log.registrar(f"  Enlace · CRC-32: 0x{c:08x} anexado")
    return dados + bytes([(c >> 24) & 0xFF, (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF])


def verificar_crc(dados_com_crc):
    if len(dados_com_crc) < 5:           # quadro destruido pelo ruido
        log.registrar("  Enlace · verificação CRC-32: quadro curto demais → inválido")
        return b"", False
    dados, recebido = dados_com_crc[:-4], dados_com_crc[-4:]
    valor = int.from_bytes(recebido, "big")
    calculado = crc32(dados)
    ok = calculado == valor
    log.registrar(f"  Enlace · verificação CRC-32: recebido=0x{valor:08x}, calculado=0x{calculado:08x} → {'OK' if ok else 'ERRO'}")
    return dados, ok


# --- correcao de erro (Hamming 7,4) ---
# cada 4 bits viram 7 (paridades nas posicoes 1, 2 e 4).

def hamming_codificar(bits):
    entrada = len(bits)
    bits = list(bits)
    while len(bits) % 4:
        bits.append(0)
    saida = []
    for i in range(0, len(bits), 4):
        d1, d2, d3, d4 = bits[i:i + 4]
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p3 = d2 ^ d3 ^ d4
        saida += [p1, p2, d1, p3, d2, d3, d4]
    log.registrar(f"  Enlace · Hamming (codificação): {entrada} bits → {len(saida)} bits (cada 4 viram 7)")
    return saida


def hamming_decodificar(bits):
    dados = []
    corrigidos = 0
    blocos = 0
    for i in range(0, len(bits) - 6, 7):
        blocos += 1
        bloco = bits[i:i + 7]
        p1, p2, d1, p3, d2, d3, d4 = bloco
        s1 = p1 ^ d1 ^ d2 ^ d4
        s2 = p2 ^ d1 ^ d3 ^ d4
        s3 = p3 ^ d2 ^ d3 ^ d4
        pos = s1 + 2 * s2 + 4 * s3     # sindrome = posicao do bit errado (0 = ok)
        if pos != 0:
            corrigidos += 1
            bloco[pos - 1] ^= 1
            d1, d2, d3, d4 = bloco[2], bloco[4], bloco[5], bloco[6]
        dados += [d1, d2, d3, d4]
    log.registrar(f"  Enlace · Hamming (decodificação): {blocos} bloco(s), {corrigidos} bit(s) corrigido(s)")
    return dados, corrigidos
