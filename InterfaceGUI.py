"""
Interface gráfica do simulador (Tkinter).

A tela deixa o usuário configurar tudo o que o diagrama do enunciado pede
(tamanho de quadro, EDC, tipo de enquadramento, modulação e ruído), roda a
simulação completa na mesma máquina e mostra dois resultados:

  - o sinal elétrico gerado, desenhado num gráfico (Canvas puro, sem matplotlib);
  - o texto recuperado no receptor e o status da verificação de erros.

Também dá para enviar a mensagem de verdade por socket para um Receptor.py que
esteja rodando, útil para a demonstração com várias conexões.

Tudo o que é "lógica" fica no Simulador; aqui é só montar a janela e desenhar.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import Simulador
import Transmissor

# Nomes amigáveis na tela -> chaves internas usadas pelo Simulador.
MODULACOES = {
    "NRZ-Polar": "nrz", "Manchester": "manchester", "Bipolar": "bipolar",
    "ASK": "ask", "FSK": "fsk", "QPSK": "qpsk", "16-QAM": "16qam",
}
ENQUADRAMENTOS = {
    "Contagem de caracteres": "contagem",
    "Flag + byte stuffing": "flag_bytes",
    "Flag + bit stuffing": "flag_bits",
}
EDCS = {
    "Nenhum": "nenhum", "Paridade par": "paridade", "Checksum": "checksum",
    "CRC-32": "crc", "Hamming (correção)": "hamming",
}


def desenhar_sinal(canvas, sinal, max_amostras=800):
    """Desenha o sinal como uma linha no Canvas, reescalando para caber."""
    canvas.delete("all")
    largura = int(canvas["width"])
    altura = int(canvas["height"])
    meio = altura / 2

    trecho = sinal[:max_amostras]
    if not trecho:
        return

    pico = max(1e-9, max(abs(v) for v in trecho))   # evita divisão por zero
    margem = altura * 0.4

    # Linha de 0V no meio, só de referência visual.
    canvas.create_line(0, meio, largura, meio, fill="#cccccc")

    pontos = []
    for i, v in enumerate(trecho):
        x = largura * i / max(1, len(trecho) - 1)
        y = meio - (v / pico) * margem
        pontos += [x, y]
    canvas.create_line(*pontos, fill="#1565c0", width=2)


class Aplicacao:
    def __init__(self, raiz):
        raiz.title("Simulador TR1 - Camadas Física e de Enlace")
        self.raiz = raiz

        painel = ttk.Frame(raiz, padding=10)
        painel.grid(row=0, column=0, sticky="n")

        # --- Campos de configuração ---
        ttk.Label(painel, text="Mensagem:").grid(row=0, column=0, sticky="w")
        self.texto = tk.Entry(painel, width=32)
        self.texto.insert(0, "Teleinformatica e Redes 1")
        self.texto.grid(row=1, column=0, columnspan=2, pady=(0, 8))

        self.modulacao = self._combo(painel, "Modulação:", MODULACOES, 2)
        self.enquadramento = self._combo(painel, "Enquadramento:", ENQUADRAMENTOS, 4)
        self.edc = self._combo(painel, "Detecção/Correção:", EDCS, 6)

        ttk.Label(painel, text="Tamanho máx. do quadro (bytes):").grid(row=8, column=0, sticky="w")
        self.tam_max = tk.Entry(painel, width=8)
        self.tam_max.insert(0, "255")
        self.tam_max.grid(row=9, column=0, sticky="w", pady=(0, 6))

        ttk.Label(painel, text="Ruído (sigma):").grid(row=10, column=0, sticky="w")
        self.sigma = tk.Entry(painel, width=8)
        self.sigma.insert(0, "0.0")
        self.sigma.grid(row=11, column=0, sticky="w", pady=(0, 8))

        ttk.Button(painel, text="Simular (local)", command=self.simular).grid(
            row=12, column=0, sticky="we", pady=2)
        ttk.Button(painel, text="Enviar p/ Receptor (socket)", command=self.enviar_socket).grid(
            row=13, column=0, sticky="we", pady=2)

        # --- Resultados ---
        self.status = ttk.Label(painel, text="", foreground="#00695c", wraplength=240)
        self.status.grid(row=14, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.recuperado = ttk.Label(painel, text="", wraplength=240)
        self.recuperado.grid(row=15, column=0, columnspan=2, sticky="w")

        # --- Gráfico do sinal ---
        area = ttk.Frame(raiz, padding=10)
        area.grid(row=0, column=1, sticky="n")
        ttk.Label(area, text="Sinal transmitido (primeiras amostras):").grid(row=0, column=0, sticky="w")
        self.canvas = tk.Canvas(area, width=620, height=300, background="white",
                                highlightthickness=1, highlightbackground="#999")
        self.canvas.grid(row=1, column=0)

    def _combo(self, painel, rotulo, opcoes, linha):
        ttk.Label(painel, text=rotulo).grid(row=linha, column=0, sticky="w")
        var = tk.StringVar(value=list(opcoes)[0])
        ttk.Combobox(painel, textvariable=var, values=list(opcoes),
                     state="readonly", width=24).grid(row=linha + 1, column=0,
                                                       sticky="w", pady=(0, 6))
        return var

    def _ler_config(self):
        return Simulador.Config(
            modulacao=MODULACOES[self.modulacao.get()],
            enquadramento=ENQUADRAMENTOS[self.enquadramento.get()],
            edc=EDCS[self.edc.get()],
            tam_max=int(self.tam_max.get()),
            sigma=float(self.sigma.get()),
        )

    def simular(self):
        try:
            cfg = self._ler_config()
            resultado = Simulador.simular_local(self.texto.get(), cfg)
        except Exception as erro:
            messagebox.showerror("Erro", str(erro))
            return
        desenhar_sinal(self.canvas, resultado["sinal_com_ruido"])
        self.status.config(text="Status do EDC: " + resultado["status"])
        self.recuperado.config(text="Texto recuperado: " + resultado["texto"])

    def enviar_socket(self):
        try:
            cfg = self._ler_config()
            Transmissor.enviar(self.texto.get(), cfg)
            messagebox.showinfo("Socket", "Mensagem enviada ao Receptor.")
        except Exception as erro:
            messagebox.showerror("Erro de socket",
                                 "Não foi possível enviar.\nO Receptor.py está rodando?\n\n" + str(erro))


def main():
    raiz = tk.Tk()
    Aplicacao(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
