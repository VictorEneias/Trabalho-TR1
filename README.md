# Simulador TR1 — Camada Física e Camada de Enlace

Trabalho final de Teleinformática e Redes 1 (UnB). Simula o caminho de uma
mensagem pelas duas camadas mais baixas da rede: enquadramento e detecção/
correção de erros (enlace) e modulação sobre um meio com ruído (física).

## Arquivos

| Arquivo | Papel |
|--------|-------|
| `CamadaFisica.py` | NRZ-Polar, Manchester, Bipolar, ASK, FSK, QPSK, 16-QAM |
| `CamadaEnlace.py` | contagem, byte/bit stuffing, paridade, checksum, CRC-32, Hamming |
| `InterfaceGUI.py` | interface gráfica (Tkinter) com gráfico do sinal |
| `Simulador.py` | orquestra TX e RX (texto → sinal → texto) |
| `Transmissor.py` / `Receptor.py` | TX e RX por socket (várias conexões) |
| `canal.py` | ruído gaussiano + transporte por socket (o "meio") |
| `Utils.py` | conversões texto ↔ bytes ↔ bits |

## Como rodar

```bash
python3 InterfaceGUI.py        # interface gráfica (Linux: sudo apt install python3-tk)
python3 Simulador.py           # demonstração no terminal

# Em rede, dois terminais:
python3 Receptor.py
python3 Transmissor.py "mensagem" 0.3
```
