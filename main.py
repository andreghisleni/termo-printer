import os
import sys
import threading
import multiprocessing
import time
import tkinter as tk
from tkinter import messagebox, ttk

import uvicorn
import pystray
from PIL import Image, ImageDraw

from config import VERSAO_ATUAL, SISTEMA, ConfigManager
from updater import AutoUpdater
from printer import PrinterEngine
from api import app

def iniciar_servidor():
    if sys.stdout is None: sys.stdout = open(os.devnull, "w")
    if sys.stderr is None: sys.stderr = open(os.devnull, "w")
    try: 
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        with open("log_erro_api.txt", "w") as f: f.write(str(e))

class TrayApp:
    icone = None # Guarda a referência do ícone

    @classmethod
    def notificar(cls, mensagem, titulo="Agente de Impressão"):
        """ Dispara uma notificação nativa no sistema operacional """
        if cls.icone:
            try:
                cls.icone.notify(mensagem, titulo)
            except Exception:
                pass

    @staticmethod
    def testar_porta(porta):
        try:
            PrinterEngine.enviar(porta, b"SIZE 105 mm, 22 mm\nGAP 2 mm, 0\nDIRECTION 1\nCLS\nTEXT 50,50,\"3\",0,1,1,\"TESTE\"\nTEXT 330,50,\"3\",0,1,1,\"TESTE\"\nTEXT 610,50,\"3\",0,1,1,\"TESTE\"\nPRINT 1\n")
            messagebox.showinfo("Sucesso", "Teste enviado!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    @classmethod
    def abrir_config(cls):
        root = tk.Tk()
        root.title(f"Agente de Impressão - {VERSAO_ATUAL}")
        root.geometry("380x180")
        root.eval('tk::PlaceWindow . center')

        tk.Label(root, text="Selecione a Impressora:", font=("Arial", 10, "bold")).pack(pady=10)
        porta_var = tk.StringVar(value=ConfigManager.carregar().get("porta"))
        
        if SISTEMA == "Windows":
            ttk.Combobox(root, textvariable=porta_var, values=PrinterEngine.listar_impressoras_windows(), width=40).pack(pady=5)
        else:
            tk.Entry(root, textvariable=porta_var, width=40).pack(pady=5)

        frm = tk.Frame(root)
        frm.pack(pady=15)
        tk.Button(frm, text="Testar", command=lambda: cls.testar_porta(porta_var.get()), bg="blue", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(frm, text="Salvar", command=lambda: [ConfigManager.salvar(porta_var.get()), messagebox.showinfo("OK", "Salvo!")], bg="green", fg="white").pack(side=tk.LEFT, padx=10)
        root.mainloop()

    @classmethod
    def rodar(cls):
        img = Image.new('RGB', (64, 64), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle((16, 16, 48, 48), fill=(0, 0, 0))
        draw.rectangle((24, 8, 40, 16), fill=(100, 100, 100))
        
        menu = pystray.Menu(
            pystray.MenuItem("Configurações", lambda: threading.Thread(target=cls.abrir_config, daemon=True).start()),
            # Passamos a função notificar para o atualizador
            pystray.MenuItem("Buscar Atualizações", lambda: threading.Thread(target=AutoUpdater.buscar_atualizacao, kwargs={"silencioso": False, "fn_notificar": cls.notificar}, daemon=True).start()),
            pystray.MenuItem("Sair", lambda icon, item: [icon.stop(), os._exit(0)])
        )
        cls.icone = pystray.Icon("Impressora", img, f"Impressão ({VERSAO_ATUAL})", menu)
        cls.icone.run()

def rotina_de_inicio():
    # Aguarda o ícone da bandeja ser criado antes de tentar notificar
    time.sleep(2)
    AutoUpdater.buscar_atualizacao(silencioso=True, fn_notificar=TrayApp.notificar)

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    
    # Inicia as threads
    threading.Thread(target=iniciar_servidor, daemon=True).start()
    threading.Thread(target=rotina_de_inicio, daemon=True).start()
    
    # Bloqueia o processo rodando o ícone
    TrayApp.rodar()