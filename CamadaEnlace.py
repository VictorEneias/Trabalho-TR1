"""
Camada de Enlace do simulador.

Três responsabilidades, na ordem em que aparecem no enunciado:

  1. Enquadramento: delimitar onde cada quadro começa e termina, para o receptor
     saber separar a mensagem em pedaços. Três técnicas:
       - contagem de caracteres  (um cabeçalho diz o tamanho do quadro)
       - flags + inserção de bytes (byte stuffing)
       - flags + inserção de bits  (bit stuffing)

  2. Detecção de erro: anexar bits/bytes redundantes (EDC) que permitem ao
     receptor PERCEBER que algo chegou corrompido. Três técnicas:
       - bit de paridade par
       - checksum da Internet (soma em complemento de um)
       - CRC-32 (padrão IEEE 802)

  3. Correção de erro: além de detectar, CONSERTAR um bit trocado:
       - Hamming (7,4)

Convenção de tipos: enquadramento por contagem e por bytes trabalha com 'bytes';
o enquadramento por bits, a paridade e o Hamming trabalham com listas de bits.
CRC e checksum trabalham com 'bytes'. O Simulador faz as conversões necessárias.
"""

FLAG = 0x7E          # 0111 1110 — delimitador de quadro (byte e bit stuffing)
ESC = 0x7D           # 0111 1101 — caractere de escape (byte stuffing)
FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]


# ===========================================================================
# 1. ENQUADRAMENTO
# ===========================================================================

def enquadrar_contagem(dados, tam_max=255):
    """
    Contagem de caracteres: cada quadro começa com um byte dizendo seu tamanho
    (incluindo o próprio byte de contagem). Como esse byte vai de 0 a 255, cada
    quadro carrega no máximo tam_max-1 bytes de dados.
    """
    quadro = bytearray()
    for i in range(0, len(dados), tam_max - 1):
        bloco = dados[i:i + tam_max - 1]
        quadro.append(len(bloco) + 1)
        quadro.extend(bloco)
    return bytes(quadro)


def desenquadrar_contagem(quadro):
    dados = bytearray()
    i = 0
    while i < len(quadro):
        n = quadro[i]            # tamanho do quadro atual
        dados.extend(quadro[i + 1:i + n])
        i += n                   # pula para o próximo cabeçalho
    return bytes(dados)


def _inserir_bytes(bloco):
    # Sempre que um byte de dado for igual a FLAG ou ESC, colocamos um ESC antes.
    # Assim o receptor não confunde dado com delimitador.
    saida = bytearray()
    for b in bloco:
        if b in (FLAG, ESC):
            saida.append(ESC)
        saida.append(b)
    return saida


def enquadrar_flag_bytes(dados, tam_max=255):
    """Flags + byte stuffing: cada quadro fica entre dois bytes FLAG."""
    quadro = bytearray()
    for i in range(0, len(dados), tam_max):
        quadro.append(FLAG)
        quadro.extend(_inserir_bytes(dados[i:i + tam_max]))
        quadro.append(FLAG)
    return bytes(quadro)


def desenquadrar_flag_bytes(quadro):
    dados = bytearray()
    dentro = False
    escapado = False
    for b in quadro:
        if not dentro:
            if b == FLAG:       # achou abertura de quadro
                dentro = True
            continue
        if escapado:            # byte anterior foi ESC, então este é dado literal
            dados.append(b)
            escapado = False
        elif b == ESC:
            escapado = True
        elif b == FLAG:         # fechamento do quadro
            dentro = False
        else:
            dados.append(b)
    return bytes(dados)


def _inserir_bits(bits):
    # Depois de cinco 1s seguidos inserimos um 0. Isso impede que os dados
    # gerem por acaso o padrão da FLAG (que tem seis 1s).
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
    """Flags + bit stuffing: cada quadro fica entre dois padrões FLAG_BITS."""
    if tam_max:
        blocos = [bits[i:i + tam_max] for i in range(0, len(bits), tam_max)]
    else:
        blocos = [list(bits)]
    quadro = []
    for bloco in blocos:
        quadro += FLAG_BITS + _inserir_bits(bloco) + FLAG_BITS
    return quadro


def desenquadrar_flag_bits(bits):
    dados = []
    i = 0
    n = len(bits)
    while i + 8 <= n:
        if bits[i:i + 8] != FLAG_BITS:   # procura a FLAG de abertura
            i += 1
            continue
        i += 8
        seguidos = 0
        while i < n:
            if bits[i:i + 8] == FLAG_BITS:   # FLAG de fechamento
                i += 8
                break
            bit = bits[i]
            i += 1
            dados.append(bit)
            if bit == 1:
                seguidos += 1
                if seguidos == 5:
                    i += 1            # descarta o 0 que foi inserido no stuffing
                    seguidos = 0
            else:
                seguidos = 0
    return dados


# ===========================================================================
# 2. DETECÇÃO DE ERRO
# ===========================================================================

def paridade_par(bits):
    """Retorna o bit (0 ou 1) que torna par a quantidade de 1s."""
    return sum(bits) % 2


def adicionar_paridade(dados):
    """Anexa um byte 0x00/0x01 com o bit de paridade par de todos os bits."""
    from Utils import bytes_para_bits
    return dados + bytes([paridade_par(bytes_para_bits(dados))])


def verificar_paridade(dados_com_paridade):
    from Utils import bytes_para_bits
    dados, recebido = dados_com_paridade[:-1], dados_com_paridade[-1]
    ok = paridade_par(bytes_para_bits(dados)) == recebido
    return dados, ok


def checksum_internet(dados):
    """
    Checksum da Internet em 16 bits: soma as palavras de 16 bits acumulando o
    'vai-um' de volta no fim (end-around carry) e devolve o complemento de um.
    A graça é que, no receptor, somar tudo de novo (dados + checksum) dá 0xFFFF
    quando não houve erro.
    """
    if len(dados) % 2:
        dados = dados + b"\x00"     # completa para ter um número par de bytes
    soma = 0
    for i in range(0, len(dados), 2):
        soma += (dados[i] << 8) | dados[i + 1]
        soma = (soma & 0xFFFF) + (soma >> 16)
    return (~soma) & 0xFFFF


def adicionar_checksum(dados):
    c = checksum_internet(dados)
    return dados + bytes([c >> 8, c & 0xFF])


def verificar_checksum(dados_com_checksum):
    dados, recebido = dados_com_checksum[:-2], dados_com_checksum[-2:]
    valor = (recebido[0] << 8) | recebido[1]
    ok = checksum_internet(dados) == valor
    return dados, ok


def crc32(dados):
    """
    CRC-32 do IEEE 802 (mesmo polinômio do Ethernet/ZIP). É uma divisão de
    polinômios em GF(2): o "resto" da divisão dos dados pelo polinômio gerador
    vira a assinatura. Implementação bit a bit, sem tabela e sem biblioteca.
    """
    crc = 0xFFFFFFFF
    for byte in dados:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320   # polinômio refletido
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF


def adicionar_crc(dados):
    c = crc32(dados)
    return dados + bytes([(c >> 24) & 0xFF, (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF])


def verificar_crc(dados_com_crc):
    dados, recebido = dados_com_crc[:-4], dados_com_crc[-4:]
    valor = int.from_bytes(recebido, "big")
    ok = crc32(dados) == valor
    return dados, ok


# ===========================================================================
# 3. CORREÇÃO DE ERRO — Hamming (7,4)
# ===========================================================================
# Cada 4 bits de dado viram 7 bits: 3 bits de paridade são posicionados de modo
# que, se um único bit chegar trocado, a "síndrome" aponta exatamente qual foi.

def hamming_codificar(bits):
    bits = list(bits)
    while len(bits) % 4:
        bits.append(0)              # completa o último grupo de 4
    saida = []
    for i in range(0, len(bits), 4):
        d1, d2, d3, d4 = bits[i:i + 4]
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p3 = d2 ^ d3 ^ d4
        saida += [p1, p2, d1, p3, d2, d3, d4]
    return saida


def hamming_decodificar(bits):
    """Devolve (bits_de_dados, quantidade_de_bits_corrigidos)."""
    dados = []
    corrigidos = 0
    for i in range(0, len(bits) - 6, 7):
        bloco = bits[i:i + 7]
        p1, p2, d1, p3, d2, d3, d4 = bloco
        # Recalcula as paridades; a síndrome (s3 s2 s1) é a posição do erro.
        s1 = p1 ^ d1 ^ d2 ^ d4
        s2 = p2 ^ d1 ^ d3 ^ d4
        s3 = p3 ^ d2 ^ d3 ^ d4
        pos = s1 + 2 * s2 + 4 * s3
        if pos != 0:
            corrigidos += 1
            bloco[pos - 1] ^= 1
            d1, d2, d3, d4 = bloco[2], bloco[4], bloco[5], bloco[6]
        dados += [d1, d2, d3, d4]
    return dados, corrigidos
