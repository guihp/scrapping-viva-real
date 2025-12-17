"""Funções para extrair dados específicos das páginas do Viva Real."""
import re
import json
import time
import logging
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


def extract_property_type(driver: WebDriver, page_source: str) -> Optional[str]:
    """Extrai o tipo do imóvel (Apartamento, Casa, etc.)."""
    if not page_source or len(page_source) < 100:
        logger.warning("page_source vazio ou muito pequeno para extrair tipo do imóvel")
        return None
    
    try:
        logger.debug("Iniciando extração de tipo do imóvel")
        soup = BeautifulSoup(page_source, 'lxml')
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            property_types = ['Apartamento', 'Casa', 'Cobertura', 'Terreno', 
                            'Sobrado', 'Kitnet', 'Studio', 'Loft', 'Sala']
            for prop_type in property_types:
                if prop_type.lower() in title_text.lower():
                    logger.debug(f"Tipo do imóvel encontrado no título: {prop_type}")
                    return prop_type
        try:
            breadcrumb_items = driver.find_elements(By.CSS_SELECTOR, "nav[aria-label='Breadcrumb'] a, nav[name='Breadcrumb'] a")
            logger.debug(f"Encontrados {len(breadcrumb_items)} itens de breadcrumb")
            for item in breadcrumb_items:
                text = item.text.strip()
                for prop_type in property_types:
                    if prop_type.lower() in text.lower():
                        logger.debug(f"Tipo do imóvel encontrado no breadcrumb: {prop_type}")
                        return prop_type
        except Exception as e:
            logger.debug(f"Erro ao buscar breadcrumb: {e}")
        logger.debug("Tipo do imóvel não encontrado")
    except Exception as e:
        logger.warning(f"Erro ao extrair tipo do imóvel: {e}")
    return None


def extract_modality(driver: WebDriver, page_source: str) -> Optional[str]:
    """Extrai a modalidade (Venda ou Aluguel)."""
    if not page_source or len(page_source) < 100:
        logger.warning("page_source vazio ou muito pequeno para extrair modalidade")
        return None
    
    try:
        logger.debug("Iniciando extração de modalidade")
        soup = BeautifulSoup(page_source, 'lxml')
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            if 'venda' in title_text.lower() or 'por r$' in title_text.lower():
                return 'Venda'
            elif 'aluguel' in title_text.lower() or 'alugar' in title_text.lower():
                return 'Aluguel'
        current_url = driver.current_url
        if '/venda/' in current_url.lower():
            return 'Venda'
        elif '/aluguel/' in current_url.lower():
            return 'Aluguel'
    except Exception as e:
        logger.warning(f"Erro ao extrair modalidade: {e}")
    return None


def extract_price(driver: WebDriver, page_source: str) -> Optional[float]:
    """Extrai o preço do imóvel."""
    if not page_source or len(page_source) < 100:
        logger.warning("page_source vazio ou muito pequeno para extrair preço")
        return None
    
    try:
        logger.debug("Iniciando extração de preço")
        soup = BeautifulSoup(page_source, 'lxml')
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            price_match = re.search(r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', title_text)
            if price_match:
                price_str = price_match.group(1).replace('.', '').replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    pass
    except Exception as e:
        logger.warning(f"Erro ao extrair preço: {e}")
    return None


def extract_characteristics(driver: WebDriver, page_source: str) -> Dict[str, Optional[int]]:
    """Extrai características do imóvel (tamanho, quartos, banheiros, etc.)."""
    if not page_source or len(page_source) < 100:
        logger.warning("page_source vazio ou muito pequeno para extrair características")
        return {'size_m2': None, 'bedrooms': None, 'suites': None, 'bathrooms': None, 'garage': None}
    
    logger.debug("Iniciando extração de características")
    """Extrai características do imóvel."""
    result = {'size_m2': None, 'bedrooms': None, 'bathrooms': None, 'suites': None, 'garage': None}
    try:
        soup = BeautifulSoup(page_source, 'lxml')
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            size_match = re.search(r'(\d+)\s*m[²2]', title_text, re.IGNORECASE)
            if size_match:
                try:
                    result['size_m2'] = int(size_match.group(1))
                except ValueError:
                    pass
            bedrooms_match = re.search(r'(\d+)\s*quarto', title_text, re.IGNORECASE)
            if bedrooms_match:
                try:
                    result['bedrooms'] = int(bedrooms_match.group(1))
                except ValueError:
                    pass
            bathrooms_match = re.search(r'(\d+)\s*banheiro', title_text, re.IGNORECASE)
            if bathrooms_match:
                try:
                    result['bathrooms'] = int(bathrooms_match.group(1))
                except ValueError:
                    pass
            # Procura por vagas no título
            garage_match = re.search(r'(\d+)\s*vaga', title_text, re.IGNORECASE)
            if garage_match:
                try:
                    result['garage'] = int(garage_match.group(1))
                except ValueError:
                    pass
        
        # Procura nos elementos da página
        try:
            # Procura por lista de características
            feature_elements = driver.find_elements(By.CSS_SELECTOR, 
                "li, [class*='feature'], [class*='characteristic'], [data-testid*='feature']")
            for element in feature_elements:
                text = element.text.strip().lower()
                # Vagas
                if not result['garage']:
                    garage_patterns = [r'(\d+)\s*vaga', r'(\d+)\s*garagem', r'garagem[:\s]*(\d+)']
                    for pattern in garage_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            try:
                                result['garage'] = int(match.group(1))
                                break
                            except ValueError:
                                pass
        except Exception:
            pass
        
        body_text = soup.get_text()
        if not result['size_m2']:
            size_match = re.search(r'(\d+)\s*m[²2]', body_text, re.IGNORECASE)
            if size_match:
                try:
                    result['size_m2'] = int(size_match.group(1))
                except ValueError:
                    pass
        if not result['bedrooms']:
            bedrooms_match = re.search(r'(\d+)\s*quarto', body_text, re.IGNORECASE)
            if bedrooms_match:
                try:
                    result['bedrooms'] = int(bedrooms_match.group(1))
                except ValueError:
                    pass
        if not result['bathrooms']:
            bathrooms_match = re.search(r'(\d+)\s*banheiro', body_text, re.IGNORECASE)
            if bathrooms_match:
                try:
                    result['bathrooms'] = int(bathrooms_match.group(1))
                except ValueError:
                    pass
        if not result['garage']:
            garage_patterns = [r'(\d+)\s*vaga', r'(\d+)\s*garagem', r'garagem[:\s]*(\d+)']
            for pattern in garage_patterns:
                garage_match = re.search(pattern, body_text, re.IGNORECASE)
                if garage_match:
                    try:
                        result['garage'] = int(garage_match.group(1))
                        break
                    except ValueError:
                        pass
    except Exception as e:
        logger.warning(f"Erro ao extrair características: {e}")
    logger.debug(f"Características extraídas: {result}")
    return result


def extract_location(driver: WebDriver, page_source: str, use_ai: bool = True) -> Dict[str, Optional[str]]:
    """Extrai informações de localização."""
    location = {'city': None, 'neighborhood': None, 'street': None, 'number': None, 'zipcode': None, 'complement': None, 'map_link': None}
    try:
        soup = BeautifulSoup(page_source, 'lxml')
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # Melhor extração da cidade - pega tudo após "em" até o final ou vírgula
            # Melhor regex para cidade - tenta pegar nome completo
            city_patterns = [
                r'em\s+([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç\s]+?)(?:,|\s*-\s*|$)',  # Cidade com capital inicial
                r'em\s+([^,]+?)(?:,|$)',  # Fallback
            ]
            for pattern in city_patterns:
                city_match = re.search(pattern, title_text, re.IGNORECASE)
                if city_match:
                    city = city_match.group(1).strip()
                    # Remove vírgulas e pontos no final
                    city = re.sub(r'[,\.\s-]+$', '', city).strip()
                    # Se for muito curto (menos de 3 caracteres), tenta pegar mais
                    if len(city) >= 3:  # Aceita apenas cidades com pelo menos 3 caracteres
                        location['city'] = city
                        break
            address_match = re.search(r'na\s+([^,]+?),\s*(\d+),\s*([^,]+?)\s+em', title_text, re.IGNORECASE)
            if address_match:
                location['street'] = address_match.group(1).strip()
                location['number'] = address_match.group(2).strip()
                location['neighborhood'] = address_match.group(3).strip()
        
        # Tenta encontrar cidade em outros lugares da página
        if not location['city']:
            try:
                # Procura em breadcrumbs ou elementos de localização
                location_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='location'], [class*='Location'], [class*='city'], [class*='City']")
                for element in location_elements:
                    text = element.text.strip()
                    if text and len(text) < 50:  # Cidade geralmente é texto curto
                        # Verifica se parece ser uma cidade (não contém números ou caracteres especiais demais)
                        if re.match(r'^[A-Za-záàâãéèêíìîóòôõúùûç\s]+$', text):
                            location['city'] = text
                            break
            except Exception:
                pass
        
        # Extrai link de localização/mapa
        try:
            # Procura por links que contenham mapas ou localização
            map_selectors = [
                "a[href*='maps']",
                "a[href*='google']",
                "a[href*='mapa']",
                "a[href*='location']",
                "a[href*='coordinates']",
                "[class*='map'] a",
                "[class*='Map'] a",
                "[class*='location'] a",
                "[class*='Location'] a",
                "[data-testid*='map'] a",
                "[data-testid*='location'] a",
                "button[onclick*='map']",
                "button[onclick*='location']",
            ]
            
            for selector in map_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # Tenta pegar o href
                        map_url = element.get_attribute('href')
                        if not map_url:
                            # Tenta pegar data-href ou onclick
                            map_url = element.get_attribute('data-href') or element.get_attribute('data-url')
                        
                        if map_url:
                            map_url_lower = map_url.lower()
                            # EXCLUI links do mapa do site do Viva Real
                            if 'mapa-do-site' in map_url_lower or 'sitemap' in map_url_lower:
                                continue
                            
                            # Aceita apenas Google Maps ou links com coordenadas
                            is_valid_map = (
                                'google.com/maps' in map_url_lower or
                                ('maps.google' in map_url_lower) or
                                ('/maps/' in map_url_lower and 'google' in map_url_lower) or
                                ('lat=' in map_url_lower and 'lng=' in map_url_lower)
                            )
                            
                            if is_valid_map:
                                # Garante que seja uma URL completa
                                if map_url.startswith('//'):
                                    map_url = 'https:' + map_url
                                elif map_url.startswith('/'):
                                    continue  # URLs relativas não são válidas para Google Maps
                                
                                location['map_link'] = map_url
                                logger.info(f"Link do Google Maps encontrado: {map_url}")
                                break
                    
                    if location['map_link']:
                        break
                except Exception:
                    continue
            
            # Se não encontrou link direto, procura em elementos com texto relacionado a mapa/localização
            if not location['map_link']:
                try:
                    map_text_elements = driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'Ver no mapa') or contains(text(), 'Mapa') or contains(text(), 'Localização')]")
                    for element in map_text_elements:
                        # Procura link pai ou filho
                        try:
                            link_element = element.find_element(By.XPATH, ".//ancestor::a[1] | .//a[1]")
                            map_url = link_element.get_attribute('href')
                            if map_url:
                                map_url_lower = map_url.lower()
                                # EXCLUI links do mapa do site
                                if 'mapa-do-site' in map_url_lower or 'sitemap' in map_url_lower:
                                    continue
                                # Aceita apenas Google Maps
                                if 'google.com/maps' in map_url_lower or ('maps.google' in map_url_lower):
                                    if map_url.startswith('//'):
                                        map_url = 'https:' + map_url
                                    location['map_link'] = map_url
                                    break
                        except:
                            continue
                except Exception:
                    pass
            
            # Se ainda não encontrou, tenta construir URL do Google Maps com os dados do endereço
            if not location['map_link'] and location.get('street') and location.get('city'):
                try:
                    address_parts = []
                    if location.get('street'):
                        address_parts.append(location['street'])
                    if location.get('number'):
                        address_parts.append(location['number'])
                    if location.get('neighborhood'):
                        address_parts.append(location['neighborhood'])
                    if location.get('city'):
                        address_parts.append(location['city'])
                    
                    if address_parts:
                        full_address = ', '.join([part for part in address_parts if part])
                        # Cria link do Google Maps
                        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={full_address.replace(' ', '+')}"
                        location['map_link'] = google_maps_url
                        logger.info(f"Link do Google Maps gerado: {google_maps_url}")
                except Exception as e:
                    logger.debug(f"Erro ao gerar link do Google Maps: {e}")
                    
        except Exception as e:
            logger.warning(f"Erro ao extrair link de localização: {e}")
        
        # Se não encontrou localização completa e AI está habilitada, tenta usar IA
        if (not location.get('city') or location.get('city') == 'São' or 
            not location.get('map_link') or 'mapa-do-site' in location.get('map_link', '')) and use_ai:
            try:
                from src.ai_helper import extract_location_with_ai
                logger.info("Tentando usar IA para melhorar localização...")
                current_url = driver.current_url
                html_snippet = page_source[:15000]
                ai_location = extract_location_with_ai(html_snippet, current_url)
                
                # Atualiza apenas se IA encontrou dados melhores
                if ai_location.get('city') and len(ai_location.get('city', '')) > len(location.get('city', '')):
                    location['city'] = ai_location.get('city')
                if ai_location.get('neighborhood') and not location.get('neighborhood'):
                    location['neighborhood'] = ai_location.get('neighborhood')
                if ai_location.get('street') and not location.get('street'):
                    location['street'] = ai_location.get('street')
                if ai_location.get('number') and not location.get('number'):
                    location['number'] = ai_location.get('number')
                if ai_location.get('zipcode') and not location.get('zipcode'):
                    location['zipcode'] = ai_location.get('zipcode')
                if ai_location.get('map_link') and 'google.com/maps' in ai_location.get('map_link', ''):
                    location['map_link'] = ai_location.get('map_link')
                    logger.info(f"IA encontrou link do Google Maps: {location['map_link']}")
                
            except Exception as e:
                logger.debug(f"Erro ao usar IA para localização: {e}")
        
        # Se ainda não tem map_link válido, tenta construir do endereço
        if not location.get('map_link') or 'mapa-do-site' in location.get('map_link', ''):
            try:
                address_parts = []
                if location.get('street'):
                    address_parts.append(location['street'])
                if location.get('number'):
                    address_parts.append(location['number'])
                if location.get('neighborhood'):
                    address_parts.append(location['neighborhood'])
                if location.get('city') and location['city'] != 'São':  # Evita usar cidade incompleta
                    address_parts.append(location['city'])
                
                if len(address_parts) >= 2:  # Precisa de pelo menos 2 partes
                    full_address = ', '.join([part for part in address_parts if part])
                    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={full_address.replace(' ', '+')}"
                    location['map_link'] = google_maps_url
                    logger.info(f"Google Maps gerado do endereço: {google_maps_url}")
            except Exception as e:
                logger.debug(f"Erro ao gerar link do Google Maps: {e}")
                
    except Exception as e:
        logger.warning(f"Erro ao extrair localização: {e}")
    return location


def extract_description(driver: WebDriver, page_source: str) -> Optional[str]:
    """Extrai a descrição completa do imóvel."""
    try:
        soup = BeautifulSoup(page_source, 'lxml')
        description_selectors = [
            "[class*='description']",
            "[class*='Description']",
            "[data-testid*='description']",
        ]
        for selector in description_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if len(text) > 50:
                        lines = text.split('\n')
                        description_lines = []
                        for line in lines:
                            line = line.strip()
                            if line and not any(header in line.lower() for header in ['descrição', 'características']):
                                description_lines.append(line)
                        if description_lines:
                            return '\n'.join(description_lines)
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"Erro ao extrair descrição: {e}")
    return None


def extract_codes(driver: WebDriver, page_source: str) -> Dict[str, Optional[str]]:
    """Extrai códigos do anunciante e do Viva Real."""
    codes = {'advertiser_code': None, 'vivareal_code': None}
    try:
        soup = BeautifulSoup(page_source, 'lxml')
        body_text = soup.get_text()
        
        # Procura por padrões de código
        # Código do anunciante: MF1203, etc
        advertiser_match = re.search(r'Código\s+do\s+anunciante[:\s]*([A-Z0-9]+)', body_text, re.IGNORECASE)
        if advertiser_match:
            codes['advertiser_code'] = advertiser_match.group(1).strip()
        
        # Código Viva Real: pode estar no formato "Código no Viva Real: 2856559150" ou "-id-2856559150"
        vivareal_match = re.search(r'Código\s+(?:no\s+)?Viva\s+Real[:\s]*(\d+)', body_text, re.IGNORECASE)
        if vivareal_match:
            codes['vivareal_code'] = vivareal_match.group(1).strip()
        
        # Se não encontrou, tenta extrair da URL
        if not codes['vivareal_code']:
            current_url = driver.current_url
            id_match = re.search(r'-id-(\d+)', current_url)
            if id_match:
                codes['vivareal_code'] = id_match.group(1)
        
        # Tenta encontrar nos elementos da página
        try:
            code_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Código')]")
            for element in code_elements:
                text = element.text
                if 'anunciante' in text.lower():
                    match = re.search(r'Código\s+do\s+anunciante[:\s]*([A-Z0-9]+)', text, re.IGNORECASE)
                    if match and not codes['advertiser_code']:
                        codes['advertiser_code'] = match.group(1).strip()
                if 'viva real' in text.lower():
                    match = re.search(r'Código\s+(?:no\s+)?Viva\s+Real[:\s]*(\d+)', text, re.IGNORECASE)
                    if match and not codes['vivareal_code']:
                        codes['vivareal_code'] = match.group(1).strip()
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Erro ao extrair códigos: {e}")
    return codes


def extract_images_with_network_interception(driver: WebDriver, max_images: int = 15) -> List[str]:
    """
    Estratégia 1: Intercepta requisições de rede para capturar URLs de imagens.
    Mais confiável para imagens carregadas dinamicamente via JavaScript.
    """
    images = []
    seen_urls = set()
    
    try:
        # Habilita logging de performance para capturar requisições de rede
        # Tenta habilitar, mas ignora erro se já estiver habilitado
        try:
            driver.execute_cdp_cmd('Performance.enable', {})
            driver.execute_cdp_cmd('Network.enable', {})
        except Exception:
            # Já pode estar habilitado, continua
            pass
        
        # Rola a página para disparar lazy loading de imagens
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(2)
        
        # Coleta logs de performance
        # IMPORTANTE: get_log retorna TODOS os logs acumulados desde que foi habilitado
        # Para processamento de múltiplas URLs, precisamos pegar apenas logs recentes
        # Vamos pegar apenas os últimos logs (mais prováveis de serem da página atual)
        try:
            all_logs = driver.get_log('performance')
            # Pega apenas os últimos 200 logs (suficiente para uma página, evita logs antigos)
            logs = all_logs[-200:] if len(all_logs) > 200 else all_logs
        except Exception as e:
            logger.debug(f"Erro ao obter logs de performance: {e}")
            logs = []
        
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                # Intercepta respostas de rede
                if method == 'Network.responseReceived':
                    response = message.get('message', {}).get('params', {}).get('response', {})
                    url = response.get('url', '')
                    mime_type = response.get('mimeType', '')
                    
                    # Verifica se é uma imagem
                    if mime_type.startswith('image/'):
                        url_lower = url.lower()
                        
                        # Filtra apenas imagens do Viva Real relacionadas ao imóvel
                        if any(domain in url_lower for domain in ['resizedimgs.vivareal.com', 'vivareal.com.br/img']):
                            # Exclui logos, banners, etc
                            exclude_keywords = ['logo', 'banner', 'icon', 'avatar', 'profile', 'corretor', 'agent', 
                                              'mota-fonseca', 'thumbnail', 'placeholder']
                            if not any(keyword in url_lower for keyword in exclude_keywords):
                                # Verifica se parece ser imagem do imóvel
                                if 'vr-listing' in url_lower or '/img/vr-listing/' in url_lower:
                                    if url not in seen_urls:
                                        images.append(url)
                                        seen_urls.add(url)
                                        if len(images) >= max_images:
                                            break
            except (KeyError, json.JSONDecodeError, ValueError):
                continue
        
        logger.info(f"Interceptação de rede encontrou {len(images)} imagens")
        
    except Exception as e:
        logger.warning(f"Erro na interceptação de rede: {e}")
    
    return images[:max_images]


def extract_images_with_page_interaction(driver: WebDriver, max_images: int = 15) -> List[str]:
    """
    Estratégia 2: Interage com a página para carregar imagens dinamicamente.
    Rola a página, clica em botões, aguarda lazy loading.
    """
    images = []
    seen_urls = set()
    
    try:
        # Rola gradualmente para disparar lazy loading
        try:
            page_height = driver.execute_script("return document.body.scrollHeight") or 1000
        except:
            page_height = 1000
        
        scroll_parts = 5
        
        for i in range(scroll_parts):
            try:
                scroll_position = (i + 1) * (page_height / scroll_parts)
                driver.execute_script(f"window.scrollTo(0, {scroll_position})")
                time.sleep(1.5)  # Aguarda carregamento
            except Exception:
                continue
        
        # Tenta clicar em botões de "Ver mais fotos" se existirem
        try:
            more_photos_selectors = [
                "button[aria-label*='mais fotos' i]",
                "button[aria-label*='ver mais' i]",
                "a[aria-label*='mais fotos' i]",
                "button:contains('Ver mais fotos')",
                "[class*='more-photos']",
                "[class*='ver-mais']",
            ]
            for selector in more_photos_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        elements[0].click()
                        time.sleep(3)
                        break
                except:
                    continue
        except:
            pass
        
        # Aguarda um pouco mais para garantir carregamento
        time.sleep(2)
        
        # Agora busca imagens no DOM
        image_selectors = [
            "img[src*='resizedimgs.vivareal.com']",
            "img[data-src*='resizedimgs.vivareal.com']",
            "img[src*='vivareal.com.br/img']",
            "[class*='gallery'] img",
            "[class*='photo'] img",
        ]
        
        for selector in image_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if len(images) >= max_images:
                        break
                    
                    # Pega URL da imagem
                    img_url = (element.get_attribute('src') or 
                              element.get_attribute('data-src') or
                              element.get_attribute('data-lazy-src'))
                    
                    if img_url and img_url not in seen_urls:
                        img_url_lower = img_url.lower()
                        # Filtra apenas imagens do imóvel
                        if 'vr-listing' in img_url_lower or '/img/vr-listing/' in img_url_lower:
                            exclude_keywords = ['logo', 'banner', 'icon', 'avatar', 'profile']
                            if not any(keyword in img_url_lower for keyword in exclude_keywords):
                                images.append(img_url)
                                seen_urls.add(img_url)
                                
            except Exception:
                continue
        
        logger.info(f"Interação com página encontrou {len(images)} imagens")
        
    except Exception as e:
        logger.warning(f"Erro na interação com página: {e}")
    
    return images[:max_images]


def extract_images_from_scripts(page_source: str, max_images: int = 15) -> List[str]:
    """
    Estratégia 3: Busca URLs de imagens em scripts JavaScript e JSON-LD.
    """
    images = []
    seen_urls = set()
    
    try:
        soup = BeautifulSoup(page_source, 'lxml')
        
        # Busca em scripts JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                # Busca recursivamente por URLs de imagens
                def find_images_in_dict(obj, depth=0):
                    if depth > 10:  # Limita profundidade
                        return
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if 'image' in key.lower() and isinstance(value, str):
                                if 'vivareal.com' in value.lower() and 'vr-listing' in value.lower():
                                    if value not in seen_urls:
                                        images.append(value)
                                        seen_urls.add(value)
                            else:
                                find_images_in_dict(value, depth + 1)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_images_in_dict(item, depth + 1)
                
                find_images_in_dict(data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Busca em scripts inline que podem conter dados de imagens
        all_scripts = soup.find_all('script')
        image_url_pattern = r'https?://[^"\'\s]*resizedimgs\.vivareal\.com[^"\'\s]*vr-listing[^"\'\s]*\.(?:jpg|jpeg|png|webp)'
        
        for script in all_scripts:
            if script.string:
                matches = re.findall(image_url_pattern, script.string, re.IGNORECASE)
                for match in matches:
                    # Remove parâmetros de query se houver
                    clean_url = match.split('?')[0] if '?' in match else match
                    if clean_url not in seen_urls:
                        images.append(clean_url)
                        seen_urls.add(clean_url)
                        if len(images) >= max_images:
                            break
        
        logger.info(f"Busca em scripts encontrou {len(images)} imagens")
        
    except Exception as e:
        logger.warning(f"Erro ao buscar imagens em scripts: {e}")
    
    return images[:max_images]


def extract_images(driver: WebDriver, page_source: str, max_images: int = 15, use_ai: bool = True) -> List[str]:
    """
    Extrai URLs das imagens do imóvel usando múltiplas estratégias em sequência.
    Filtra apenas fotos reais do imóvel, excluindo logos, banners, avatares, etc.
    """
    images = []
    seen_urls = set()
    
    # Estratégia 1: Interceptação de rede (mais confiável)
    logger.info("Tentando extrair imagens via interceptação de rede...")
    network_images = extract_images_with_network_interception(driver, max_images)
    for img in network_images:
        if img not in seen_urls:
            images.append(img)
            seen_urls.add(img)
    
    # Estratégia 2: Se não encontrou suficiente, interage com página
    if len(images) < 3:
        logger.info("Poucas imagens encontradas, tentando interação com página...")
        interaction_images = extract_images_with_page_interaction(driver, max_images)
        for img in interaction_images:
            if img not in seen_urls:
                images.append(img)
                seen_urls.add(img)
    
    # Estratégia 3: Se ainda não encontrou suficiente, busca em scripts
    if len(images) < 3:
        logger.info("Poucas imagens encontradas, buscando em scripts JavaScript/JSON...")
        script_images = extract_images_from_scripts(page_source, max_images)
        for img in script_images:
            if img not in seen_urls:
                images.append(img)
                seen_urls.add(img)
    
    # Estratégia 4: Se ainda vazio, usa IA como último recurso
    if len(images) < 1 and use_ai:
        try:
            logger.info("Tentando usar IA para encontrar imagens...")
            from src.ai_helper import extract_images_with_ai
            current_url = driver.current_url
            html_snippet = page_source[:30000]  # Limita tamanho para economizar tokens
            ai_images = extract_images_with_ai(html_snippet, current_url)
            for ai_img in ai_images:
                if ai_img not in seen_urls and len(images) < max_images:
                    images.append(ai_img)
                    seen_urls.add(ai_img)
            if ai_images:
                logger.info(f"IA encontrou {len(ai_images)} imagens adicionais")
        except Exception as e:
            logger.debug(f"Erro ao usar IA para imagens: {e}")
    
    logger.info(f"Total de {len(images)} imagens válidas extraídas")
    return images[:max_images]

