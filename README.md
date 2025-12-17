# 🏠 Viva Real Scraper - Interface Visual

Scraper com interface web visual para extrair dados de imóveis do Viva Real.

## ✨ Características

- 🎨 **Interface Web Visual** - Interface moderna e intuitiva
- 📊 **Visualização de Dados** - Dados exibidos de forma organizada
- 🖼️ **Preview de Imagens** - Visualização das imagens do imóvel
- 💾 **Download JSON** - Baixe os dados extraídos facilmente
- ⚡ **Processamento Rápido** - Extração eficiente de dados

## 🚀 Instalação

### Instalação Local

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

### 🐳 Deploy no Coolify

Este projeto está preparado para deploy no Coolify. Siga os passos:

1. **Conecte o repositório no Coolify:**
   - Acesse seu painel do Coolify
   - Crie um novo recurso
   - Selecione "GitHub" como fonte
   - Conecte o repositório: `https://github.com/guihp/scrapping-viva-real.git`
   - Selecione a branch `main`

2. **Configurações no Coolify:**
   - **Tipo de Build**: Dockerfile
   - **Porta**: 8501
   - **Comando de Build**: (deixe vazio, o Dockerfile já está configurado)
   - **Comando de Start**: (deixe vazio, o Dockerfile já está configurado)

3. **Variáveis de Ambiente (Opcional):**
   - `OPENAI_API_KEY`: Chave da API OpenAI (apenas se quiser usar funcionalidades de IA)
   - `STREAMLIT_SERVER_PORT`: Porta do Streamlit (padrão: 8501)
   - `STREAMLIT_SERVER_ADDRESS`: Endereço do servidor (padrão: 0.0.0.0)

4. **Deploy:**
   - Clique em "Deploy" e aguarde o build
   - O Coolify irá construir a imagem Docker automaticamente
   - Após o build, a aplicação estará disponível na URL fornecida pelo Coolify

**Nota:** O Dockerfile já está configurado com todas as dependências necessárias, incluindo Chrome para o Selenium.

## 💻 Como Usar

### Interface Web (Recomendado)

Execute o comando abaixo para iniciar a interface visual:

```bash
streamlit run app.py
```

Isso abrirá automaticamente uma página no seu navegador com a interface.

### Passos para usar:

1. Cole a URL do imóvel do Viva Real no campo de texto
2. Ajuste as configurações na sidebar (opcional)
3. Clique em "🚀 Extrair Dados"
4. Aguarde o processamento
5. Visualize os dados extraídos de forma organizada
6. Baixe o JSON se desejar

## 📋 Dados Extraídos

- **Informações Básicas**: Tipo, modalidade, preço
- **Características**: Metragem, quartos, suítes, banheiros, vagas
- **Localização**: Cidade, bairro, endereço completo, CEP
- **Descrição**: Texto completo do anúncio
- **Imagens**: URLs de até 15 imagens

## 🛠️ Tecnologias

- **Streamlit** - Interface web
- **Selenium** - Web scraping
- **BeautifulSoup** - Parsing HTML
- **Pandas** - Processamento de dados

## 📝 Exemplo de URL

```
https://www.vivareal.com.br/imovel/apartamento-3-quartos-olho-d-agua-bairros-sao-luis-com-garagem-95m2-venda-RS990000-id-2858257670/
```

## ⚙️ Configurações

Na sidebar da interface você pode configurar:

- **Modo Headless**: Executa sem abrir o navegador (mais rápido)
- **Timeout**: Tempo de espera para carregamento da página

## 📦 Estrutura do Projeto

```
scrapinh/
├── app.py              # Interface web (Streamlit)
├── src/
│   ├── scraper.py      # Classe principal do scraper
│   ├── extractors.py   # Funções de extração
│   ├── validators.py   # Validação de dados
│   └── utils.py        # Utilitários
├── data/
│   └── output/         # Arquivos JSON salvos
└── requirements.txt    # Dependências
```

## 🎯 Funcionalidades da Interface

- ✅ Input de URL com validação
- ✅ Métricas visuais (preço, metragem, quartos, banheiros)
- ✅ Cards informativos organizados
- ✅ Preview de imagens em grid
- ✅ Visualização de descrição completa
- ✅ Download do JSON
- ✅ Exibição do JSON completo
- ✅ Feedback visual durante processamento

## 🔧 Troubleshooting

### Erro ao instalar Streamlit

```bash
pip install --upgrade pip
pip install streamlit
```

### Chrome não encontrado

O scraper precisa do Chrome instalado. O ChromeDriver é baixado automaticamente.

### Timeout

Se a página demorar muito para carregar, aumente o timeout na sidebar.

## 📄 Licença

Este projeto é fornecido "como está", sem garantias.


