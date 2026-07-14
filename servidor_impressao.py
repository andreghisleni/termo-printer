import os
import time
import json
import platform
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Para a lista suspensa (Combobox)
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pystray
from PIL import Image, ImageDraw

# ADICIONE ESTES DOIS:
import sys
import multiprocessing

# Importação condicional para o Windows
SISTEMA = platform.system()
if SISTEMA == "Windows":
    import win32print

# ==========================================
# 1. GERENCIADOR DE CONFIGURAÇÕES
# ==========================================
ARQUIVO_CONFIG = "config_impressora.json"

def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"porta": "" if SISTEMA == "Windows" else "/dev/usb/lp0"}

def salvar_config(porta):
    with open(ARQUIVO_CONFIG, "w") as f:
        json.dump({"porta": porta}, f)

# ==========================================
# 2. MOTOR DE IMPRESSÃO UNIVERSAL
# ==========================================
def enviar_para_impressora(porta_ou_nome, comandos_tspl):
    """ Envia os comandos TSPL dependendo do Sistema Operacional """
    if SISTEMA == "Windows":
        hPrinter = win32print.OpenPrinter(porta_ou_nome)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Etiquetas TSPL", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, comandos_tspl)
            win32print.EndPagePrinter(hPrinter)
        finally:
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)
    else:
        # Lógica original do Linux
        with open(porta_ou_nome, 'wb') as impressora:
            impressora.write(comandos_tspl)

# ==========================================
# 3. FASTAPI E GERAÇÃO DO LAYOUT
# ==========================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

class EtiquetaData(BaseModel):
    id: str
    codigo: str
    nome: str
    status: str
    ref: str
    qr_data: str

class RequestImpressao(BaseModel):
    etiquetas: List[EtiquetaData]

def mm(valor_em_mm): return int(valor_em_mm * 8)

def gerar_comandos_linha(dados_etiquetas, layout):
    posicoes_x_mm = [1.5, 37.0, 71.8]
    margem_superior = 0.5    

    comandos = [
        b"SIZE 105 mm, 22 mm\n", b"GAP 2 mm, 0\n", b"DIRECTION 1\n", b"CODEPAGE 1252\n", b"CLS\n"
    ]

    for i, x_mm in enumerate(posicoes_x_mm):
        if i >= len(dados_etiquetas): break
        dados = dados_etiquetas[i]
        x_base = mm(x_mm)
        y_base = mm(margem_superior)
        y_inicio_texto = y_base + mm(20) 
        
        for texto in layout.get("textos", []):
            campo = texto["campo"]
            valor = str(dados.get(campo, ""))
            tipo_campo = texto.get("tipo", "simples")
            rot = texto.get("rotacao", 270)
            nivel_bold = texto.get("bold", 0)
            
            if tipo_campo == "bloco_inteligente":
                limite_1 = texto["max_chars_normal"]
                limite_2 = texto["max_chars_pequena"]
                linha1_texto = valor[:limite_1] 
                linha2_texto = valor[limite_1 : limite_1 + limite_2] 
                
                linhas = []
                if linha1_texto: linhas.append({"texto": linha1_texto, "fonte": texto["fonte_normal"]})
                if linha2_texto: linhas.append({"texto": linha2_texto, "fonte": texto["fonte_pequena"]})
                
                for idx, linha in enumerate(linhas):
                    x_atual = x_base + mm(texto["x_mm"] + (texto["passo_x_mm"] * idx))
                    y_atual = y_inicio_texto + mm(texto["y_mm"])
                    if nivel_bold > 0: comandos.append(f"SET BOLD {nivel_bold}\n".encode('windows-1252', errors='ignore'))
                    comandos.append(f"TEXT {x_atual},{y_atual},\"{linha['fonte']}\",{rot},1,1,\"{linha['texto']}\"\n".encode('windows-1252', errors='ignore'))
                    if nivel_bold > 0: comandos.append(b"SET BOLD 0\n")
            else:
                x_atual = x_base + mm(texto["x_mm"])
                y_atual = y_inicio_texto + mm(texto["y_mm"])
                if nivel_bold > 0: comandos.append(f"SET BOLD {nivel_bold}\n".encode('windows-1252', errors='ignore'))
                comandos.append(f"TEXT {x_atual},{y_atual},\"{texto['fonte']}\",{rot},1,1,\"{valor}\"\n".encode('windows-1252', errors='ignore'))
                if nivel_bold > 0: comandos.append(b"SET BOLD 0\n")
            
        if "qrcode" in layout:
            qr = layout["qrcode"]
            x_qr = x_base + mm(qr["x_mm"])
            y_qr = y_base + mm(qr["y_mm"])
            comandos.append(f"QRCODE {x_qr},{y_qr},M,{qr['tamanho']},A,{qr['rotacao']},\"{dados.get(qr['campo'], '')}\"\n".encode('windows-1252', errors='ignore'))

    comandos.append(b"PRINT 1\n")
    return b"".join(comandos)

@app.post("/imprimir")
def imprimir_etiquetas(request: RequestImpressao):
    config = carregar_config()
    caminho_porta = config.get("porta")
    
    if not caminho_porta:
        raise HTTPException(status_code=400, detail="Impressora não configurada no aplicativo local.")
    
    layout_etiqueta = {
        "textos": [
            {"tipo": "simples", "campo": "id","x_mm": 0.5,  "y_mm": 0.0,  "fonte": "3", "bold": 0},
            {"tipo": "simples", "campo": "codigo", "x_mm": 1.0,  "y_mm": -9.0, "fonte": "1", "bold": 0},
            {"tipo": "bloco_inteligente", "campo": "nome", "x_mm": 4.0, "y_mm": 0.0, "passo_x_mm": 3.5, "fonte_normal": "2", "max_chars_normal": 11, "fonte_pequena": "1", "max_chars_pequena": 28, "bold": 0},
            {"tipo": "simples", "campo": "status", "x_mm": 12,  "y_mm": 0.0,  "fonte": "3", "bold": 1},
            {"tipo": "simples", "campo": "ref",    "x_mm": 15.0, "y_mm": 0.0,  "fonte": "1", "bold": 0},
        ],
        "qrcode": {"campo": "qr_data", "x_mm": 18.0, "y_mm": 5.5, "tamanho": 4, "rotacao": 0}
    }
    
    linha_dados = [etiqueta.dict() for etiqueta in request.etiquetas]

    try:
        for i in range(0, len(linha_dados), 3):
            lote_atual = linha_dados[i : i+3]
            bytes_tspl = gerar_comandos_linha(lote_atual, layout_etiqueta)
            enviar_para_impressora(caminho_porta, bytes_tspl) # Usa a função universal
            time.sleep(0.5) 
        return {"status": "sucesso", "mensagem": f"Impressão finalizada!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 4. INTERFACE GRÁFICA (TELA DE TESTE E CONFIG)
# ==========================================
def testar_comunicacao(porta):
    try:
        comando_teste = b"SIZE 105 mm, 22 mm\nGAP 2 mm, 0\nDIRECTION 1\nCLS\nTEXT 50,50,\"3\",0,1,1,\"TESTE OK\"\nPRINT 1\n"
        enviar_para_impressora(porta, comando_teste) # Usa a função universal
        messagebox.showinfo("Sucesso", "Teste enviado com sucesso para o Spooler/Porta!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro na comunicação:\n{e}")

def obter_impressoras_windows():
    if SISTEMA == "Windows":
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        return [printer[2] for printer in printers]
    return []

def abrir_tela_config():
    root = tk.Tk()
    root.title("Configurar Impressora")
    root.geometry("380x180")
    root.eval('tk::PlaceWindow . center')

    tk.Label(root, text="Selecione/Digite a Impressora:", font=("Arial", 10, "bold")).pack(pady=10)
    
    config = carregar_config()
    porta_var = tk.StringVar(value=config.get("porta"))
    
    # Se for Windows, mostra um Dropdown com as impressoras. Se for Linux, mostra input de texto.
    if SISTEMA == "Windows":
        lista_impressoras = obter_impressoras_windows()
        combo_porta = ttk.Combobox(root, textvariable=porta_var, values=lista_impressoras, width=40)
        combo_porta.pack(pady=5)
    else:
        entrada_porta = tk.Entry(root, textvariable=porta_var, width=40)
        entrada_porta.pack(pady=5)

    def acao_salvar():
        salvar_config(porta_var.get())
        messagebox.showinfo("Salvo", "Configuração atualizada com sucesso!")

    def acao_testar():
        testar_comunicacao(porta_var.get())

    frame_botoes = tk.Frame(root)
    frame_botoes.pack(pady=15)

    tk.Button(frame_botoes, text="Testar Impressão", command=acao_testar, bg="blue", fg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(frame_botoes, text="Salvar Configuração", command=acao_salvar, bg="green", fg="white").pack(side=tk.LEFT, padx=10)

    root.mainloop()

# ==========================================
# 5. BANDEJA DO SISTEMA E INICIALIZAÇÃO
# ==========================================
def desenhar_icone():
    img = Image.new('RGB', (64, 64), color = (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((16, 16, 48, 48), fill=(0, 0, 0))
    draw.rectangle((24, 8, 40, 16), fill=(100, 100, 100))
    return img

def on_configurar(icon, item):
    threading.Thread(target=abrir_tela_config, daemon=True).start()

def on_sair(icon, item):
    icon.stop()
    os._exit(0)

def rodar_servidor_api():
    # 1. Corrige o bug do PyInstaller --noconsole
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
        
    try:
        # 2. Inicia o servidor
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        # 3. Se a API quebrar, ela salva o erro em um bloco de notas!
        with open("log_erro_api.txt", "w") as f:
            f.write(f"Erro ao iniciar API: {str(e)}")

if __name__ == "__main__":
    # COMANDO OBRIGATÓRIO PARA O UVICORN FUNCIONAR NO .EXE DO WINDOWS
    multiprocessing.freeze_support() 
    
    threading.Thread(target=rodar_servidor_api, daemon=True).start()
    
    menu = pystray.Menu(
        pystray.MenuItem("Configurações e Teste", on_configurar),
        pystray.MenuItem("Sair (Desligar API)", on_sair)
    )
    icone_tray = pystray.Icon("Impressora", desenhar_icone(), "Servidor de Impressão", menu)
    icone_tray.run()