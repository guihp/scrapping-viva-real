"""Helper para usar API do ChatGPT para melhorar extração de dados."""
import logging
import json
import re
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI não disponível. Funcionalidades de IA desabilitadas.")

# Configuração da API - usa variável de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def extract_images_with_ai(html_snippet: str, page_url: str) -> List[str]:
    """
    Estratégia 4: Usa IA para identificar URLs de imagens de imóveis no HTML.
    Analisa HTML completo procurando padrões de URLs de imagens do Viva Real.
    """
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        logger.warning("OpenAI não disponível ou chave de API não configurada")
        return []
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Extrai todas as URLs de imagens do HTML primeiro usando regex mais abrangente
        img_urls_pattern = r'https?://[^"\'\s<>]*resizedimgs\.vivareal\.com[^"\'\s<>]*\.(?:jpg|jpeg|png|webp)'
        data_src_pattern = r'data-src=["\']([^"\']*resizedimgs\.vivareal\.com[^"\']*\.(?:jpg|jpeg|png|webp))["\']'
        src_pattern = r'src=["\']([^"\']*resizedimgs\.vivareal\.com[^"\']*\.(?:jpg|jpeg|png|webp))["\']'
        
        all_urls = re.findall(img_urls_pattern, html_snippet, re.IGNORECASE)
        all_urls.extend(re.findall(data_src_pattern, html_snippet, re.IGNORECASE))
        all_urls.extend(re.findall(src_pattern, html_snippet, re.IGNORECASE))
        
        # Remove duplicatas e limpa URLs
        vivareal_urls = []
        seen = set()
        for url in all_urls:
            # Remove parâmetros de query para normalizar
            clean_url = url.split('?')[0] if '?' in url else url
            if clean_url not in seen and 'vr-listing' in clean_url.lower():
                vivareal_urls.append(clean_url)
                seen.add(clean_url)
        
        if not vivareal_urls:
            # Tenta buscar padrões mais gerais
            general_pattern = r'https?://[^"\'\s<>]*vivareal[^"\'\s<>]*\.(?:jpg|jpeg|png|webp)'
            all_general = re.findall(general_pattern, html_snippet, re.IGNORECASE)
            for url in all_general:
                clean_url = url.split('?')[0] if '?' in url else url
                if clean_url not in seen and ('vr-listing' in clean_url.lower() or '/img/' in clean_url.lower()):
                    vivareal_urls.append(clean_url)
                    seen.add(clean_url)
        
        if not vivareal_urls:
            return []
        
        # Limita a 30 URLs para não usar muitos tokens
        vivareal_urls = vivareal_urls[:30]
        
        # Cria lista de URLs para análise
        urls_text = "\n".join([f"- {url}" for url in vivareal_urls[:25]])
        
        prompt = f"""Analise estas URLs de imagens de uma página de imóvel do Viva Real e retorne APENAS as URLs que são FOTOS REAIS DO IMÓVEL.

URLs encontradas:
{urls_text}

EXCLUA URLs que contenham:
- logo, banner, avatar, icon, thumbnail-small, placeholder
- profile, user, agent, corretor
- header, footer, nav, menu, button, badge

INCLUA APENAS URLs que sejam:
- Fotos do imóvel (interior/exterior)
- Da galeria de fotos
- Com boa resolução

Retorne APENAS um JSON array com as URLs válidas:
["url1", "url2"]
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo mais barato
            messages=[
                {"role": "system", "content": "Você é um especialista em web scraping. Retorne apenas JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content.strip()
        
        # Tenta parsear o JSON
        # Remove markdown code blocks se houver
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        if result.endswith("```"):
            result = result.rsplit("```", 1)[0].strip()
        
        images = json.loads(result)
        if isinstance(images, list):
            # Filtra apenas URLs válidas e adiciona protocolo se necessário
            valid_images = []
            for img in images:
                if isinstance(img, str) and img.startswith('http'):
                    valid_images.append(img)
                elif isinstance(img, str) and img.startswith('//'):
                    valid_images.append('https:' + img)
            logger.info(f"IA encontrou {len(valid_images)} imagens válidas")
            return valid_images[:15]  # Limita a 15
        
    except json.JSONDecodeError as e:
        logger.warning(f"Erro ao parsear resposta da IA: {e}")
        logger.debug(f"Resposta recebida: {result[:200] if 'result' in locals() else 'N/A'}")
    except Exception as e:
        logger.warning(f"Erro ao usar IA para extrair imagens: {e}")
    
    return []


def extract_location_with_ai(html_snippet: str, page_url: str) -> Dict[str, Optional[str]]:
    """
    Usa IA para extrair informações de localização mais precisas.
    Retorna dicionário com localização.
    """
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        return {}
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""Analise este HTML de uma página de imóvel do Viva Real e extraia informações de localização precisas.

URL da página: {page_url}

HTML:
{html_snippet[:8000]}

Extraia:
- Cidade (nome completo, ex: "São Luís" não apenas "São")
- Bairro
- Rua/Avenida (endereço completo)
- Número
- CEP (se disponível)
- Link do Google Maps ou coordenadas (se disponível)

Retorne APENAS um JSON com esta estrutura:
{{
  "city": "nome da cidade completo",
  "neighborhood": "nome do bairro",
  "street": "nome da rua/avenida",
  "number": "número",
  "zipcode": "CEP ou null",
  "map_link": "URL do Google Maps válida ou null"
}}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um especialista em extração de dados. Retorne apenas JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        
        # Remove markdown se houver
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        if result.endswith("```"):
            result = result.rsplit("```", 1)[0].strip()
        
        location = json.loads(result)
        if isinstance(location, dict):
            logger.info("IA extraiu localização com sucesso")
            # Garante que map_link seja do Google Maps se existir
            if location.get('map_link') and 'google.com/maps' not in location.get('map_link', ''):
                # Se não for Google Maps, pode tentar construir
                if location.get('street') and location.get('city'):
                    address_parts = []
                    if location.get('street'):
                        address_parts.append(location['street'])
                    if location.get('number'):
                        address_parts.append(location['number'])
                    if location.get('neighborhood'):
                        address_parts.append(location['neighborhood'])
                    if location.get('city'):
                        address_parts.append(location['city'])
                    if len(address_parts) >= 2:
                        full_address = ', '.join([part for part in address_parts if part])
                        location['map_link'] = f"https://www.google.com/maps/search/?api=1&query={full_address.replace(' ', '+')}"
            return location
        
    except json.JSONDecodeError as e:
        logger.warning(f"Erro ao parsear localização da IA: {e}")
    except Exception as e:
        logger.warning(f"Erro ao usar IA para extrair localização: {e}")
    
    return {}
