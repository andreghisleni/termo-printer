import os
import sys
import subprocess
import requests

from config import VERSAO_ATUAL, REPO_GITHUB

class AutoUpdater:
    @staticmethod
    def buscar_atualizacao(silencioso=False, fn_notificar=None):
        try:
            if fn_notificar and not silencioso:
                fn_notificar("Procurando por novas versões no servidor...", "Buscando Atualização")
                
            if VERSAO_ATUAL == "DEV_VERSION":
                if fn_notificar and not silencioso:
                    fn_notificar("Atualização ignorada. Você está rodando via código-fonte.", "Modo Desenvolvedor")
                return 
                
            url_api = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"
            resposta = requests.get(url_api, timeout=5)
            
            if resposta.status_code != 200: 
                if fn_notificar and not silencioso:
                    fn_notificar("Servidor de atualizações indisponível no momento.", "Erro na Busca")
                return 
                
            dados = resposta.json()
            versao_remota = dados.get("tag_name")

            if versao_remota and versao_remota != VERSAO_ATUAL:
                url_download = next((a["browser_download_url"] for a in dados.get("assets", []) if a["name"] == "Agente_Impressao.exe"), None)
                if not url_download: return
                
                if fn_notificar:
                    fn_notificar(f"Baixando versão {versao_remota} em segundo plano...", "Atualização Encontrada!")

                caminho_exe_atual = sys.executable
                pasta_base = os.path.dirname(caminho_exe_atual)
                nome_exe = os.path.basename(caminho_exe_atual)
                
                caminho_novo_exe = os.path.join(pasta_base, "update_temp.exe")
                caminho_bat = os.path.join(pasta_base, "atualizar.bat")
                
                resposta_download = requests.get(url_download, stream=True)
                resposta_download.raise_for_status()
                
                with open(caminho_novo_exe, 'wb') as arquivo:
                    for chunk in resposta_download.iter_content(chunk_size=8192):
                        arquivo.write(chunk)
                        
                if os.path.getsize(caminho_novo_exe) < 5 * 1024 * 1024:
                    if fn_notificar:
                        fn_notificar("O arquivo baixado parece corrompido. Atualização abortada.", "Erro no Download")
                    return

                # ==========================================
                # O SCRIPT DE BAT BLINDADO (Com limpeza de cache)
                # ==========================================
                script_bat = f"""@echo off
cd /d "{pasta_base}"

:aguardar
timeout /t 1 /nobreak > NUL
del "{nome_exe}" > NUL 2>&1
if exist "{nome_exe}" goto aguardar

ren "update_temp.exe" "{nome_exe}"

:: MATA A HERANÇA DO PYINSTALLER DIRETAMENTE NO CMD DO WINDOWS
set _MEIPASS=
set _MEIPASS2=
set MEIPASS=
set MEIPASS2=

start "" "{nome_exe}"
del "%~f0"
"""
                with open(caminho_bat, "w", encoding="utf-8") as bat_file:
                    bat_file.write(script_bat)

                if fn_notificar:
                    fn_notificar("O aplicativo será reiniciado para aplicar a nova versão.", "Atualização Concluída")

                subprocess.Popen(f'"{caminho_bat}"', shell=True, cwd=pasta_base)
                os._exit(0)
                
            else:
                if fn_notificar and not silencioso:
                    fn_notificar("Você já está rodando a versão mais recente!", "Sistema Atualizado")

        except Exception as e:
            if fn_notificar and not silencioso:
                fn_notificar(f"Erro ao verificar: {str(e)}", "Falha na Atualização")