# rotina principal: liga as camadas.
# ida:   texto -> bytes -> [EDC] -> [enquadramento] -> bits -> modulacao -> sinal
# volta: sinal -> demodulacao -> bits -> [desenquadramento] -> [verifica/corrige] -> texto
# simular_local faz ida+ruido+volta na mesma maquina (usado pela GUI e nos testes);
# Transmissor/Receptor usam transmitir/receber com o sinal indo por socket.
# obs: escolhe-se UMA modulacao por vez (banda-base ou portadora).

import CamadaFisica as fis
import CamadaEnlace as enl
import Utils
import canal
import log

# nome -> (codificar, decodificar). evita um monte de if espalhado
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
    def __init__(self, modulacao="nrz", enquadramento="flag_bytes",
                 edc="crc", tam_max=255, sigma=0.0):
        self.modulacao = modulacao
        self.enquadramento = enquadramento
        self.edc = edc
        self.tam_max = tam_max
        self.sigma = sigma

    def como_dicionario(self):
        return dict(self.__dict__)


def _aplicar_edc(dados, edc):
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
        while len(bits) % 8:          # completa pra fechar byte (o enquadramento espera bytes)
            bits.append(0)
        return Utils.bits_para_bytes(bits)
    raise ValueError("EDC desconhecido: " + edc)


def _enquadrar(protegido, cfg):
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
    log.registrar(f"TX » Aplicação: mensagem = {texto!r} ({len(texto)} caracteres)")
    dados = Utils.texto_para_bytes(texto)
    log.registrar(f"TX » texto→bytes (UTF-8): {log.previa_bytes(dados)}")
    protegido = _aplicar_edc(dados, cfg.edc)
    bits = _enquadrar(protegido, cfg)
    codificar, _ = MODULACOES[cfg.modulacao]
    sinal = codificar(bits)
    log.registrar(f"TX » sinal pronto para o meio: {len(sinal)} amostras")
    return sinal


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
    log.registrar(f"RX » Física: {len(sinal)} amostras chegaram do meio")
    _, decodificar = MODULACOES[cfg.modulacao]
    bits = decodificar(sinal)
    protegido = _desenquadrar(bits, cfg)
    dados, status = _verificar_edc(protegido, cfg.edc)
    texto = Utils.bytes_para_texto(dados)
    log.registrar(f"RX » bits→texto: {texto!r}  (status do EDC: {status})")
    return texto, status


def simular_local(texto, cfg):
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
    # sem argumentos roda a config padrao; da pra passar tudo pela linha de comando
    import argparse
    p = argparse.ArgumentParser(
        description="Simula o caminho de uma mensagem pelas camadas física e de enlace.")
    p.add_argument("texto", nargs="?", default="Teleinformatica e Redes 1",
                   help="mensagem a transmitir (use aspas se tiver espaços)")
    p.add_argument("--mod", default="nrz", choices=list(MODULACOES),
                   help="modulação (padrão: nrz)")
    p.add_argument("--enq", default="flag_bytes",
                   choices=["contagem", "flag_bytes", "flag_bits"],
                   help="enquadramento (padrão: flag_bytes)")
    p.add_argument("--edc", default="crc",
                   choices=["nenhum", "paridade", "checksum", "crc", "hamming"],
                   help="detecção/correção de erro (padrão: crc)")
    p.add_argument("--tam", type=int, default=255,
                   help="tamanho máximo de quadro em bytes (padrão: 255)")
    p.add_argument("--sigma", type=float, default=0.0,
                   help="intensidade do ruído gaussiano no meio (padrão: 0.0)")
    args = p.parse_args()

    cfg = Config(modulacao=args.mod, enquadramento=args.enq, edc=args.edc,
                 tam_max=args.tam, sigma=args.sigma)
    resultado = simular_local(args.texto, cfg)

    print()
    print("Texto enviado:    ", repr(args.texto))
    print("Texto recuperado: ", repr(resultado["texto"]))
    print("Status do EDC:    ", resultado["status"])
    print("Amostras de sinal:", len(resultado["sinal"]))


if __name__ == "__main__":
    main()
