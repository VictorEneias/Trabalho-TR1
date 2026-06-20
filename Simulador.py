"""
Simulador — a rotina principal que liga todas as camadas.

Caminho de IDA (transmissor):
    texto -> bytes -> [EDC] -> [enquadramento] -> bits -> modulação -> SINAL

Caminho de VOLTA (receptor):
    SINAL -> demodulação -> bits -> [desenquadramento] -> [verifica/corrige EDC]
          -> bytes -> texto

A função simular_local() faz o caminho inteiro na mesma máquina (ida + ruído +
volta) e é o que a interface gráfica usa. Os programas Transmissor.py e
Receptor.py reaproveitam transmitir() e receber() para fazer o mesmo, só que
com o sinal passando por um socket.

Em todas as etapas há chamadas a log.registrar(), então dá para acompanhar a
mensagem passo a passo no terminal e no arquivo de log.

Decisão de projeto: o usuário escolhe UMA técnica de modulação por vez (de banda-
base OU por portadora). As duas famílias estão implementadas em CamadaFisica.
"""

import CamadaFisica as fis
import CamadaEnlace as enl
import Utils
import canal
import log

# Cada modulação tem um par (codificar, decodificar). Centralizar aqui evita
# espalhar 'if tipo == ...' pelo código.
MODULACOES = {
    "nrz":        (fis.codificar_nrz_polar,  fis.decodificar_nrz_polar),
    "manchester": (fis.codificar_manchester, fis.decodificar_manchester),
    "bipolar":    (fis.codificar_bipolar,    fis.decodificar_bipolar),
    "ask":        (fis.codificar_ask,        fis.decodificar_ask),
    "fsk":        (fis.codificar_fsk,        fis.decodificar_fsk),
    "qpsk":       (fis.codificar_qpsk,       fis.decodificar_qpsk),
    "16qam":      (fis.codificar_16qam,      fis.decodificar_16qam),
}


class Config:
    """Junta todas as escolhas da simulação num lugar só."""

    def __init__(self, modulacao="nrz", enquadramento="flag_bytes",
                 edc="crc", tam_max=255, sigma=0.0):
        self.modulacao = modulacao
        self.enquadramento = enquadramento
        self.edc = edc
        self.tam_max = tam_max
        self.sigma = sigma

    def como_dicionario(self):
        return dict(self.__dict__)


# ---- Etapas internas da IDA ----------------------------------------------

def _aplicar_edc(dados, edc):
    """Anexa a redundância de detecção/correção escolhida. Devolve bytes."""
    log.registrar(f"TX » Enlace/EDC: aplicando '{edc}'")
    if edc == "nenhum":
        return dados
    if edc == "paridade":
        return enl.adicionar_paridade(dados)
    if edc == "checksum":
        return enl.adicionar_checksum(dados)
    if edc == "crc":
        return enl.adicionar_crc(dados)
    if edc == "hamming":
        bits = enl.hamming_codificar(Utils.bytes_para_bits(dados))
        while len(bits) % 8:          # alinha em bytes para o enquadramento
            bits.append(0)
        return Utils.bits_para_bytes(bits)
    raise ValueError("EDC desconhecido: " + edc)


def _enquadrar(protegido, cfg):
    """Enquadra os bytes protegidos e devolve a lista de bits a modular."""
    log.registrar(f"TX » Enlace/Enquadramento: aplicando '{cfg.enquadramento}'")
    if cfg.enquadramento == "contagem":
        return Utils.bytes_para_bits(enl.enquadrar_contagem(protegido, cfg.tam_max))
    if cfg.enquadramento == "flag_bytes":
        return Utils.bytes_para_bits(enl.enquadrar_flag_bytes(protegido, cfg.tam_max))
    if cfg.enquadramento == "flag_bits":
        bits = Utils.bytes_para_bits(protegido)
        return enl.enquadrar_flag_bits(bits, cfg.tam_max * 8)
    raise ValueError("enquadramento desconhecido: " + cfg.enquadramento)


def transmitir(texto, cfg):
    """texto -> SINAL (lista de tensões). Não aplica ruído."""
    log.registrar(f"TX » Aplicação: mensagem = {texto!r} ({len(texto)} caracteres)")
    dados = Utils.texto_para_bytes(texto)
    log.registrar(f"TX » texto→bytes (UTF-8): {log.previa_bytes(dados)}")
    protegido = _aplicar_edc(dados, cfg.edc)
    bits = _enquadrar(protegido, cfg)
    codificar, _ = MODULACOES[cfg.modulacao]
    sinal = codificar(bits)
    log.registrar(f"TX » sinal pronto para o meio: {len(sinal)} amostras")
    return sinal


# ---- Etapas internas da VOLTA --------------------------------------------

def _desenquadrar(bits, cfg):
    log.registrar(f"RX » Enlace/Desenquadramento: aplicando '{cfg.enquadramento}'")
    if cfg.enquadramento == "contagem":
        return enl.desenquadrar_contagem(Utils.bits_para_bytes(bits))
    if cfg.enquadramento == "flag_bytes":
        return enl.desenquadrar_flag_bytes(Utils.bits_para_bytes(bits))
    if cfg.enquadramento == "flag_bits":
        return Utils.bits_para_bytes(enl.desenquadrar_flag_bits(bits))
    raise ValueError("enquadramento desconhecido: " + cfg.enquadramento)


def _verificar_edc(protegido, edc):
    """Devolve (dados, mensagem_de_status)."""
    log.registrar(f"RX » Enlace/Verificação: aplicando '{edc}'")
    if edc == "nenhum":
        return protegido, "sem verificação"
    if edc == "paridade":
        dados, ok = enl.verificar_paridade(protegido)
        return dados, "OK" if ok else "ERRO detectado (paridade)"
    if edc == "checksum":
        dados, ok = enl.verificar_checksum(protegido)
        return dados, "OK" if ok else "ERRO detectado (checksum)"
    if edc == "crc":
        dados, ok = enl.verificar_crc(protegido)
        return dados, "OK" if ok else "ERRO detectado (CRC)"
    if edc == "hamming":
        bits, corrigidos = enl.hamming_decodificar(Utils.bytes_para_bits(protegido))
        dados = Utils.bits_para_bytes(bits)
        return dados, "OK (sem erros)" if corrigidos == 0 else f"{corrigidos} bit(s) corrigido(s)"
    raise ValueError("EDC desconhecido: " + edc)


def receber(sinal, cfg):
    """SINAL -> (texto, status)."""
    log.registrar(f"RX » Física: {len(sinal)} amostras chegaram do meio")
    _, decodificar = MODULACOES[cfg.modulacao]
    bits = decodificar(sinal)
    protegido = _desenquadrar(bits, cfg)
    dados, status = _verificar_edc(protegido, cfg.edc)
    texto = Utils.bytes_para_texto(dados)
    log.registrar(f"RX » bits→texto: {texto!r}  (status do EDC: {status})")
    return texto, status


def simular_local(texto, cfg):
    """Faz ida + ruído + volta na mesma máquina. Útil para a GUI e os testes."""
    log.iniciar("simulacao")
    log.registrar(f"configuração: {cfg.como_dicionario()}")
    sinal = transmitir(texto, cfg)
    sinal_com_ruido = canal.aplicar_ruido_gaussiano(sinal, cfg.sigma)
    texto_recuperado, status = receber(sinal_com_ruido, cfg)
    log.registrar(f"resultado: {texto_recuperado!r}  ({status})")
    log.encerrar()
    return {
        "sinal": sinal,
        "sinal_com_ruido": sinal_com_ruido,
        "texto": texto_recuperado,
        "status": status,
    }


def main():
    # Demonstração rápida no terminal (a entrega "de verdade" usa a GUI).
    cfg = Config(modulacao="nrz", enquadramento="flag_bytes", edc="crc", sigma=0.0)
    resultado = simular_local("Teleinformatica e Redes 1", cfg)
    print("Texto recuperado:", resultado["texto"])
    print("Status do EDC:", resultado["status"])
    print("Amostras de sinal geradas:", len(resultado["sinal"]))


if __name__ == "__main__":
    main()
