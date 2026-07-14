import os
import sys
import subprocess
import requests # O urllib foi removido!

from config import VERSAO_ATUAL, REPO_GITHUB

class AutoUpdater:
    @staticmethod
    def buscar_atualizacao(silencioso=False, fn_notificar=None):
        try:
            if fn_notificar and not silencioso:
                fn_notificar("Procurando por novas versões no servidor...", "Buscando Atualização")
                
            # Trava visual para o Modo de Desenvolvimento
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

            # Se achou versão nova e diferente da atual
            if versao_remota and versao_remota != VERSAO_ATUAL:
                url_download = next((a["browser_download_url"] for a in dados.get("assets", []) if a["name"] == "Agente_Impressao.exe"), None)
                if not url_download: return
                
                if fn_notificar:
                    fn_notificar(f"Baixando versão {versao_remota} em segundo plano...", "Atualização Encontrada!")

                nome_exe_atual = os.path.basename(sys.executable)
                nome_exe_novo = "update_temp.exe"
                
                # ==========================================
                # CORREÇÃO: Usando 'requests' para baixar e contornar erro de SSL
                # ==========================================
                resposta_download = requests.get(url_download, stream=True)
                resposta_download.raise_for_status() # Verifica se a URL é válida
                
                with open(nome_exe_novo, 'wb') as arquivo:
                    for chunk in resposta_download.iter_content(chunk_size=8192):
                        arquivo.write(chunk)
                # ==========================================

                script_bat = f"""@echo off\ntimeout /t 3 /nobreak > NUL\ndel "{nome_exe_atual}"\nren "{nome_exe_novo}" "{nome_exe_atual}"\nstart "" "{nome_exe_atual}"\ndel "%~f0"\n"""
                with open("atualizar.bat", "w") as bat_file:
                    bat_file.write(script_bat)

                if fn_notificar:
                    fn_notificar("O aplicativo será reiniciado para aplicar a nova versão.", "Atualização Concluída")

                subprocess.Popen("atualizar.bat", shell=True)
                os._exit(0)
                
            else:
                if fn_notificar and not silencioso:
                    fn_notificar("Você já está rodando a versão mais recente!", "Sistema Atualizado")

        except Exception as e:
            if fn_notificar and not silencioso:
                fn_notificar(f"Erro ao verificar: {str(e)}", "Falha na Atualização")