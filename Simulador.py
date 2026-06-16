# Simulador.py

from CamadaFisica import (
    texto_para_bits,
    bits_para_texto,
    codificar_nrz_polar,
    decodificar_nrz_polar,
    codificar_manchester,
    decodificar_manchester,
    codificar_bipolar,
    decodificar_bipolar
)


def testar_modulacao(nome, bits, codificador, decodificador):
    print("=" * 60)
    print(f"Testando modulação: {nome}")

    sinal = codificador(bits)
    bits_recebidos = decodificador(sinal)
    texto_recebido = bits_para_texto(bits_recebidos)

    print("Bits originais:")
    print(bits)

    print("\nSinal modulado:")
    print(sinal)

    print("\nBits recebidos:")
    print(bits_recebidos)

    print("\nTexto recebido:")
    print(texto_recebido)

    print("=" * 60)
    print()


def main():
    texto = "Enéias"

    print("Texto original:")
    print(texto)
    print()

    bits = texto_para_bits(texto)

    testar_modulacao(
        "NRZ-Polar",
        bits,
        codificar_nrz_polar,
        decodificar_nrz_polar
    )

    testar_modulacao(
        "Manchester",
        bits,
        codificar_manchester,
        decodificar_manchester
    )

    testar_modulacao(
        "Bipolar",
        bits,
        codificar_bipolar,
        decodificar_bipolar
    )


if __name__ == "__main__":
    main()