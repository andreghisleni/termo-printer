import time
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import ConfigManager
from printer import PrinterEngine
from layout import LabelBuilder

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class EtiquetaData(BaseModel): id: str; codigo: str; nome: str; status: str; ref: str; qr_data: str
class RequestImpressao(BaseModel): etiquetas: List[EtiquetaData]

@app.post("/imprimir")
def api_imprimir(request: RequestImpressao):
    porta = ConfigManager.carregar().get("porta")
    if not porta: raise HTTPException(status_code=400, detail="Impressora não configurada.")
    
    layout = {
        "textos": [
            {"tipo": "simples", "campo": "id", "x_mm": 0.5, "y_mm": 0.0, "fonte": "3", "bold": 0},
            {"tipo": "simples", "campo": "codigo", "x_mm": 1.0, "y_mm": -9.0, "fonte": "1", "bold": 0},
            {"tipo": "bloco_inteligente", "campo": "nome", "x_mm": 4.0, "y_mm": 0.0, "passo_x_mm": 3.5, "fonte_normal": "2", "max_chars_normal": 11, "fonte_pequena": "1", "max_chars_pequena": 28, "bold": 0},
            {"tipo": "simples", "campo": "status", "x_mm": 12, "y_mm": 0.0, "fonte": "3", "bold": 1},
            {"tipo": "simples", "campo": "ref", "x_mm": 15.0, "y_mm": 0.0, "fonte": "1", "bold": 0},
        ],
        "qrcode": {"campo": "qr_data", "x_mm": 18.0, "y_mm": 5.5, "tamanho": 4, "rotacao": 0}
    }
    
    dados = [e.dict() for e in request.etiquetas]
    try:
        for i in range(0, len(dados), 3):
            bytes_tspl = LabelBuilder.gerar_etiqueta_padrao(dados[i:i+3], layout)
            PrinterEngine.enviar(porta, bytes_tspl)
            time.sleep(0.5) 
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))