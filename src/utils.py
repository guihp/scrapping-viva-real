"""Funções auxiliares para o scraper."""
import time
import random
from typing import Dict

# User-Agents para rotação
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
]


def get_random_user_agent() -> str:
    """Retorna um User-Agent aleatório."""
    return random.choice(USER_AGENTS)


def get_headers() -> Dict[str, str]:
    """Retorna headers HTTP padrão para requisições."""
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def rate_limit(min_seconds: float = 2.0, max_seconds: float = 5.0):
    """
    Implementa rate limiting com delay aleatório.
    
    Args:
        min_seconds: Tempo mínimo de espera em segundos
        max_seconds: Tempo máximo de espera em segundos
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)



