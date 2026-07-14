import os
import json
import platform

# O GitHub Actions vai injetar a versão real aqui no lugar de DEV_VERSION
VERSAO_ATUAL = "DEV_VERSION"

# MUDE AQUI PARA O SEU USUÁRIO E REPOSITÓRIO!
REPO_GITHUB = "andreghisleni/termo-printer"

ARQUIVO_CONFIG = "config_impressora.json"
SISTEMA = platform.system()

class ConfigManager:
    @staticmethod
    def carregar():
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"porta": "" if SISTEMA == "Windows" else "/dev/usb/lp0"}

    @staticmethod
    def salvar(porta):
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump({"porta": porta}, f)