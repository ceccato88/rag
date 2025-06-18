"""Testes para o módulo utils.cache."""
import pytest
import time
from unittest.mock import patch

from utils.cache import SimpleCache, CacheEntry, cached, cache_function, global_cache


class TestCacheEntry:
    """Testes para a classe CacheEntry."""
    
    def test_cache_entry_creation(self):
        """Testa criação de entrada de cache."""
        entry = CacheEntry(value="test", timestamp=time.time())
        assert entry.value == "test"
        assert entry.hits == 0
        assert isinstance(entry.timestamp, float)


class TestSimpleCache:
    """Testes para a classe SimpleCache."""
    
    def test_cache_initialization(self):
        """Testa inicialização do cache."""
        cache = SimpleCache(max_size=100, default_ttl=3600)
        assert cache.max_size == 100
        assert cache.default_ttl == 3600
        assert len(cache._cache) == 0
    
    def test_cache_set_and_get(self):
        """Testa operações básicas de set e get."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        assert result == "value1"
    
    def test_cache_miss(self):
        """Testa cache miss."""
        cache = SimpleCache()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_expiration(self):
        """Testa expiração de entradas do cache."""
        cache = SimpleCache(default_ttl=0.1)  # 100ms TTL
        cache.set("key1", "value1")
        
        # Imediatamente deve retornar o valor
        assert cache.get("key1") == "value1"
        
        # Após expiração deve retornar None
        time.sleep(0.2)
        assert cache.get("key1") is None
    
    def test_cache_eviction(self):
        """Testa remoção de entradas quando cache está cheio."""
        cache = SimpleCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache._cache) == 2
        
        # Adicionar terceira entrada deve remover a mais antiga
        time.sleep(0.01)  # Garantir timestamp diferente
        cache.set("key3", "value3")
        assert len(cache._cache) == 2
        assert cache.get("key1") is None  # Primeira foi removida
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_cache_clear(self):
        """Testa limpeza do cache."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        assert len(cache._cache) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_stats(self):
        """Testa estatísticas do cache."""
        cache = SimpleCache(max_size=10)
        cache.set("key1", "value1")
        cache.get("key1")  # 1 hit
        cache.get("key1")  # 2 hits
        
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["total_hits"] == 2
        assert stats["hit_rate"] == 2.0
    
    def test_create_key(self):
        """Testa criação de chaves únicas."""
        cache = SimpleCache()
        
        key1 = cache._create_key("arg1", "arg2", kwarg1="value1")
        key2 = cache._create_key("arg1", "arg2", kwarg1="value1")
        key3 = cache._create_key("arg1", "arg2", kwarg1="value2")
        
        assert key1 == key2  # Mesmos argumentos = mesma chave
        assert key1 != key3  # Argumentos diferentes = chaves diferentes


class TestCachedDecorator:
    """Testes para o decorator cached."""
    
    def test_cached_function(self):
        """Testa decorator cached."""
        cache = SimpleCache()
        call_count = 0
        
        @cached(cache)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Primeira chamada
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Segunda chamada (deve vir do cache)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Não deve ter chamado a função novamente
        
        # Chamada com argumento diferente
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2
    
    def test_cached_function_with_kwargs(self):
        """Testa decorator cached com kwargs."""
        cache = SimpleCache()
        call_count = 0
        
        @cached(cache)
        def function_with_kwargs(x, multiplier=2):
            nonlocal call_count
            call_count += 1
            return x * multiplier
        
        result1 = function_with_kwargs(5, multiplier=3)
        result2 = function_with_kwargs(5, multiplier=3)
        
        assert result1 == result2 == 15
        assert call_count == 1


class TestCacheFunctionDecorator:
    """Testes para o decorator cache_function."""
    
    def test_cache_function_simple(self):
        """Testa decorator cache_function simples."""
        call_count = 0
        
        @cache_function
        def simple_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = simple_function(5)
        result2 = simple_function(5)
        
        assert result1 == result2 == 10
        assert call_count == 1
    
    def test_cache_function_with_ttl(self):
        """Testa decorator cache_function com TTL customizado."""
        call_count = 0
        
        @cache_function(ttl=0.1)  # 100ms TTL
        def function_with_ttl(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = function_with_ttl(5)
        assert result1 == 10
        assert call_count == 1
        
        # Deve vir do cache
        result2 = function_with_ttl(5)
        assert result2 == 10
        assert call_count == 1
        
        # Após expiração deve executar novamente
        time.sleep(0.2)
        result3 = function_with_ttl(5)
        assert result3 == 10
        assert call_count == 2


class TestGlobalCache:
    """Testes para o cache global."""
    
    def test_global_cache_exists(self):
        """Testa se o cache global existe e funciona."""
        assert global_cache is not None
        assert isinstance(global_cache, SimpleCache)
        
        global_cache.set("test_key", "test_value")
        assert global_cache.get("test_key") == "test_value"
    
    def teardown_method(self):
        """Limpa cache global após cada teste."""
        global_cache.clear()


class TestIntegration:
    """Testes de integração do sistema de cache."""
    
    def test_multiple_cached_functions(self):
        """Testa múltiplas funções usando cache."""
        cache = SimpleCache()
        
        @cached(cache)
        def func1(x):
            return x + 1
        
        @cached(cache)
        def func2(x):
            return x * 2
        
        # Diferentes funções devem ter chaves diferentes
        result1 = func1(5)
        result2 = func2(5)
        
        assert result1 == 6
        assert result2 == 10
        
        # Verificar que ambas estão no cache
        stats = cache.stats()
        assert stats["size"] == 2
    
    def test_cache_memory_management(self):
        """Testa gestão de memória do cache."""
        cache = SimpleCache(max_size=3)
        
        # Preencher cache até o limite
        for i in range(3):
            cache.set(f"key{i}", f"value{i}")
        
        assert len(cache._cache) == 3
        
        # Adicionar mais uma entrada deve disparar eviction
        time.sleep(0.01)
        cache.set("key3", "value3")
        
        assert len(cache._cache) == 3
        assert cache.get("key0") is None  # Primeira entrada foi removida
