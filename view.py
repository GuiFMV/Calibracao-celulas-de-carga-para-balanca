import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import numpy as np
# import threading
import time
import json


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BAUDRATE = 115200


# ============================================================
# APLICAÇÃO
# ============================================================

class CalibracaoHX711:

    def __init__(self, root):

        self.root = root
        self.root.title("Calibração - Balança HX711")
        self.root.geometry("900x700")

        # ----------------------------------------------------
        # SERIAL
        # ----------------------------------------------------

        self.serial = None

        # ----------------------------------------------------
        # DADOS DA CALIBRAÇÃO
        # ----------------------------------------------------

        self.tara = 0

        self.pontos = []

        self.A = 0.0
        self.B = 0.0
        self.C = 0.0

        # ----------------------------------------------------
        # VARIÁVEIS
        # ----------------------------------------------------

        self.porta_var = tk.StringVar()
        self.leituras_var = tk.StringVar(value="10")
        self.peso_var = tk.StringVar()
        self.tara_var = tk.StringVar(value="0")

        # ====================================================
        # INTERFACE
        # ====================================================

        self.criar_interface()

        self.atualizar_portas()


    # ========================================================
    # INTERFACE
    # ========================================================

    def criar_interface(self):

        # ----------------------------------------------------
        # SERIAL
        # ----------------------------------------------------

        frame_serial = ttk.LabelFrame(
            self.root,
            text="Comunicação serial"
        )

        frame_serial.pack(
            fill="x",
            padx=10,
            pady=10
        )

        ttk.Label(
            frame_serial,
            text="Porta:"
        ).grid(row=0, column=0, padx=5, pady=5)

        self.combo_porta = ttk.Combobox(
            frame_serial,
            textvariable=self.porta_var,
            width=15
        )

        self.combo_porta.grid(
            row=0,
            column=1,
            padx=5
        )

        ttk.Button(
            frame_serial,
            text="Atualizar",
            command=self.atualizar_portas
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            frame_serial,
            text="Conectar",
            command=self.conectar
        ).grid(row=0, column=3, padx=5)


        # ----------------------------------------------------
        # CONFIGURAÇÃO
        # ----------------------------------------------------

        frame_config = ttk.LabelFrame(
            self.root,
            text="Configuração"
        )

        frame_config.pack(
            fill="x",
            padx=10,
            pady=5
        )

        ttk.Label(
            frame_config,
            text="Número de leituras:"
        ).grid(row=0, column=0, padx=5, pady=10)

        ttk.Entry(
            frame_config,
            textvariable=self.leituras_var,
            width=10
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            frame_config,
            text="Aplicar",
            command=self.aplicar_numero_leituras
        ).grid(row=0, column=2, padx=5)


        # ----------------------------------------------------
        # TARA
        # ----------------------------------------------------

        frame_tara = ttk.LabelFrame(
            self.root,
            text="Tara"
        )

        frame_tara.pack(
            fill="x",
            padx=10,
            pady=5
        )

        ttk.Button(
            frame_tara,
            text="FAZER TARA",
            command=self.fazer_tara
        ).grid(row=0, column=0, padx=10, pady=10)

        ttk.Label(
            frame_tara,
            text="Tara:"
        ).grid(row=0, column=1)

        ttk.Label(
            frame_tara,
            textvariable=self.tara_var
        ).grid(row=0, column=2, padx=10)


        # ----------------------------------------------------
        # PONTO
        # ----------------------------------------------------

        frame_ponto = ttk.LabelFrame(
            self.root,
            text="Novo ponto de calibração"
        )

        frame_ponto.pack(
            fill="x",
            padx=10,
            pady=5
        )

        ttk.Label(
            frame_ponto,
            text="Peso conhecido (g):"
        ).grid(row=0, column=0, padx=5, pady=10)

        ttk.Entry(
            frame_ponto,
            textvariable=self.peso_var,
            width=15
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            frame_ponto,
            text="ADICIONAR PONTO",
            command=self.adicionar_ponto
        ).grid(row=0, column=2, padx=10)


        # ----------------------------------------------------
        # TABELA
        # ----------------------------------------------------

        frame_tabela = ttk.LabelFrame(
            self.root,
            text="Pontos de calibração"
        )

        frame_tabela.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        colunas = (
            "numero",
            "peso",
            "bruto",
            "corrigido"
        )

        self.tabela = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="headings"
        )

        self.tabela.heading(
            "numero",
            text="Nº"
        )

        self.tabela.heading(
            "peso",
            text="Peso (g)"
        )

        self.tabela.heading(
            "bruto",
            text="Bruto"
        )

        self.tabela.heading(
            "corrigido",
            text="Corrigido"
        )

        self.tabela.column(
            "numero",
            width=50
        )

        self.tabela.column(
            "peso",
            width=150
        )

        self.tabela.column(
            "bruto",
            width=200
        )

        self.tabela.column(
            "corrigido",
            width=200
        )

        self.tabela.pack(
            fill="both",
            expand=True
        )


        # ----------------------------------------------------
        # CALIBRAÇÃO
        # ----------------------------------------------------

        frame_calibracao = ttk.LabelFrame(
            self.root,
            text="Curva de calibração"
        )

        frame_calibracao.pack(
            fill="x",
            padx=10,
            pady=5
        )

        ttk.Button(
            frame_calibracao,
            text="FINALIZAR CALIBRAÇÃO",
            command=self.finalizar_calibracao
        ).grid(row=0, column=0, padx=10, pady=10)

        ttk.Button(
            frame_calibracao,
            text="ENVIAR CURVA PARA ESP32",
            command=self.enviar_curva
        ).grid(row=0, column=1, padx=10)


        # ----------------------------------------------------
        # RESULTADOS
        # ----------------------------------------------------

        self.resultado = tk.Text(
            frame_calibracao,
            height=7,
            width=90
        )

        self.resultado.grid(
            row=1,
            column=0,
            columnspan=3,
            padx=10,
            pady=10
        )


        # ----------------------------------------------------
        # SALVAR
        # ----------------------------------------------------

        ttk.Button(
            self.root,
            text="SALVAR CALIBRAÇÃO",
            command=self.salvar_calibracao
        ).pack(
            pady=5
        )


    # ========================================================
    # PORTAS
    # ========================================================

    def atualizar_portas(self):

        portas = [
            porta.device
            for porta in serial.tools.list_ports.comports()
        ]

        self.combo_porta["values"] = portas

        if portas:
            self.porta_var.set(portas[0])


    # ========================================================
    # CONECTAR
    # ========================================================

    def conectar(self):

        if self.serial and self.serial.is_open:
            self.serial.close()

        try:

            self.serial = serial.Serial(
                self.porta_var.get(),
                BAUDRATE,
                timeout=2
            )

            time.sleep(2)

            messagebox.showinfo(
                "Serial",
                "ESP32 conectado com sucesso."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível conectar:\n{erro}"
            )


    # ========================================================
    # ENVIA COMANDO
    # ========================================================

    def enviar_comando(self, comando):

        if not self.serial or not self.serial.is_open:

            messagebox.showerror(
                "Erro",
                "ESP32 não está conectado."
            )

            return []

        self.serial.reset_input_buffer()

        self.serial.write(
            (comando + "\n").encode()
        )

        respostas = []

        inicio = time.time()

        while time.time() - inicio < 10:

            if self.serial.in_waiting:

                linha = (
                    self.serial.readline()
                    .decode(
                        errors="ignore"
                    )
                    .strip()
                )

                if linha:
                    respostas.append(linha)

                    # Comandos terminados por essas respostas
                    if (
                        linha.startswith("RAW=")
                        or
                        linha.startswith("TARE_OK=")
                        or
                        linha == "COEF_OK"
                        or
                        linha.startswith("SETN_OK=")
                        or
                        linha.startswith("ERROR=")
                    ):
                        break

            time.sleep(0.01)

        return respostas


    # ========================================================
    # NÚMERO DE LEITURAS
    # ========================================================

    def aplicar_numero_leituras(self):

        try:

            numero = int(
                self.leituras_var.get()
            )

            if numero < 1:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Erro",
                "Número de leituras inválido."
            )

            return

        respostas = self.enviar_comando(
            f"SETN,{numero}"
        )

        if respostas:

            messagebox.showinfo(
                "Leituras",
                "\n".join(respostas)
            )


    # ========================================================
    # TARA
    # ========================================================

    def fazer_tara(self):

        resposta = self.enviar_comando(
            "TARE"
        )

        for linha in resposta:

            if linha.startswith("TARE_OK="):

                self.tara = int(
                    linha.split("=")[1]
                )

                self.tara_var.set(
                    str(self.tara)
                )

                messagebox.showinfo(
                    "Tara",
                    f"Tara definida:\n{self.tara}"
                )

                return

        messagebox.showerror(
            "Erro",
            "Não foi possível obter a tara."
        )


    # ========================================================
    # ADICIONAR PONTO
    # ========================================================

    def adicionar_ponto(self):

        try:

            peso = float(
                self.peso_var.get()
                .replace(",", ".")
            )

        except ValueError:

            messagebox.showerror(
                "Erro",
                "Digite um peso válido."
            )

            return

        resposta = self.enviar_comando(
            "READ"
        )

        bruto = None

        for linha in resposta:

            if linha.startswith("RAW="):

                bruto = int(
                    linha.split("=")[1]
                )

        if bruto is None:

            messagebox.showerror(
                "Erro",
                "Não foi possível obter a leitura do HX711."
            )

            return

        corrigido = bruto - self.tara

        self.pontos.append({
            "peso": peso,
            "bruto": bruto,
            "corrigido": corrigido
        })

        numero = len(self.pontos)

        self.tabela.insert(
            "",
            "end",
            values=(
                numero,
                f"{peso:.3f}",
                bruto,
                corrigido
            )
        )

        self.peso_var.set("")


    # ========================================================
    # CALCULAR CURVA
    # ========================================================

    def finalizar_calibracao(self):

        if len(self.pontos) < 3:

            messagebox.showerror(
                "Erro",
                "São necessários pelo menos 3 pontos."
            )

            return

        x = np.array(
            [
                ponto["corrigido"]
                for ponto in self.pontos
            ],
            dtype=float
        )

        y = np.array(
            [
                ponto["peso"]
                for ponto in self.pontos
            ],
            dtype=float
        )

        # ----------------------------------------------------
        # REGRESSÃO QUADRÁTICA
        # ----------------------------------------------------

        try:

            coeficientes = np.polyfit(
                x,
                y,
                2
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Erro ao calcular curva:\n{erro}"
            )

            return

        self.A = float(
            coeficientes[0]
        )

        self.B = float(
            coeficientes[1]
        )

        self.C = float(
            coeficientes[2]
        )

        # ----------------------------------------------------
        # R²
        # ----------------------------------------------------

        y_calculado = (
            self.A * x * x
            + self.B * x
            + self.C
        )

        ss_res = np.sum(
            (y - y_calculado) ** 2
        )

        ss_tot = np.sum(
            (y - np.mean(y)) ** 2
        )

        if ss_tot > 0:

            r2 = 1 - (
                ss_res / ss_tot
            )

        else:

            r2 = 1.0

        # ----------------------------------------------------
        # MOSTRA RESULTADO
        # ----------------------------------------------------

        self.resultado.delete(
            "1.0",
            tk.END
        )

        self.resultado.insert(
            tk.END,
            "CURVA DE CALIBRAÇÃO\n\n"
        )

        self.resultado.insert(
            tk.END,
            "Peso(g) = A*x² + B*x + C\n\n"
        )

        self.resultado.insert(
            tk.END,
            f"A = {self.A:.15e}\n"
        )

        self.resultado.insert(
            tk.END,
            f"B = {self.B:.15e}\n"
        )

        self.resultado.insert(
            tk.END,
            f"C = {self.C:.15e}\n\n"
        )

        self.resultado.insert(
            tk.END,
            f"R² = {r2:.10f}\n\n"
        )

        self.resultado.insert(
            tk.END,
            "x = leitura bruta - tara\n"
        )

        self.resultado.insert(
            tk.END,
            f"tara = {self.tara}\n"
        )

        messagebox.showinfo(
            "Calibração",
            "Curva calculada com sucesso."
        )


    # ========================================================
    # ENVIA CURVA
    # ========================================================

    def enviar_curva(self):

        if len(self.pontos) < 3:

            messagebox.showerror(
                "Erro",
                "Calcule a curva primeiro."
            )

            return

        comando = (
            f"COEF,"
            f"{self.A:.15e},"
            f"{self.B:.15e},"
            f"{self.C:.15e}"
        )

        resposta = self.enviar_comando(
            comando
        )

        if "COEF_OK" in resposta:

            messagebox.showinfo(
                "Curva",
                "Coeficientes enviados para o ESP32."
            )

        else:

            messagebox.showwarning(
                "Curva",
                "\n".join(resposta)
            )


    # ========================================================
    # SALVAR
    # ========================================================

    def salvar_calibracao(self):

        if len(self.pontos) < 3:

            messagebox.showerror(
                "Erro",
                "Não há uma calibração válida."
            )

            return

        arquivo = filedialog.asksaveasfilename(
            title="Salvar calibração",
            defaultextension=".json",
            filetypes=[
                (
                    "Arquivo JSON",
                    "*.json"
                )
            ]
        )

        if not arquivo:
            return

        dados = {
            "tara": self.tara,

            "numero_leituras":
                int(self.leituras_var.get()),

            "coeficientes": {
                "A": self.A,
                "B": self.B,
                "C": self.C
            },

            "pontos": self.pontos
        }

        with open(
            arquivo,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                dados,
                f,
                indent=4,
                ensure_ascii=False
            )

        messagebox.showinfo(
            "Salvar",
            "Calibração salva com sucesso."
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = CalibracaoHX711(root)

    root.mainloop()