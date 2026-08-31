import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import numpy as np
import time
import json

BAURDRATE = 115200

class CalibracaoHX711:
    def __init__(self, root):
        self.root = root
        self.root.title("Calibração - Balança HX711")
        self.root.geometry("900x700")
        
        self.serial = None
        
        self.tara = 0
        
        self.pontos = []
        
        self.A = 0.0
        self.B = 0.0
        self.C = 0.0
        
        self.porta_var = tk.StringVar()
        self.leituras_var = tk.StringVar(value="10")
        self.peso_var = tk.StringVar()
        self.tara_var = tk.StringVar(value="0")
        
        self.criar_interface()
        self.atualizar_portas()
        
    def criar_interface(self):
        # Serial
        frame_serial = ttk.LabelFrame(self.root, text="Comunicação serial")
        
        frame_serial.pack(fill="x", padx=10, pady=10)
        
        ttk.label(frame_serial, text="Porta:").grid(row=0, column=0, padx=20,pady=20)
        
        self.combo_porta = ttk.Combobox(frame_serial, textvariable=self.porta_var, width=15)
        
        self.combo_porta.grid(row=0, column=1,padx=5)
        
        ttk.Button(frame_serial, text="Atualizar", command=self.atualizar_portas).grid(row=0,column=2,padx=5)
        
        ttk.Button(frame_serial, text="Conectar", command=self.conectar).grid(row=0, column=3, padx=5)
        
        # Configuração
        frame_config = ttk.LabelFrame(self.root, text="Configuração")
        
        frame_config.pack(fill="x", padx=10, padu=5)
        
        ttk.label(frame_config, text="Número de leituras:").grid(row=0, column=0, padx=5,pady=10)
        
        ttk.Entry(frame_config, textvariable=self.leituras_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Button(frame_config, text="Aplicar", command=self.aplicar_numero_leituras).grid(row=0, column=2, padx=5)
        
        # Tara
        frame_tara = ttk.LabelFrame(self.root, text="Tara")
        
        frame_tara.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame_tara, text="Fazer Tara", command=self.fazer_tara).grid(row=0, column=0, padx=10, pady=10)
        
        ttk.Label(frame_tara, text="Tara:")
        
        ttk.Label(frame_tara, textvariable=self.tara_var).grid(row=0, column=0, padx=10)
        
        # Adicionar Ponto
        frame_ponto = ttk.LabelFrame(self.root, text="Novo ponto de calibração")
        
        frame_ponto.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_ponto, text="Peso conhecido (g):").grid(row=0, column=0, padx=5, pady=10)
        
        ttk.Entry(frame_ponto, textvariable=self.peso_var, width=15).grid(row=0, column=2, padx=10)
        
        # Tabela
        frame_tabela = ttk.LabelFrame(self.root, text="Pontos de calibração")
        
        frame_tabela.pack(fill="both", expand=True, padx=10, pady=5)
        
        colunas = ("numero", "peso", "bruto", "corrigido")
        
        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings")
        
        self.tabela.heading("numero", text="N°")
        
        self.tabela.heading("peso", text="Peso(g)")
        
        self.tabela.heading("corrigido", text="Corrigido")
        
        self.tabela.column("numero", width=50)
        
        self.tabela.column("peso", width=150)
        
        self.tabela.column("bruto", width=200)
        
        self.tabela.column("corrigido", width=200)
        
        self.tabela.pack(fill="both", expand=True)
        
        # Calibração
        frame_calibracao = ttk.LabelFrame(self.root, text="Curva de calibração")
        
        frame_calibracao.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame_calibracao, text="FINALIZAR CALIBRAÇÃO").grid(row=0,column=0, padx=10, pady=10)
        
        ttk.Button(frame_calibracao, text="ENVIAR CURVA PARA ESP32", command=self.enviar_curva).grid(row=0, column=1, padx=10)
        
        # Resultados
        self.resultado = tk.Text(frame_calibracao, height=7, width=90)
        
        self.resultado.grid(row=1, column=0, columnspan=3, padx=10, pady=10)
        
        # Salvar variáveis da equação
        ttk.Button(self.root, text="SALVAR CALIBRAÇÃO", command=self.salvar_calibracao).pack(pady=5)
        
    # Portas possíveis
    def atualizar_portas(self):
        portas = [porta.device for porta in serial.tools.list_ports.comports()]
        
        self.combo_porta["values"] = portas
        
        if portas:
            self.porta_var.set(portas[0])
    
    # Conectar na porta
    def conectar(self):
        if self.serial and serial.serial.is_open:
            self.serial.close()
            
        try:
            self.serial = serial.Serial(self.porta_var.get(), BAURDRATE, timeout=2)
        
            time.sleep(2)
            
            messagebox.showinfo("Serial", "ESP32 conectado com sucesso.")
            
        except Exception as erro:
            messagebox.showerror("Erro", f"Não foi possível conectar:\n{erro}")
        
    # Enviar comando
    def enviar_comando(self, comando):
        if not self.serial or not self.seiral.is_open:
            messagebox.showerror("Erro", "ESP32 não está conectado.")
            
            return[]

        self.serial.reset_input_buffer()
        self.serial.write((comando + "\n").encode())
        
        respostas = []
        
        inicio = time.time()
        
        while time.time() - inicio < 10:
            if serial.serial.in_waiting:
                linha = (self.serial.readline().decode(errors="ignore").strip())

                if linha:
                    respostas.append(linha)
                    
                    if(linha.startswith("RAW=") or linha.startswith("TARE_OK=")
                       or linha.startswith("SETN_OK=") or linha.startswith("ERROR=")
                       or linha == "COEF_OK"):
                        break
                    
            time.sleep(0.01)

        return respostas
    
    # Número de leituras
    def aplicar_numero_leituras(self):
        try:
            numero = int(self.leituras_var.get())
            
            if numero < 1:
                raise ValueError
            
        except ValueError:
            messagebox.showerror("Erro", "Número de leituras inválidos")
            
            return
        
        respostas = self.enviar_comando(f"SETN,{numero}")
        
        if respostas:
            messagebox.showinfo("Leituras", "\n".join(respostas))
            
    # Tara
    def fazer_tara(self):
        resposta = self.enviar_comando("TARE")
        
        for linha in resposta:
            if linha.startswith("TARE_OK="):
                self.tara = int(linha.split("=")[1])
                self.tara_var.set(str(self.tara))
                
                messagebox.showinfo("Tara", f"Tara definida:\n{self.tara}")
                
                return
            messagebox.showerror("Erro", "Não foi possível obter tara.")
    
    # Adicionar ponto
    def adicionar_ponto(self):
        try:
            peso = float(self.peso_var.get().replace(",","."))
            
        except ValueError:
            messagebox.showerror("Error","Digite um peso válido.")
            return
        
        resposta = self.enviar_comando("READ")
        
        bruto = None
        
        for linha in resposta:
            if linha.startswith("RAW="):
                bruto = int(linha.split("=")[1])
        
        if bruto is None:
            messagebox.showerror("Error", "Não foi possível obter a leitura do HX711.")
            return
        
        corrigido = bruto - self.tara
        
        self.pontos.append({"peso": peso, "bruto": bruto, "corrigido": corrigido})
        
        self.peso_var.set("")
        
    # Calcular curva
    def finalizar_calibracao(self):
        if len(self.pontos) < 3:
            messagebox.showerror("Erro", "São necessários pelo menos 3 pontos.")    
            return
        
        x = np.array([ponto["corrigido"] for ponto in self.pontos], dtype=float)
        y = np.array([ponto["peso"] for ponto in self.pontos], dtype=float)
        
        try:
            coeficientes = np.polyfit(x, y, 2)
        
        except Exception as erro:
            messagebox.showerror("Erro", f"Erro ao calcular curva:\n{erro}")
            
        self.A = float(coeficientes[0])
    
if __name__ == "__main__":
    root = tk.TK()        
    
    app = CalibracaoHX711
            
    root.mainloop()