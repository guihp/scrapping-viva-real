# 🚀 Guia de Deploy no Coolify

## ⚠️ IMPORTANTE: Configurar Build Pack

O Coolify está usando **Nixpacks** por padrão, mas para este projeto funcionar corretamente, você **DEVE** usar o **Dockerfile**.

## 📋 Passo a Passo

### 1. Acesse as Configurações do Recurso

No painel do Coolify, vá até o recurso que você criou e clique em **"Settings"** ou **"Configurações"**.

### 2. Configure o Build Pack

1. Procure pela seção **"Build Pack"** ou **"Build Configuration"**
2. **Mude de "Auto" ou "Nixpacks" para "Dockerfile"**
3. Isso garantirá que o Coolify use o `Dockerfile` que já está no repositório

### 3. Configure a Porta

- **Porta**: `8501`
- Certifique-se de que a porta está configurada corretamente

### 4. Variáveis de Ambiente (Opcional)

Se quiser usar funcionalidades de IA, adicione:
- `OPENAI_API_KEY`: Sua chave da API OpenAI

### 5. Faça um Novo Deploy

Após alterar o Build Pack para Dockerfile:
1. Clique em **"Redeploy"** ou **"Deploy"**
2. Aguarde o build completar
3. O Dockerfile irá instalar o Chrome e todas as dependências necessárias

## 🔍 Verificando se Está Funcionando

Após o deploy, acesse a URL fornecida pelo Coolify. Você deve ver a interface do Streamlit.

Se o Selenium não funcionar (erros relacionados ao Chrome), significa que o Nixpacks foi usado ao invés do Dockerfile. Nesse caso:

1. Verifique novamente se o Build Pack está configurado como **"Dockerfile"**
2. Faça um novo deploy

## ❓ Por que Dockerfile é necessário?

O Dockerfile instala:
- Google Chrome
- Todas as dependências do sistema para o Selenium
- Python e todas as bibliotecas Python

O Nixpacks não instala o Chrome automaticamente, então o Selenium não funcionará.

## 🐛 Troubleshooting

### Erro: "Chrome not found" ou "WebDriverException"

**Solução**: Configure o Build Pack como "Dockerfile" e faça um novo deploy.

### A aplicação não inicia

Verifique os logs no Coolify para ver o erro específico.

### Porta não acessível

Certifique-se de que a porta está configurada como `8501` no Coolify.


