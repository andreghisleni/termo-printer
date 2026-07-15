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
                    fn_notificar("Atualização ignorada. Você está em Modo Desenvolvedor.", "Aviso")
                return 
                
            url_api = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"
            resposta = requests.get(url_api, timeout=5)
            
            if resposta.status_code != 200: 
                return 
                
            dados = resposta.json()
            versao_remota = dados.get("tag_name")

            if versao_remota and versao_remota != VERSAO_ATUAL:
                # Agora procura pelo arquivo do "Instalador", e não mais pelo executável puro
                url_download = next((a["browser_download_url"] for a in dados.get("assets", []) if "Instalador" in a["name"]), None)
                if not url_download: return
                
                if fn_notificar:
                    fn_notificar(f"Baixando nova versão {versao_remota}...", "Atualizando")

                pasta_base = os.path.dirname(sys.executable)
                caminho_instalador = os.path.join(pasta_base, "Atualizacao_Temp.exe")
                
                resposta_download = requests.get(url_download, stream=True)
                resposta_download.raise_for_status()
                
                with open(caminho_instalador, 'wb') as arquivo:
                    for chunk in resposta_download.iter_content(chunk_size=8192):
                        arquivo.write(chunk)
                        
                if os.path.getsize(caminho_instalador) < 2 * 1024 * 1024:
                    if fn_notificar: fn_notificar("Erro no download.", "Falha")
                    return

                if fn_notificar:
                    fn_notificar("Instalando atualização... O aplicativo irá reiniciar.", "Quase lá!")

                # Manda o Windows rodar o instalador TOTALMENTE silencioso e fechar este app
                comando = f'"{caminho_instalador}" /VERYSILENT /SUPPRESSMSGBOXES /FORCECLOSEAPPLICATIONS'
                subprocess.Popen(comando, shell=True)
                
                # Desliga o aplicativo antigo para não atrapalhar
                os._exit(0)
                
            else:
                if fn_notificar and not silencioso:
                    fn_notificar("Você já está na versão mais recente!", "Tudo Certo")

        except Exception as e:
            if fn_notificar and not silencioso:
                fn_notificar(f"Erro: {str(e)}", "Falha")