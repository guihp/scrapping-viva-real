# 🔧 Configuração Completa no Coolify

## ✅ Checklist de Configuração

### 1. Configurações Gerais (Configuration → General)

- **Build Pack**: `Dockerfile` ✅
- **Ports Exposes**: `8501` ⚠️ **IMPORTANTE: Altere de 3000 para 8501**
- **Ports Mappings**: `8501:8501` ⚠️ **IMPORTANTE: Altere de 3000:3000 para 8501:8501**
- **Dockerfile Location**: `/Dockerfile` ✅

### 2. Healthcheck (Configuration → Healthcheck)

Configure o healthcheck para verificar se a aplicação está rodando:

- **Healthcheck Type**: `HTTP`
- **Healthcheck Path**: `/_stcore/health`
- **Healthcheck Port**: `8501`
- **Healthcheck Interval**: `30` (segundos)
- **Healthcheck Timeout**: `10` (segundos)
- **Healthcheck Retries**: `3`

### 3. Variáveis de Ambiente (Configuration → Environment Variables)

**NÃO é necessário adicionar variáveis de ambiente** para o funcionamento básico.

Apenas se quiser usar funcionalidades de IA:
- `OPENAI_API_KEY`: Sua chave da API OpenAI (opcional)

### 4. Domínio

O domínio já está configurado: `https://nccs84ckwgo04gg000s0c4s0.vemprajogo.com`

## 🚨 Problemas Comuns e Soluções

### Erro 502 Bad Gateway

**Causa**: Porta incorreta configurada no Coolify

**Solução**:
1. Vá em Configuration → General
2. Altere "Ports Exposes" de `3000` para `8501`
3. Altere "Ports Mappings" de `3000:3000` para `8501:8501`
4. Clique em "Save"
5. Faça um "Redeploy"

### Aplicação não responde

**Verifique**:
1. Os logs no Coolify (aba "Logs")
2. Se o container está "Running" (status verde)
3. Se o healthcheck está passando

### Healthcheck falhando

**Solução**:
1. Configure o healthcheck conforme instruções acima
2. Aguarde pelo menos 40 segundos após o deploy (tempo de inicialização)
3. Verifique os logs para ver se há erros

## 📝 Passo a Passo Completo

1. ✅ Build Pack configurado como "Dockerfile"
2. ✅ Porta alterada para 8501
3. ✅ Healthcheck configurado (opcional, mas recomendado)
4. ✅ Salvar todas as configurações
5. ✅ Fazer Redeploy
6. ✅ Aguardar build completar
7. ✅ Acessar o domínio fornecido pelo Coolify

## 🔍 Verificação Final

Após o deploy, você deve ver nos logs:
```
You can now view your Streamlit app in your browser.
URL: http://0.0.0.0:8501
```

E ao acessar o domínio, deve ver a interface do Streamlit funcionando.

