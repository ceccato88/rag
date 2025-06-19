"""Utilitário de cache para otimização de performance."""
import time
import hashlib
import json
import logging
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Entrada do cache com timestamp."""
    value: Any
    timestamp: float
    hits: int = 0

class SimpleCache:
    """Cache simples em memória com TTL (Time To Live)."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Inicializa o cache.
        
        Args:
            max_size: Tamanho máximo do cache
            default_ttl: TTL padrão em segundos (1 hora)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
    
    def _create_key(self, *args, **kwargs) -> str:
        """Cria chave única baseada nos argumentos."""
        key_data = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """Recupera valor do cache."""
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        # Verifica se expirou
        if time.time() - entry.timestamp > effective_ttl:
            del self._cache[key]
            logger.debug(f"Cache key '{key}' expirou")
            return None
        
        entry.hits += 1
        logger.debug(f"Cache hit para key '{key}' (hits: {entry.hits})")
        return entry.value
    
    def set(self, key: str, value: Any) -> None:
        """Armazena valor no cache."""
        # Remove entradas antigas se cache está cheio
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.time()
        )
        logger.debug(f"Cache set para key '{key}'")
    
    def _evict_oldest(self) -> None:
        """Remove entrada mais antiga do cache."""
        if not self._cache:
            return
            
        oldest_key = min(self._cache.keys(), 
                        key=lambda k: self._cache[k].timestamp)
        del self._cache[oldest_key]
        logger.debug(f"Cache evict: removido key '{oldest_key}'")
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache limpo: {count} entradas removidas")
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        total_hits = sum(entry.hits for entry in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
            "hit_rate": total_hits / max(1, len(self._cache))
        }

def cached(cache: SimpleCache, ttl: Optional[int] = None):
    """
    Decorator para cachear resultados de funções.
    
    Args:
        cache: Instância do cache a ser usado
        ttl: TTL específico para esta função (sobrescreve o padrão)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cria chave única para esta chamada
            key = f"{func.__name__}:{cache._create_key(*args, **kwargs)}"
            
            # Tenta recuperar do cache com TTL específico
            result = cache.get(key, ttl)
            if result is not None:
                return result
            
            # Executa função e armazena resultado
            logger.debug(f"Cache miss para função '{func.__name__}', executando...")
            result = func(*args, **kwargs)
            cache.set(key, result)
            
            return result
        
        # Adiciona método para limpar cache desta função
        wrapper.clear_cache = lambda: cache.clear()
        wrapper.cache_stats = lambda: cache.stats()
        
        return wrapper
    return decorator

# Cache global para uso simples
global_cache = SimpleCache()

def cache_function(func: Callable = None, *, ttl: int = 3600):
    """
    Decorator simples para cachear funções usando cache global.
    
    Uso:
        @cache_function
        def minha_funcao():
            pass
            
        @cache_function(ttl=1800)  # 30 minutos
        def outra_funcao():
            pass
    """
    if func is None:
        return lambda f: cached(global_cache, ttl)(f)
    return cached(global_cache, ttl)(func)
