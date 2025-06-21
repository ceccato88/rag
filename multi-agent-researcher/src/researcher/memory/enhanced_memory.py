"""
Enhanced Memory System with Distributed Storage, Semantic Search, and Intelligent Caching
"""

import asyncio
import hashlib
import json
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from researcher.memory.base import Memory, MemoryEntry, ResearchMemory
from researcher.utils.multiagent_logger import get_multiagent_logger


class StorageBackend(Enum):
    """Tipos de backend de armazenamento"""
    IN_MEMORY = "in_memory"
    REDIS = "redis"
    POSTGRES = "postgres"
    HYBRID = "hybrid"


class IndexType(Enum):
    """Tipos de índices disponíveis"""
    HASH = "hash"
    BTREE = "btree"
    SEMANTIC = "semantic"
    FULLTEXT = "fulltext"
    METADATA = "metadata"


@dataclass
class CachePolicy:
    """Política de cache para diferentes tipos de dados"""
    ttl: int = 3600  # Time to live em segundos
    max_size: int = 1000  # Máximo de entradas
    eviction_policy: str = "lru"  # lru, lfu, ttl
    compression: bool = False
    encryption: bool = False


@dataclass
class SearchQuery:
    """Query estruturada para busca na memória"""
    text: Optional[str] = None
    semantic_query: Optional[str] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[Tuple[datetime, datetime]] = None
    agent_ids: Optional[List[str]] = None
    data_types: Optional[List[str]] = None
    similarity_threshold: float = 0.7
    max_results: int = 10


@dataclass
class SearchResult:
    """Resultado de busca estruturado"""
    entries: List[MemoryEntry]
    total_found: int
    search_time: float
    used_indexes: List[str]
    relevance_scores: Optional[List[float]] = None


class MultiIndex:
    """Sistema de múltiplos índices para diferentes tipos de busca"""
    
    def __init__(self):
        self.indexes: Dict[IndexType, Any] = {}
        self._initialize_indexes()
    
    def _initialize_indexes(self):
        """Inicializa diferentes tipos de índices"""
        # Hash index para busca exata por chave
        self.indexes[IndexType.HASH] = {}
        
        # BTree index para range queries temporais
        self.indexes[IndexType.BTREE] = {}
        
        # Metadata index invertido
        self.indexes[IndexType.METADATA] = {}
        
        # Full-text index para busca textual
        self.indexes[IndexType.FULLTEXT] = {}
        
        # Semantic index para busca semântica (simulado)
        self.indexes[IndexType.SEMANTIC] = {}
    
    async def add_entry(self, entry: MemoryEntry):
        """Adiciona entrada a todos os índices relevantes"""
        # Hash index
        self.indexes[IndexType.HASH][entry.key] = entry
        
        # BTree index (por timestamp)
        timestamp_key = entry.timestamp.isoformat()
        if timestamp_key not in self.indexes[IndexType.BTREE]:
            self.indexes[IndexType.BTREE][timestamp_key] = []
        self.indexes[IndexType.BTREE][timestamp_key].append(entry)
        
        # Metadata index
        for meta_key, meta_value in entry.metadata.items():
            meta_index_key = f"{meta_key}:{meta_value}"
            if meta_index_key not in self.indexes[IndexType.METADATA]:
                self.indexes[IndexType.METADATA][meta_index_key] = []
            self.indexes[IndexType.METADATA][meta_index_key].append(entry)
        
        # Full-text index (simulado com palavras-chave)
        if hasattr(entry.value, 'lower') or isinstance(entry.value, str):
            text_content = str(entry.value).lower()
            words = text_content.split()
            for word in words:
                if len(word) > 3:  # Apenas palavras significativas
                    if word not in self.indexes[IndexType.FULLTEXT]:
                        self.indexes[IndexType.FULLTEXT][word] = []
                    self.indexes[IndexType.FULLTEXT][word].append(entry)
        
        # Semantic index (simulado - em produção usaria embeddings)
        if isinstance(entry.value, str) and len(entry.value) > 10:
            semantic_key = self._generate_semantic_key(entry.value)
            if semantic_key not in self.indexes[IndexType.SEMANTIC]:
                self.indexes[IndexType.SEMANTIC][semantic_key] = []
            self.indexes[IndexType.SEMANTIC][semantic_key].append(entry)
    
    def _generate_semantic_key(self, text: str) -> str:
        """Gera chave semântica simplificada (em produção usaria embeddings)"""
        # Simulação de embedding usando hash de palavras-chave importantes
        words = text.lower().split()
        important_words = [w for w in words if len(w) > 4][:5]
        return hashlib.md5(" ".join(sorted(important_words)).encode()).hexdigest()[:8]
    
    async def search(self, query: SearchQuery) -> List[MemoryEntry]:
        """Busca usando múltiplos índices"""
        results = []
        
        # Busca textual
        if query.text:
            text_results = await self._search_fulltext(query.text)
            results.extend(text_results)
        
        # Busca semântica
        if query.semantic_query:
            semantic_results = await self._search_semantic(query.semantic_query)
            results.extend(semantic_results)
        
        # Filtros de metadata
        if query.metadata_filters:
            metadata_results = await self._search_metadata(query.metadata_filters)
            results.extend(metadata_results)
        
        # Filtro temporal
        if query.time_range:
            results = self._filter_by_time_range(results, query.time_range)
        
        # Filtro por agent_ids
        if query.agent_ids:
            results = [entry for entry in results if entry.agent_id in query.agent_ids]
        
        # Remover duplicatas mantendo ordem de relevância
        seen_keys = set()
        unique_results = []
        for entry in results:
            if entry.key not in seen_keys:
                seen_keys.add(entry.key)
                unique_results.append(entry)
        
        return unique_results[:query.max_results]
    
    async def _search_fulltext(self, query: str) -> List[MemoryEntry]:
        """Busca full-text usando índice invertido"""
        words = query.lower().split()
        candidate_entries = set()
        
        for word in words:
            if word in self.indexes[IndexType.FULLTEXT]:
                candidate_entries.update(self.indexes[IndexType.FULLTEXT][word])
        
        return list(candidate_entries)
    
    async def _search_semantic(self, query: str) -> List[MemoryEntry]:
        """Busca semântica (simulada)"""
        semantic_key = self._generate_semantic_key(query)
        
        # Em produção, aqui calcularia similaridade de embeddings
        if semantic_key in self.indexes[IndexType.SEMANTIC]:
            return self.indexes[IndexType.SEMANTIC][semantic_key]
        
        return []
    
    async def _search_metadata(self, filters: Dict[str, Any]) -> List[MemoryEntry]:
        """Busca por filtros de metadata"""
        results = []
        
        for key, value in filters.items():
            meta_key = f"{key}:{value}"
            if meta_key in self.indexes[IndexType.METADATA]:
                results.extend(self.indexes[IndexType.METADATA][meta_key])
        
        return results
    
    def _filter_by_time_range(self, entries: List[MemoryEntry], 
                             time_range: Tuple[datetime, datetime]) -> List[MemoryEntry]:
        """Filtra entradas por range temporal"""
        start_time, end_time = time_range
        return [
            entry for entry in entries 
            if start_time <= entry.timestamp <= end_time
        ]


class HierarchicalCache:
    """Cache hierárquico com múltiplas camadas"""
    
    def __init__(self):
        # L1: Cache em memória (mais rápido)
        self.l1_cache: Dict[str, Any] = {}
        self.l1_access_times: Dict[str, float] = {}
        self.l1_max_size = 1000
        
        # L2: Cache com TTL (médio)
        self.l2_cache: Dict[str, Tuple[Any, float]] = {}  # (value, expiry_time)
        self.l2_max_size = 5000
        
        # Estatísticas
        self.cache_hits = {"l1": 0, "l2": 0}
        self.cache_misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache hierárquico"""
        # Tentar L1 primeiro
        if key in self.l1_cache:
            self.l1_access_times[key] = time.time()
            self.cache_hits["l1"] += 1
            return self.l1_cache[key]
        
        # Tentar L2
        if key in self.l2_cache:
            value, expiry_time = self.l2_cache[key]
            
            if time.time() < expiry_time:
                # Promover para L1
                await self._promote_to_l1(key, value)
                self.cache_hits["l2"] += 1
                return value
            else:
                # Expirado, remover do L2
                del self.l2_cache[key]
        
        self.cache_misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Armazena valor no cache"""
        # Armazenar em L1
        await self._promote_to_l1(key, value)
        
        # Armazenar em L2 com TTL
        expiry_time = time.time() + ttl
        self.l2_cache[key] = (value, expiry_time)
        
        # Gerenciar tamanho do L2
        if len(self.l2_cache) > self.l2_max_size:
            await self._evict_l2()
    
    async def _promote_to_l1(self, key: str, value: Any):
        """Promove item para L1 cache"""
        # Verificar limite de tamanho
        if len(self.l1_cache) >= self.l1_max_size:
            await self._evict_l1()
        
        self.l1_cache[key] = value
        self.l1_access_times[key] = time.time()
    
    async def _evict_l1(self):
        """Remove item menos recentemente usado do L1"""
        if not self.l1_access_times:
            return
        
        # Encontrar item com access_time mais antigo
        oldest_key = min(self.l1_access_times.keys(), 
                        key=lambda k: self.l1_access_times[k])
        
        del self.l1_cache[oldest_key]
        del self.l1_access_times[oldest_key]
    
    async def _evict_l2(self):
        """Remove itens expirados do L2"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self.l2_cache.items()
            if current_time >= expiry_time
        ]
        
        for key in expired_keys:
            del self.l2_cache[key]
        
        # Se ainda estiver acima do limite, remover mais antigos
        if len(self.l2_cache) > self.l2_max_size:
            sorted_items = sorted(
                self.l2_cache.items(),
                key=lambda x: x[1][1]  # Sort by expiry_time
            )
            
            # Remover 20% dos mais antigos
            remove_count = len(sorted_items) // 5
            for key, _ in sorted_items[:remove_count]:
                del self.l2_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = sum(self.cache_hits.values()) + self.cache_misses
        hit_rate = sum(self.cache_hits.values()) / total_requests if total_requests > 0 else 0.0
        
        return {
            "l1_size": len(self.l1_cache),
            "l2_size": len(self.l2_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "l1_hit_rate": self.cache_hits["l1"] / total_requests if total_requests > 0 else 0.0,
            "l2_hit_rate": self.cache_hits["l2"] / total_requests if total_requests > 0 else 0.0
        }


class DistributedMemoryStorage(Memory[Any]):
    """Sistema de memória distribuída com sharding inteligente"""
    
    def __init__(self, storage_backend: StorageBackend = StorageBackend.IN_MEMORY):
        self.storage_backend = storage_backend
        self.local_storage: Dict[str, MemoryEntry] = {}
        self.multi_index = MultiIndex()
        self.cache = HierarchicalCache()
        
        # Configurações de sharding
        self.num_shards = 4
        self.shard_strategy = "agent_hash"  # agent_hash, time_hash, content_hash
        
        # Métricas
        self.operation_count = 0
        self.total_operation_time = 0.0
    
    def _compute_shard(self, key: str, agent_id: Optional[str] = None) -> int:
        """Computa shard baseado na estratégia configurada"""
        if self.shard_strategy == "agent_hash" and agent_id:
            return hash(agent_id) % self.num_shards
        elif self.shard_strategy == "time_hash":
            return int(time.time()) % self.num_shards
        else:  # content_hash
            return hash(key) % self.num_shards
    
    async def store(self, key: str, value: Any, agent_id: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Armazena valor com distribuição automática"""
        start_time = time.time()
        
        try:
            # Criar entry
            entry = MemoryEntry(
                key=key,
                value=value,
                timestamp=datetime.utcnow(),
                agent_id=agent_id,
                metadata=metadata or {}
            )
            
            # Determinar shard
            shard_id = self._compute_shard(key, agent_id)
            sharded_key = f"shard_{shard_id}:{key}"
            
            # Armazenar localmente
            self.local_storage[sharded_key] = entry
            
            # Adicionar aos índices
            await self.multi_index.add_entry(entry)
            
            # Adicionar ao cache
            await self.cache.set(key, entry)
            
        finally:
            self._record_operation_time(time.time() - start_time)
    
    async def retrieve(self, key: str, agent_id: Optional[str] = None) -> Optional[Any]:
        """Recupera valor com busca otimizada"""
        start_time = time.time()
        
        try:
            # Tentar cache primeiro
            cached_entry = await self.cache.get(key)
            if cached_entry:
                return cached_entry.value if hasattr(cached_entry, 'value') else cached_entry
            
            # Buscar em todas as shards se necessário
            for shard_id in range(self.num_shards):
                sharded_key = f"shard_{shard_id}:{key}"
                if sharded_key in self.local_storage:
                    entry = self.local_storage[sharded_key]
                    
                    # Atualizar cache
                    await self.cache.set(key, entry)
                    
                    return entry.value
            
            return None
            
        finally:
            self._record_operation_time(time.time() - start_time)
    
    async def delete(self, key: str, agent_id: Optional[str] = None) -> bool:
        """Remove valor de todas as shards"""
        start_time = time.time()
        deleted = False
        
        try:
            for shard_id in range(self.num_shards):
                sharded_key = f"shard_{shard_id}:{key}"
                if sharded_key in self.local_storage:
                    del self.local_storage[sharded_key]
                    deleted = True
            
            return deleted
            
        finally:
            self._record_operation_time(time.time() - start_time)
    
    async def search(self, query: SearchQuery) -> SearchResult:
        """Busca avançada usando múltiplos índices"""
        start_time = time.time()
        
        try:
            # Usar multi-index para busca
            entries = await self.multi_index.search(query)
            
            search_time = time.time() - start_time
            
            return SearchResult(
                entries=entries,
                total_found=len(entries),
                search_time=search_time,
                used_indexes=["multi_index"]
            )
            
        finally:
            self._record_operation_time(time.time() - start_time)
    
    async def list_keys(self, prefix: Optional[str] = None, 
                       agent_id: Optional[str] = None) -> List[str]:
        """Lista chaves com filtros opcionais"""
        keys = []
        
        for sharded_key, entry in self.local_storage.items():
            # Extrair chave original
            original_key = sharded_key.split(":", 1)[1] if ":" in sharded_key else sharded_key
            
            # Aplicar filtros
            if prefix and not original_key.startswith(prefix):
                continue
            
            if agent_id and entry.agent_id != agent_id:
                continue
            
            keys.append(original_key)
        
        return keys
    
    async def clear(self, agent_id: Optional[str] = None) -> None:
        """Limpa armazenamento com filtro opcional"""
        if agent_id:
            # Remover apenas entradas do agente específico
            keys_to_remove = []
            for sharded_key, entry in self.local_storage.items():
                if entry.agent_id == agent_id:
                    keys_to_remove.append(sharded_key)
            
            for key in keys_to_remove:
                del self.local_storage[key]
        else:
            # Limpar tudo
            self.local_storage.clear()
            self.multi_index = MultiIndex()  # Recrear índices
    
    def _record_operation_time(self, operation_time: float):
        """Registra métricas de operação"""
        self.operation_count += 1
        self.total_operation_time += operation_time
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance"""
        avg_operation_time = (
            self.total_operation_time / self.operation_count 
            if self.operation_count > 0 else 0.0
        )
        
        return {
            "operation_count": self.operation_count,
            "average_operation_time": avg_operation_time,
            "total_entries": len(self.local_storage),
            "cache_stats": self.cache.get_stats(),
            "storage_backend": self.storage_backend.value,
            "num_shards": self.num_shards
        }


class EnhancedResearchMemory(ResearchMemory):
    """Sistema de memória enhanced para pesquisa com recursos avançados"""
    
    def __init__(self, storage: Optional[DistributedMemoryStorage] = None):
        if storage is None:
            storage = DistributedMemoryStorage()
        
        super().__init__(storage)
        self.enhanced_storage = storage
        
        # Sistemas especializados
        self.checkpoint_manager = CheckpointManager(storage)
        self.pattern_learner = MemoryPatternLearner(storage)
        self.access_optimizer = AccessPatternOptimizer()
    
    async def store_reasoning_step(self, agent_id: str, step_data: Dict[str, Any], 
                                 session_id: str) -> str:
        """Armazena step de reasoning com indexação especializada"""
        step_key = f"reasoning:{session_id}:{len(step_data.get('history', []))}"
        
        await self.enhanced_storage.store(
            key=step_key,
            value=step_data,
            agent_id=agent_id,
            metadata={
                "type": "reasoning_step",
                "session_id": session_id,
                "step_type": step_data.get("step_type"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return step_key
    
    async def search_similar_reasoning(self, query: str, agent_id: str, 
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """Busca reasoning patterns similares"""
        search_query = SearchQuery(
            semantic_query=query,
            metadata_filters={"type": "reasoning_step"},
            agent_ids=[agent_id],
            max_results=limit
        )
        
        result = await self.enhanced_storage.search(search_query)
        return [entry.value for entry in result.entries]
    
    async def create_agent_checkpoint(self, agent_id: str) -> str:
        """Cria checkpoint completo do estado de um agente"""
        return await self.checkpoint_manager.create_checkpoint(agent_id)
    
    async def restore_agent_from_checkpoint(self, agent_id: str, checkpoint_id: str) -> bool:
        """Restaura agente a partir de checkpoint"""
        return await self.checkpoint_manager.restore_checkpoint(agent_id, checkpoint_id)
    
    async def learn_from_session(self, session_id: str, success_metrics: Dict[str, float]):
        """Aprende padrões a partir de uma sessão bem-sucedida"""
        await self.pattern_learner.learn_from_session(session_id, success_metrics)
    
    async def suggest_next_action(self, agent_id: str, current_context: str) -> Optional[str]:
        """Sugere próxima ação baseada em padrões aprendidos"""
        return await self.pattern_learner.suggest_next_action(agent_id, current_context)


class CheckpointManager:
    """Gerenciador de checkpoints incrementais"""
    
    def __init__(self, storage: DistributedMemoryStorage):
        self.storage = storage
    
    async def create_checkpoint(self, agent_id: str) -> str:
        """Cria checkpoint incremental do estado do agente"""
        checkpoint_id = f"checkpoint:{agent_id}:{int(time.time())}"
        
        # Obter último checkpoint
        last_checkpoint = await self._get_latest_checkpoint(agent_id)
        last_checkpoint_time = (
            datetime.fromisoformat(last_checkpoint["timestamp"]) 
            if last_checkpoint else datetime.min
        )
        
        # Buscar apenas dados modificados desde último checkpoint
        search_query = SearchQuery(
            agent_ids=[agent_id],
            time_range=(last_checkpoint_time, datetime.utcnow()),
            max_results=1000
        )
        
        result = await self.storage.search(search_query)
        
        # Criar checkpoint incremental
        checkpoint_data = {
            "type": "incremental_checkpoint",
            "agent_id": agent_id,
            "base_checkpoint": last_checkpoint["checkpoint_id"] if last_checkpoint else None,
            "changes": [entry.dict() for entry in result.entries],
            "timestamp": datetime.utcnow().isoformat(),
            "change_count": len(result.entries)
        }
        
        await self.storage.store(
            key=checkpoint_id,
            value=checkpoint_data,
            agent_id=agent_id,
            metadata={"type": "checkpoint", "checkpoint_type": "incremental"}
        )
        
        return checkpoint_id
    
    async def _get_latest_checkpoint(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Recupera último checkpoint do agente"""
        search_query = SearchQuery(
            agent_ids=[agent_id],
            metadata_filters={"type": "checkpoint"},
            max_results=1
        )
        
        result = await self.storage.search(search_query)
        
        if result.entries:
            return result.entries[0].value
        
        return None
    
    async def restore_checkpoint(self, agent_id: str, checkpoint_id: str) -> bool:
        """Restaura estado a partir de checkpoint"""
        try:
            checkpoint_data = await self.storage.retrieve(checkpoint_id, agent_id)
            
            if not checkpoint_data:
                return False
            
            # Se for checkpoint incremental, reconstruir chain
            if checkpoint_data["type"] == "incremental_checkpoint":
                await self._restore_incremental_chain(agent_id, checkpoint_data)
            else:
                await self._restore_full_checkpoint(agent_id, checkpoint_data)
            
            return True
            
        except Exception as e:
            logger = get_multiagent_logger()
            logger.error(f"Erro ao restaurar checkpoint {checkpoint_id}: {e}")
            return False
    
    async def _restore_incremental_chain(self, agent_id: str, checkpoint_data: Dict[str, Any]):
        """Restaura chain de checkpoints incrementais"""
        # Implementação para reconstruir estado a partir de chain de checkpoints
        pass
    
    async def _restore_full_checkpoint(self, agent_id: str, checkpoint_data: Dict[str, Any]):
        """Restaura checkpoint completo"""
        # Implementação para restaurar checkpoint completo
        pass


class MemoryPatternLearner:
    """Sistema de aprendizado de padrões de uso da memória"""
    
    def __init__(self, storage: DistributedMemoryStorage):
        self.storage = storage
        self.learned_patterns: Dict[str, List[Dict]] = {}
    
    async def learn_from_session(self, session_id: str, success_metrics: Dict[str, float]):
        """Aprende padrões de uma sessão bem-sucedida"""
        # Buscar todos os dados da sessão
        search_query = SearchQuery(
            metadata_filters={"session_id": session_id},
            max_results=1000
        )
        
        result = await self.storage.search(search_query)
        
        if result.entries and success_metrics.get("overall_success", 0) > 0.7:
            # Extrair padrão de acesso
            access_pattern = self._extract_access_pattern(result.entries)
            
            # Armazenar padrão aprendido
            pattern_key = f"learned_pattern:{session_id}"
            pattern_data = {
                "access_pattern": access_pattern,
                "success_metrics": success_metrics,
                "session_id": session_id,
                "learned_at": datetime.utcnow().isoformat()
            }
            
            await self.storage.store(
                key=pattern_key,
                value=pattern_data,
                metadata={"type": "learned_pattern"}
            )
    
    def _extract_access_pattern(self, entries: List[MemoryEntry]) -> Dict[str, Any]:
        """Extrai padrão de acesso dos dados da sessão"""
        # Analisar sequência de operações
        operations = []
        for entry in sorted(entries, key=lambda e: e.timestamp):
            operations.append({
                "type": entry.metadata.get("type"),
                "timestamp": entry.timestamp.isoformat(),
                "data_size": len(str(entry.value))
            })
        
        return {
            "operation_sequence": operations,
            "total_operations": len(operations),
            "session_duration": (entries[-1].timestamp - entries[0].timestamp).total_seconds(),
            "most_common_operation": max(set(op["type"] for op in operations), 
                                       key=lambda x: [op["type"] for op in operations].count(x))
        }
    
    async def suggest_next_action(self, agent_id: str, current_context: str) -> Optional[str]:
        """Sugere próxima ação baseada em padrões aprendidos"""
        # Buscar padrões similares
        search_query = SearchQuery(
            semantic_query=current_context,
            metadata_filters={"type": "learned_pattern"},
            max_results=5
        )
        
        result = await self.storage.search(search_query)
        
        if result.entries:
            # Analisar padrões e sugerir próxima ação
            best_pattern = max(result.entries, 
                             key=lambda e: e.value["success_metrics"]["overall_success"])
            
            # Extrair sugestão do melhor padrão
            pattern = best_pattern.value["access_pattern"]
            return pattern.get("most_common_operation")
        
        return None


class AccessPatternOptimizer:
    """Otimizador de padrões de acesso à memória"""
    
    def __init__(self):
        self.access_history: List[Dict[str, Any]] = []
        self.optimization_suggestions: List[str] = []
    
    def record_access(self, operation: str, key: str, duration: float):
        """Registra padrão de acesso"""
        self.access_history.append({
            "operation": operation,
            "key": key,
            "duration": duration,
            "timestamp": time.time()
        })
        
        # Manter apenas últimos 1000 acessos
        if len(self.access_history) > 1000:
            self.access_history = self.access_history[-1000:]
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analisa padrões de acesso e sugere otimizações"""
        if not self.access_history:
            return {}
        
        # Análise de frequência de acesso
        key_frequency = {}
        operation_frequency = {}
        
        for access in self.access_history:
            key_frequency[access["key"]] = key_frequency.get(access["key"], 0) + 1
            operation_frequency[access["operation"]] = operation_frequency.get(access["operation"], 0) + 1
        
        # Identificar hot keys (acessados frequentemente)
        hot_keys = [key for key, freq in key_frequency.items() if freq > 10]
        
        # Identificar operações lentas
        slow_operations = [
            access for access in self.access_history 
            if access["duration"] > 1.0  # Mais de 1 segundo
        ]
        
        # Gerar sugestões de otimização
        suggestions = []
        
        if hot_keys:
            suggestions.append(f"Consider caching these frequently accessed keys: {hot_keys[:5]}")
        
        if slow_operations:
            suggestions.append(f"Found {len(slow_operations)} slow operations, consider optimization")
        
        return {
            "hot_keys": hot_keys,
            "slow_operations": len(slow_operations),
            "most_common_operation": max(operation_frequency.items(), key=lambda x: x[1])[0],
            "optimization_suggestions": suggestions
        }