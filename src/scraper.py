"""Classe principal do scraper do Viva Real."""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from functools import wraps

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from src.extractors import (
    extract_property_type, extract_modality, extract_price,
    extract_characteristics, extract_location, extract_description, extract_images, extract_codes
)
from src.validators import clean_data
from src.utils import get_headers, rate_limit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    """Decorator para retry logic."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= 1.5
            raise last_exception
        return wrapper
    return decorator


class VivaRealScraper:
    """Scraper para extrair dados de páginas de imóveis do Viva Real."""

    def __init__(self, headless: bool = False, timeout: int = 45):
        self.timeout = timeout
        self.driver = None
        self.headless = headless
        self._setup_driver()

    def _setup_driver(self):
        """Configura o WebDriver do Selenium."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        headers = get_headers()
        chrome_options.add_argument(f'user-agent={headers["User-Agent"]}')
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
        except Exception as e:
            logger.error(f"Erro ao configurar WebDriver: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def _wait_for_page_load(self):
        """Aguarda o carregamento completo da página e habilita interceptação de rede."""
        try:
            # Aguarda body básico
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Aguarda JavaScript carregar completamente
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                logger.warning("JavaScript não carregou completamente, mas continuando...")
            
            # Habilita performance logging para interceptação de rede
            try:
                self.driver.execute_cdp_cmd('Performance.enable', {})
                self.driver.execute_cdp_cmd('Network.enable', {})
            except Exception as e:
                logger.debug(f"Erro ao habilitar interceptação de rede: {e}")
            
            # Aguarda elementos específicos do Viva Real estarem presentes
            # Tenta encontrar pelo menos um destes elementos-chave
            key_selectors = [
                "h1",  # Título do imóvel
                "[class*='price']",  # Preço
                "[class*='Price']",
                "[data-testid*='price']",
                "title",  # Tag title
            ]
            
            element_found = False
            for selector in key_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    element_found = True
                    logger.debug(f"Elemento-chave encontrado: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not element_found:
                logger.warning("Elementos-chave não encontrados, mas continuando...")
            
            # Aguarda um pouco mais para garantir que conteúdo dinâmico carregou
            time.sleep(3)
            
        except TimeoutException:
            logger.warning("Timeout ao aguardar carregamento da página")

    def _clean_driver_state(self):
        """Limpa o estado do WebDriver antes de processar uma nova URL."""
        try:
            # Limpa cookies
            self.driver.delete_all_cookies()
            logger.debug("Cookies limpos")
            
            # Limpa localStorage e sessionStorage via JavaScript
            try:
                self.driver.execute_script("window.localStorage.clear();")
                self.driver.execute_script("window.sessionStorage.clear();")
                logger.debug("localStorage e sessionStorage limpos")
            except Exception as e:
                logger.debug(f"Erro ao limpar storage: {e}")
            
            # Limpa cache (desabilita e reabilita cache)
            try:
                self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
                logger.debug("Cache do navegador limpo")
            except Exception as e:
                logger.debug(f"Erro ao limpar cache: {e}")
            
            # Limpa logs de performance (desabilita e reabilita)
            try:
                self.driver.execute_cdp_cmd('Performance.disable', {})
                self.driver.execute_cdp_cmd('Network.disable', {})
                logger.debug("Logs de performance resetados")
            except Exception as e:
                logger.debug(f"Erro ao resetar logs: {e}")
                
        except Exception as e:
            logger.warning(f"Erro ao limpar estado do driver: {e}")

    def scrape(self, url: str) -> Dict:
        """Extrai dados de uma URL do Viva Real."""
        if not self.driver:
            raise RuntimeError("WebDriver não está inicializado")
        logger.info(f"Iniciando scraping de: {url}")
        try:
            # IMPORTANTE: Para múltiplas URLs, precisamos garantir que cada página seja processada isoladamente
            # Limpa estado do driver antes de carregar nova URL
            self._clean_driver_state()
            
            # Navega para a URL
            logger.info(f"Navegando para: {url}")
            self.driver.get(url)
            
            # Valida se realmente navegou para a URL correta
            time.sleep(1)  # Aguarda navegação completar
            current_url = self.driver.current_url
            # Normaliza URLs para comparação (remove parâmetros de query, etc)
            url_normalized = url.split('?')[0].strip('/')
            current_normalized = current_url.split('?')[0].strip('/')
            
            if url_normalized not in current_normalized and current_normalized not in url_normalized:
                logger.warning(f"URL navegada ({current_url}) não corresponde exatamente à URL solicitada ({url})")
                # Tenta navegar novamente
                time.sleep(1)
                self.driver.get(url)
                time.sleep(1)
                current_url = self.driver.current_url
                current_normalized = current_url.split('?')[0].strip('/')
                if url_normalized not in current_normalized and current_normalized not in url_normalized:
                    logger.error(f"Não foi possível navegar para {url}. URL atual: {current_url}")
                    # Continua mesmo assim, pode ser redirecionamento válido
                else:
                    logger.info(f"Navegação bem-sucedida na segunda tentativa: {current_url}")
            else:
                logger.debug(f"Navegação confirmada para: {current_url}")
            
            rate_limit(1, 2)
            self._wait_for_page_load()
            page_source = self.driver.page_source
            if not page_source or len(page_source) < 1000:
                raise ValueError("Página não carregou completamente")
            logger.info(f"Iniciando extração de dados para {url}")
            data = {
                'url': url,
                'scraped_at': datetime.utcnow().isoformat() + 'Z',
                'property_type': extract_property_type(self.driver, page_source),
                'category': None,
                'modality': extract_modality(self.driver, page_source),
                'price': extract_price(self.driver, page_source),
                'size_m2': None, 'bedrooms': None, 'suites': None,
                'bathrooms': None, 'garage': None,
                'location': extract_location(self.driver, page_source, use_ai=True),
                'description': extract_description(self.driver, page_source),
                'images': extract_images(self.driver, page_source, use_ai=True),
            }
            logger.info(f"Extraction inicial concluída: property_type={data.get('property_type') is not None}, price={data.get('price') is not None}, images={len(data.get('images', []))}")
            characteristics = extract_characteristics(self.driver, page_source)
            data.update(characteristics)
            codes = extract_codes(self.driver, page_source)
            data['advertiser_code'] = codes.get('advertiser_code')
            data['vivareal_code'] = codes.get('vivareal_code')
            
            # Validação pós-extração
            essential_fields = ['property_type', 'price', 'location']
            extracted_count = sum(1 for field in essential_fields if (
                data.get(field) is not None and 
                (not isinstance(data.get(field), dict) or data.get(field).get('city') is not None)
            ))
            
            if extracted_count == 0:
                logger.warning(f"Nenhum campo essencial foi extraído para {url}, tentando reextrair...")
                # Tenta aguardar mais um pouco e reextrair
                time.sleep(5)
                page_source = self.driver.page_source
                # Re-extrai campos essenciais
                if not data.get('property_type'):
                    data['property_type'] = extract_property_type(self.driver, page_source)
                if not data.get('price'):
                    data['price'] = extract_price(self.driver, page_source)
                if not data.get('location') or not data.get('location', {}).get('city'):
                    data['location'] = extract_location(self.driver, page_source, use_ai=True)
                
                # Loga resultado da re-extração
                re_extracted = sum(1 for field in essential_fields if (
                    data.get(field) is not None and 
                    (not isinstance(data.get(field), dict) or data.get(field).get('city') is not None)
                ))
                if re_extracted > 0:
                    logger.info(f"Re-extração bem-sucedida: {re_extracted} campos essenciais encontrados")
                else:
                    logger.error(f"Re-extração falhou: nenhum campo essencial encontrado para {url}")
            
            data = clean_data(data)
            logger.info(f"Scraping concluído com sucesso. Campos extraídos: property_type={data.get('property_type') is not None}, price={data.get('price') is not None}, location={data.get('location', {}).get('city') is not None}")
            return data
        except Exception as e:
            logger.error(f"Erro durante scraping: {e}", exc_info=True)
            raise

    def close(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

