# 🚀 Agente de Impressão Térmica - Guia de Lançamento (Release)

Este projeto possui uma esteira de CI/CD (GitHub Actions) configurada para **compilação na nuvem** e **atualização automática** (Auto-Update) nos clientes.

Sempre que você quiser lançar uma nova versão para os usuários, **não é necessário compilar o `.exe` manualmente**. Basta seguir os 3 passos abaixo.

---

## 📦 Como lançar uma nova versão

### Passo 1: Salve e envie seu código para a `main`
Certifique-se de que tudo está testado localmente (onde a versão roda como `DEV_VERSION`). Adicione e comite suas alterações normalmente:
```bash
git add .
git commit -m "Sua mensagem sobre o que mudou nesta versão"
git push origin main

```

### Passo 2: Crie a Tag da nova versão

O GitHub Actions está programado para agir **apenas** quando recebe uma Tag que começa com a letra `v`. Escolha o número da sua nova versão (ex: `v1.0.1`, `v1.1.0`, `v2.0.0`):

```bash
git tag v1.0.1

```

### Passo 3: Envie a Tag para o GitHub (O Gatilho)

Envie essa Tag específica para o servidor. É este comando que aciona a automação:

```bash
git push origin v1.0.1

```

*(Se preferir, você pode enviar todas as tags de uma vez com `git push --tags`)*

---

## ⚙️ O que acontece nos bastidores?

Ao rodar o Passo 3, o GitHub fará o seguinte automaticamente (leva cerca de 2 minutos):

1. Sobe um servidor Windows limpo.
2. Abre o seu arquivo `config.py` e substitui a palavra `"DEV_VERSION"` por `"v1.0.1"`.
3. Instala o PyInstaller e compila o `main.py` em um único `Agente_Impressao.exe`.
4. Cria uma página de **Release** pública no seu repositório e anexa o executável.

**Fim!** Assim que a Release for publicada, todos os aplicativos abertos nos computadores dos seus clientes vão detectar a nova versão, baixar o `.exe` silenciosamente, substituir o arquivo antigo e reiniciar sozinhos.

---

## ⚠️ Pontos de Atenção (Checklist)

* **Prefixo Obrigatório:** A tag **precisa** começar com a letra minúscula `v` (ex: `v1.2.3`), caso contrário, o GitHub Actions vai ignorar.
* **Variável de Repositório:** Se um dia você mudar o nome do seu projeto ou o seu nome de usuário no GitHub, lembre-se de atualizar a variável `REPO_GITHUB` dentro do arquivo `config.py`, ou o Auto-Updater dos clientes não conseguirá achar a nova versão.

```