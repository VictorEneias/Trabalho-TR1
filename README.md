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
| `Transmissor.py` / `Receptor.py` | TX e RX por socket (aceita várias conexões) |
| `canal.py` | ruído gaussiano + transporte por socket (o "meio") |
| `Utils.py` | conversões texto ↔ bytes ↔ bits |
| `log.py` | registra o passo a passo no terminal e em `logs/` |

## Como rodar

```bash
python3 InterfaceGUI.py        # interface gráfica (Linux: sudo apt install python3-tk)
python3 Simulador.py           # demonstração no terminal (config padrão)
```

O `Simulador.py` também aceita os parâmetros pela linha de comando:

```bash
python3 Simulador.py "sua mensagem" --mod qpsk --enq flag_bits --edc hamming --sigma 0.3 --tam 255
python3 Simulador.py --help    # lista todas as opções
```

- `--mod`: nrz, manchester, bipolar, ask, fsk, qpsk, 16qam
- `--enq`: contagem, flag_bytes, flag_bits
- `--edc`: nenhum, paridade, checksum, crc, hamming
- `--tam`: tamanho máximo de quadro (bytes) · `--sigma`: intensidade do ruído

Em rede, com dois terminais (dá para abrir vários transmissores ao mesmo tempo):

```bash
python3 Receptor.py                       # fica ouvindo
python3 Transmissor.py "mensagem" 0.3     # envia (0.3 = sigma do ruído)
```

## Logs

Cada execução (simulação local ou conexão de socket) grava um arquivo `.txt` em
`logs/` e também imprime no terminal, descrevendo a mensagem passo a passo
(conversões, EDC, enquadramento, modulação, ruído e resultado). Útil para
acompanhar e depurar.
