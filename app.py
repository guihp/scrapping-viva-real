"""Interface web visual para o scraper do Viva Real."""
import streamlit as st
import json
from pathlib import Path
from src.scraper import VivaRealScraper
from datetime import datetime
import time

# Configuração da página
st.set_page_config(
    page_title="Viva Real Scraper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .property-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        color: #1a1a1a;
        font-size: 1rem;
    }
    .info-box strong {
        color: #1f77b4;
        font-weight: 600;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">🏠 Viva Real Scraper</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    headless_mode = st.checkbox("Modo Headless", value=True, help="Executa sem abrir o navegador")
    timeout = st.slider("Timeout (segundos)", min_value=10, max_value=60, value=45, step=5)
    
    st.markdown("---")
    st.markdown("### 📖 Como usar")
    st.markdown("""
    1. Cole a URL do imóvel do Viva Real
    2. Clique em "Extrair Dados"
    3. Aguarde o processamento
    4. Visualize os dados extraídos
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Dica")
    st.info("Exemplo de URL:\n\n`https://www.vivareal.com.br/imovel/apartamento-...-id-1234567890/`")
    
    st.markdown("---")
    st.markdown("### 📚 Histórico")
    if 'scraping_history' in st.session_state and len(st.session_state['scraping_history']) > 0:
        st.success(f"✅ {len(st.session_state['scraping_history'])} imóvel(is) já extraído(s)")
        if st.button("🗑️ Limpar Histórico", use_container_width=True):
            st.session_state['scraping_history'] = []
            st.rerun()
    else:
        st.info("Nenhum imóvel extraído ainda")

# Área principal
st.markdown("### 📥 Entrada de Dados")
input_mode = st.radio(
    "Selecione o modo de entrada:",
    ["URL Única", "Lista de URLs"],
    horizontal=True
)

if input_mode == "URL Única":
    col1, col2 = st.columns([3, 1])
    with col1:
        url_input = st.text_input(
            "🔗 URL do Imóvel",
            placeholder="Cole aqui a URL do imóvel do Viva Real...",
            help="A URL deve ser do site vivareal.com.br e conter '/imovel/' no caminho"
        )
    with col2:
        st.write("")  # Espaçamento
        st.write("")  # Espaçamento
        scrape_button = st.button("🚀 Extrair Dados", type="primary", use_container_width=True)
    url_list = None
else:
    url_list = st.text_area(
        "📋 Lista de URLs (uma por linha)",
        placeholder="Cole aqui as URLs, uma em cada linha:\nhttps://www.vivareal.com.br/imovel/...-id-123/\nhttps://www.vivareal.com.br/imovel/...-id-456/\n...",
        height=150,
        help="Cole múltiplas URLs do Viva Real, uma em cada linha"
    )
    scrape_button = st.button("🚀 Extrair Todos os Imóveis", type="primary", use_container_width=True)
    url_input = None

# Validação da URL
def validate_url(url: str) -> bool:
    """Valida se a URL é do Viva Real."""
    if not url:
        return False
    return 'vivareal.com.br' in url.lower() and '/imovel/' in url.lower()

# Função auxiliar para processar uma única URL
def process_single_url(url: str, scraper: VivaRealScraper, progress_bar=None, status_text=None, total=None):
    """Processa uma única URL e retorna os dados."""
    try:
        if status_text:
            status_text.text(f"🔄 Processando: {url[:60]}...")
        
        data = scraper.scrape(url)
        
        # Valida se os dados foram extraídos corretamente
        if not data or not isinstance(data, dict):
            return None, "Dados extraídos estão vazios ou em formato incorreto"
        
        # Valida se pelo menos alguns dados essenciais foram coletados
        if not data.get('url') or data.get('url') != url:
            return None, f"URL do dado extraído ({data.get('url')}) não corresponde à URL solicitada ({url})"
        
        # Salvar dados
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        property_id = url.split('-id-')[1].split('/')[0] if '-id-' in url else str(int(time.time()))
        filename = f"property_{property_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Adiciona ao histórico/cache
        if 'scraping_history' not in st.session_state:
            st.session_state['scraping_history'] = []
        st.session_state['scraping_history'].append({
            'timestamp': data.get('scraped_at'),
            'url': url,
            'property_id': property_id,
            'data': data,
            'filepath': str(filepath)
        })
        
        if progress_bar and total:
            completed = len(st.session_state.get('scraping_history', []))
            progress_bar.progress(completed / total)
        
        return data, None
    except Exception as e:
        return None, str(e)

# Processamento

if scrape_button:
    if input_mode == "URL Única":
        if not url_input:
            st.error("❌ Por favor, insira uma URL")
        elif not validate_url(url_input):
            st.error("❌ URL inválida! A URL deve ser do Viva Real e conter '/imovel/' no caminho.")
        else:
            with st.spinner("🔄 Extraindo dados... Isso pode levar alguns segundos..."):
                try:
                    with VivaRealScraper(headless=headless_mode, timeout=timeout) as scraper:
                        data = scraper.scrape(url_input)
                    
                    st.success("✅ Dados extraídos com sucesso!")
                    st.balloons()
                    
                    # Salvar dados
                    output_dir = Path("data/output")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    property_id = url_input.split('-id-')[1].split('/')[0] if '-id-' in url_input else str(int(time.time()))
                    filename = f"property_{property_id}.json"
                    filepath = output_dir / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    # Adiciona ao histórico/cache
                    if 'scraping_history' not in st.session_state:
                        st.session_state['scraping_history'] = []
                    st.session_state['scraping_history'].append({
                        'timestamp': data.get('scraped_at'),
                        'url': url_input,
                        'property_id': property_id,
                        'data': data,
                        'filepath': str(filepath)
                    })
                    
                    st.session_state['scraped_data'] = data
                    st.session_state['filepath'] = str(filepath)
                    
                except Exception as e:
                    st.error(f"❌ Erro ao extrair dados: {str(e)}")
                    st.exception(e)
    else:  # Lista de URLs
        if not url_list or not url_list.strip():
            st.error("❌ Por favor, insira pelo menos uma URL")
        else:
            # Processa lista de URLs
            urls = [url.strip() for url in url_list.split('\n') if url.strip()]
            valid_urls = [url for url in urls if validate_url(url)]
            invalid_urls = [url for url in urls if not validate_url(url)]
            
            if invalid_urls:
                st.warning(f"⚠️ {len(invalid_urls)} URL(s) inválida(s) foram ignoradas")
                with st.expander("Ver URLs inválidas"):
                    for url in invalid_urls:
                        st.text(url)
            
            if not valid_urls:
                st.error("❌ Nenhuma URL válida encontrada!")
            else:
                st.info(f"📋 Processando {len(valid_urls)} imóvel(is)...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                successful = 0
                failed = 0
                errors_list = []
                
                with VivaRealScraper(headless=headless_mode, timeout=timeout) as scraper:
                    for idx, url in enumerate(valid_urls, 1):
                        data, error = process_single_url(url, scraper, progress_bar, status_text, len(valid_urls))
                        if data:
                            successful += 1
                        else:
                            failed += 1
                            errors_list.append({'url': url, 'error': error})
                        
                        # Delay maior entre requisições para garantir que página anterior foi processada
                        # O estado já é limpo automaticamente pelo scraper, mas adiciona delay para evitar rate limiting
                        if idx < len(valid_urls):
                            time.sleep(3)
                
                progress_bar.progress(1.0)
                status_text.empty()
                
                if successful > 0:
                    st.success(f"✅ {successful} imóvel(is) extraído(s) com sucesso!")
                    st.balloons()
                    
                    # Mostra o último imóvel processado
                    if st.session_state.get('scraping_history'):
                        last_property = st.session_state['scraping_history'][-1]
                        st.session_state['scraped_data'] = last_property['data']
                
                if failed > 0:
                    st.warning(f"⚠️ {failed} imóvel(is) falharam durante a extração")
                    with st.expander("Ver erros"):
                        for error_item in errors_list:
                            st.error(f"**URL:** {error_item['url']}\n**Erro:** {error_item['error']}")

# Exibição dos dados
if 'scraped_data' in st.session_state:
    data = st.session_state['scraped_data']
    
    st.markdown("---")
    st.markdown(f'<div class="success-box"><h2>📊 Dados Extraídos</h2></div>', unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Preço", f"R$ {data.get('price', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if data.get('price') else "N/A")
    
    with col2:
        st.metric("📐 Metragem", f"{data.get('size_m2', 'N/A')} m²" if data.get('size_m2') else "N/A")
    
    with col3:
        st.metric("🛏️ Quartos", data.get('bedrooms', 'N/A'))
    
    with col4:
        st.metric("🚿 Banheiros", data.get('bathrooms', 'N/A'))
    
    # Informações detalhadas
    st.markdown("### 📝 Informações Detalhadas")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f'<div class="info-box"><strong>🏠 Tipo:</strong> {data.get("property_type", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box"><strong>💼 Modalidade:</strong> {data.get("modality", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box"><strong>🛏️ Suítes:</strong> {data.get("suites", "N/A") if data.get("suites") is not None else "N/A"}</div>', unsafe_allow_html=True)
        garage_value = data.get("garage")
        st.markdown(f'<div class="info-box"><strong>🚗 Vagas:</strong> {garage_value if garage_value is not None else "N/A"}</div>', unsafe_allow_html=True)
    
    with info_col2:
        location = data.get('location', {})
        city = location.get("city", "N/A")
        st.markdown(f'<div class="info-box"><strong>📍 Cidade:</strong> {city}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box"><strong>🏘️ Bairro:</strong> {location.get("neighborhood", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box"><strong>🛣️ Endereço:</strong> {location.get("street", "N/A")}, {location.get("number", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box"><strong>📮 CEP:</strong> {location.get("zipcode", "N/A")}</div>', unsafe_allow_html=True)
        map_link = location.get("map_link")
        if map_link:
            st.markdown(f'<div class="info-box"><strong>🗺️ Link da Localização:</strong> <a href="{map_link}" target="_blank" style="color: #1f77b4;">Ver no Mapa</a></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box"><strong>🗺️ Link da Localização:</strong> N/A</div>', unsafe_allow_html=True)
    
    # Códigos (advertiser e vivareal)
    if data.get('advertiser_code') or data.get('vivareal_code'):
        st.markdown("### 🔢 Códigos do Anúncio")
        codes_col1, codes_col2 = st.columns(2)
        with codes_col1:
            st.markdown(f'<div class="info-box"><strong>📋 Código do Anunciante:</strong> {data.get("advertiser_code", "N/A")}</div>', unsafe_allow_html=True)
        with codes_col2:
            st.markdown(f'<div class="info-box"><strong>🔖 Código no Viva Real:</strong> {data.get("vivareal_code", "N/A")}</div>', unsafe_allow_html=True)
    
    # Descrição
    if data.get('description'):
        st.markdown("### 📄 Descrição")
        st.markdown(f'<div class="info-box">{data["description"][:500]}{"..." if len(data["description"]) > 500 else ""}</div>', unsafe_allow_html=True)
        with st.expander("Ver descrição completa"):
            st.text_area("", value=data['description'], height=200, disabled=True)
    
    # Imagens
    images = data.get('images', [])
    if images:
        st.markdown(f"### 🖼️ Imagens ({len(images)} encontradas)")
        # Mostra as primeiras 6 imagens em grid
        cols = st.columns(3)
        for idx, img_url in enumerate(images[:6]):
            with cols[idx % 3]:
                try:
                    st.image(img_url, use_container_width=True, caption=f"Imagem {idx + 1}")
                except:
                    st.markdown(f"[Link da Imagem {idx + 1}]({img_url})")
        if len(images) > 6:
            with st.expander(f"Ver todas as {len(images)} imagens"):
                for idx, img_url in enumerate(images[6:], start=7):
                    try:
                        st.image(img_url, use_container_width=True, caption=f"Imagem {idx}")
                    except:
                        st.markdown(f"[Link da Imagem {idx}]({img_url})")
    
    # Download do JSON
    st.markdown("---")
    st.markdown("### 💾 Download dos Dados")
    
    download_col1, download_col2 = st.columns(2)
    
    with download_col1:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        property_id = data.get('url', '').split('-id-')[1].split('/')[0] if '-id-' in data.get('url', '') else 'data'
        st.download_button(
            label="📥 Baixar JSON Atual",
            data=json_str,
            file_name=f"property_{property_id}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with download_col2:
        # Botão para baixar todos os JSONs do histórico
        if 'scraping_history' in st.session_state and len(st.session_state['scraping_history']) > 0:
            all_data = {
                'total_properties': len(st.session_state['scraping_history']),
                'exported_at': datetime.utcnow().isoformat() + 'Z',
                'properties': [item['data'] for item in st.session_state['scraping_history']]
            }
            all_json_str = json.dumps(all_data, ensure_ascii=False, indent=2)
            st.download_button(
                label=f"📦 Baixar Todos ({len(st.session_state['scraping_history'])} imóveis)",
                data=all_json_str,
                file_name=f"all_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Exibir JSON completo
    with st.expander("📋 Ver JSON Completo"):
        st.json(data)
    
    st.info(f"💾 Arquivo salvo em: {st.session_state.get('filepath', 'N/A')}")

# Rodapé
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Viva Real Scraper - Extração de dados de imóveis</div>", unsafe_allow_html=True)

