"""Funções para validar e limpar dados extraídos."""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def normalize_text(text: Optional[str]) -> Optional[str]:
    """Normaliza texto: remove espaços extras, normaliza encoding."""
    if not text:
        return None
    if not isinstance(text, str):
        text = str(text)
    text = ' '.join(text.split())
    text = text.strip()
    if not text:
        return None
    return text


def normalize_zipcode(zipcode: Optional[str]) -> Optional[str]:
    """Normaliza CEP para formato XXXXX-XXX."""
    if not zipcode:
        return None
    digits = re.sub(r'\D', '', str(zipcode))
    if len(digits) == 8:
        return f"{digits[:5]}-{digits[5:]}"
    elif len(digits) == 7:
        return f"{digits[:4]}-{digits[4:]}"
    return None


def validate_price(price: Any) -> Optional[float]:
    """Valida e normaliza preço."""
    if price is None:
        return None
    if isinstance(price, (int, float)):
        if price >= 0:
            return float(price)
        return None
    if isinstance(price, str):
        price_clean = re.sub(r'[^\d.,]', '', price)
        price_clean = price_clean.replace(',', '.')
        if price_clean.count('.') > 1:
            price_clean = price_clean.replace('.', '')
        try:
            price_float = float(price_clean)
            if price_float >= 0:
                return price_float
        except ValueError:
            pass
    return None


def validate_int_value(value: Any, min_val: int = 0, max_val: Optional[int] = None) -> Optional[int]:
    """Valida e normaliza valor inteiro."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        int_val = int(value)
        if int_val >= min_val:
            if max_val is None or int_val <= max_val:
                return int_val
        return None
    if isinstance(value, str):
        digits = re.sub(r'\D', '', value)
        if digits:
            try:
                int_val = int(digits)
                if int_val >= min_val:
                    if max_val is None or int_val <= max_val:
                        return int_val
            except ValueError:
                pass
    return None


def validate_url(url: Optional[str]) -> Optional[str]:
    """Valida URL."""
    if not url:
        return None
    if not isinstance(url, str):
        url = str(url)
    url = url.strip()
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if url_pattern.match(url):
        return url
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return 'https://www.vivareal.com.br' + url
    return None


def clean_location(location: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Limpa e valida dados de localização."""
    cleaned = {
        'city': normalize_text(location.get('city')),
        'neighborhood': normalize_text(location.get('neighborhood')),
        'street': normalize_text(location.get('street')),
        'number': normalize_text(location.get('number')),
        'zipcode': normalize_zipcode(location.get('zipcode')),
        'complement': normalize_text(location.get('complement')),
        'map_link': validate_url(location.get('map_link')),
    }
    return cleaned


def clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Limpa e valida todos os dados extraídos."""
    cleaned = {}
    cleaned['url'] = validate_url(data.get('url'))
    cleaned['scraped_at'] = data.get('scraped_at')
    cleaned['property_type'] = normalize_text(data.get('property_type'))
    cleaned['category'] = normalize_text(data.get('category')) if data.get('category') else None
    cleaned['modality'] = normalize_text(data.get('modality'))
    cleaned['price'] = validate_price(data.get('price'))
    cleaned['size_m2'] = validate_int_value(data.get('size_m2'), min_val=1)
    cleaned['bedrooms'] = validate_int_value(data.get('bedrooms'), min_val=0)
    cleaned['suites'] = validate_int_value(data.get('suites'), min_val=0)
    cleaned['bathrooms'] = validate_int_value(data.get('bathrooms'), min_val=0)
    cleaned['garage'] = validate_int_value(data.get('garage'), min_val=0)
    if 'location' in data and isinstance(data['location'], dict):
        cleaned['location'] = clean_location(data['location'])
    else:
        cleaned['location'] = {
            'city': None, 'neighborhood': None, 'street': None,
            'number': None, 'zipcode': None, 'complement': None, 'map_link': None,
        }
    cleaned['description'] = normalize_text(data.get('description'))
    
    # Códigos
    cleaned['advertiser_code'] = normalize_text(data.get('advertiser_code'))
    cleaned['vivareal_code'] = normalize_text(data.get('vivareal_code'))
    
    images = data.get('images', [])
    if isinstance(images, list):
        cleaned_images = []
        for img_url in images:
            validated_url = validate_url(img_url)
            if validated_url:
                cleaned_images.append(validated_url)
        cleaned['images'] = cleaned_images[:15]
    else:
        cleaned['images'] = []
    logger.info("Dados limpos e validados")
    return cleaned

