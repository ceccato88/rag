"""
Enhanced RAG Subagents with Specialization, Retry Logic, and Shared Memory
"""

import asyncio
import time
import uuid
import sys
import os
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))
from src.core.config import SystemConfig

from researcher.agents.base import Agent, AgentContext, AgentResult, AgentState
from researcher.agents.document_search_agent import RAGResearchSubagent, RAGSubagentConfig
from researcher.tools.optimized_rag_search import OptimizedRAGSearchTool, DocumentProcessor
from researcher.memory.base import Memory, ResearchMemory

# Configuração centralizada
system_config = SystemConfig()


class SpecialistType(Enum):
    """Tipos de especialização para subagentes"""
    GENERAL = "general"
    CONCEPTUAL = "conceptual"
    COMPARATIVE = "comparative"
    TECHNICAL = "technical"
    EXAMPLES = "examples"
    HISTORICAL = "historical"


class RetryStrategy(Enum):
    """Estratégias de retry para diferentes tipos de erro"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE_RETRY = "immediate_retry"
    NO_RETRY = "no_retry"


class EnhancedRAGSubagentConfig(RAGSubagentConfig):
    """Configuração expandida para subagentes enhanced"""
    specialist_type: SpecialistType = SpecialistType.GENERAL
    max_retries: int = system_config.multiagent.max_retries
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    concurrency_limit: int = system_config.multiagent.concurrency_limit
    timeout_seconds: float = system_config.multiagent.subagent_timeout
    enable_cache: bool = True
    share_discoveries: bool = True
    circuit_breaker_threshold: int = system_config.multiagent.circuit_breaker_threshold
    circuit_breaker_timeout: int = system_config.multiagent.circuit_breaker_timeout


class CircuitBreakerState(Enum):
    """Estados do circuit breaker"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker para proteger contra falhas cascata"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def can_execute(self) -> bool:
        """Verifica se pode executar baseado no estado do circuit breaker"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Registra sucesso e reseta contador"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Registra falha e atualiza estado"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class SharedMemoryManager:
    """Gerenciador de memória compartilhada entre subagentes"""
    
    def __init__(self, memory: Memory[Any]):
        self.memory = memory
        self.discovery_queue = asyncio.Queue()
        
    async def share_discovery(self, agent_id: str, discovery: Dict[str, Any]):
        """Compartilha descoberta com outros agentes"""
        discovery_entry = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow(),
            "discovery": discovery,
            "keywords": self._extract_keywords(discovery)
        }
        
        # Adicionar à queue para processamento
        await self.discovery_queue.put(discovery_entry)
        
        # Armazenar na memória compartilhada
        discovery_key = f"discovery:{agent_id}:{int(time.time())}"
        await self.memory.store(
            key=discovery_key,
            value=discovery_entry,
            metadata={"type": "shared_discovery", "agent_id": agent_id}
        )
    
    async def get_relevant_discoveries(self, query: str, agent_id: str) -> List[Dict[str, Any]]:
        """Recupera descobertas relevantes para uma query"""
        query_keywords = set(query.lower().split())
        relevant_discoveries = []
        
        # Buscar todas as descobertas compartilhadas
        discovery_keys = await self.memory.list_keys(prefix="discovery:")
        
        for key in discovery_keys:
            discovery_data = await self.memory.retrieve(key)
            if discovery_data and discovery_data["agent_id"] != agent_id:  # Não incluir próprias descobertas
                discovery_keywords = set(discovery_data.get("keywords", []))
                
                # Verificar relevância baseada em keywords
                if query_keywords.intersection(discovery_keywords):
                    relevant_discoveries.append(discovery_data)
        
        # Ordenar por timestamp (mais recentes primeiro)
        return sorted(relevant_discoveries, key=lambda x: x["timestamp"], reverse=True)[:5]
    
    def _extract_keywords(self, discovery: Dict[str, Any]) -> List[str]:
        """Extrai keywords de uma descoberta para indexação"""
        text = str(discovery.get("findings", ""))
        words = text.lower().replace(",", " ").replace(".", " ").split()
        
        # Filtrar palavras muito curtas e muito comuns
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords = [word for word in words if len(word) > 3 and word not in stopwords]
        
        return list(set(keywords))[:10]  # Máximo 10 keywords


class ConceptExtractionSubagent(RAGResearchSubagent):
    """Subagente especializado em extração de conceitos e definições"""
    
    _focus_area = "conceptual_understanding"
    
    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Cria plano focado em conceitos e definições"""
        return [{
            "query": f"definition concepts fundamentals {context.query}",
            "objective": context.objective,
            "focus_area": "conceptual",
            "expected_output": "Clear definitions and conceptual understanding"
        }]
    
    # Herda execute do RAGResearchSubagent que já usa a ferramenta otimizada


class ComparativeAnalysisSubagent(RAGResearchSubagent):
    """Subagente especializado em análises comparativas"""
    
    _focus_area = "comparative_analysis"
    
    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Cria plano focado em comparações e alternativas"""
        return [{
            "query": f"compare alternatives differences {context.query}",
            "objective": context.objective,
            "focus_area": "comparative",
            "expected_output": "Comparative analysis with pros/cons"
        }]


class TechnicalDetailSubagent(RAGResearchSubagent):
    """Subagente especializado em detalhes técnicos"""
    
    _focus_area = "technical_implementation"
    
    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Cria plano focado em aspectos técnicos"""
        return [{
            "query": f"technical implementation architecture {context.query}",
            "objective": context.objective,
            "focus_area": "technical",
            "expected_output": "Detailed technical implementation information"
        }]


class ExampleFinderSubagent(RAGResearchSubagent):
    """Subagente especializado em encontrar exemplos e casos de uso"""
    
    _focus_area = "examples_and_use_cases"
    
    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Cria plano focado em exemplos práticos"""
        return [{
            "query": f"examples use cases applications {context.query}",
            "objective": context.objective,
            "focus_area": "examples",
            "expected_output": "Concrete examples and use cases"
        }]


class SpecialistSelector:
    """Seletor inteligente de especialistas baseado na query"""
    
    def __init__(self):
        self.specialists = {
            SpecialistType.CONCEPTUAL: ConceptExtractionSubagent,
            SpecialistType.COMPARATIVE: ComparativeAnalysisSubagent,
            SpecialistType.TECHNICAL: TechnicalDetailSubagent,
            SpecialistType.EXAMPLES: ExampleFinderSubagent,
            SpecialistType.GENERAL: RAGResearchSubagent
        }
        
        # Patterns para identificar tipos de queries
        self.query_patterns = {
            SpecialistType.CONCEPTUAL: [
                "what is", "define", "definition", "concept", "meaning", "explain"
            ],
            SpecialistType.COMPARATIVE: [
                "compare", "comparison", "vs", "versus", "difference", "alternative",
                "pros and cons", "advantages", "disadvantages"
            ],
            SpecialistType.TECHNICAL: [
                "how", "implementation", "technical", "architecture", "design",
                "specifications", "methodology", "algorithm"
            ],
            SpecialistType.EXAMPLES: [
                "example", "examples", "use case", "case study", "practical",
                "real world", "application", "scenario"
            ]
        }
    
    def select_specialists(self, query: str, objective: str, max_specialists: int = 3) -> List[Type[RAGResearchSubagent]]:
        """Seleciona especialistas apropriados baseado na query e objetivo"""
        query_lower = query.lower()
        objective_lower = objective.lower()
        combined_text = f"{query_lower} {objective_lower}"
        
        # Pontuação para cada tipo de especialista
        specialist_scores = {}
        
        for specialist_type, patterns in self.query_patterns.items():
            score = sum(1 for pattern in patterns if pattern in combined_text)
            if score > 0:
                specialist_scores[specialist_type] = score
        
        # Se nenhum padrão específico foi encontrado, usar general
        if not specialist_scores:
            return [self.specialists[SpecialistType.GENERAL]]
        
        # Selecionar top specialists baseado na pontuação
        sorted_specialists = sorted(
            specialist_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        selected_types = [item[0] for item in sorted_specialists[:max_specialists]]
        selected_classes = [self.specialists[spec_type] for spec_type in selected_types]
        
        return selected_classes


class EnhancedRAGSubagent(RAGResearchSubagent):
    """Subagente RAG com recursos avançados de retry, cache e colaboração"""
    
    def __init__(
        self,
        config: Optional[EnhancedRAGSubagentConfig] = None,
        shared_memory: Optional[Memory[Any]] = None,
        **kwargs
    ):
        # Usar config padrão se não fornecido
        if config is None:
            config = EnhancedRAGSubagentConfig()
        
        super().__init__(config, **kwargs)
        self.enhanced_config = config
        self.shared_memory = shared_memory
        self.memory_manager = SharedMemoryManager(shared_memory) if shared_memory else None
        
        # Controle de concorrência
        self.semaphore = asyncio.Semaphore(config.concurrency_limit)
        
        # Circuit breaker para proteção
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout=config.circuit_breaker_timeout
        )
        
        # Cache local para resultados
        self.local_cache: Dict[str, Any] = {}
        
        # Métricas
        self.execution_count = 0
        self.success_count = 0
        self.total_execution_time = 0.0
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Executa subagente com controle de concorrência e retry logic"""
        async with self.semaphore:  # Controle de concorrência
            return await self._run_with_protection(context)
    
    async def _run_with_protection(self, context: AgentContext) -> AgentResult:
        """Executa com circuit breaker e retry logic"""
        
        # Verificar circuit breaker
        if not self.circuit_breaker.can_execute():
            return AgentResult(
                agent_id=self.agent_id,
                status=AgentState.FAILED,
                output="Service temporarily unavailable (circuit breaker open)",
                error="Circuit breaker protection active"
            )
        
        # Tentar execução com retry
        last_exception = None
        
        for attempt in range(self.enhanced_config.max_retries + 1):
            try:
                start_time = time.time()
                
                # Verificar cache primeiro
                if self.enhanced_config.enable_cache:
                    cached_result = await self._check_cache(context.query)
                    if cached_result:
                        self.add_thinking("Found cached result for similar query")
                        return cached_result
                
                # Obter contexto compartilhado
                shared_context = await self._get_shared_context(context)
                
                # Executar com timeout
                result = await asyncio.wait_for(
                    self._execute_enhanced(context, shared_context),
                    timeout=self.enhanced_config.timeout_seconds
                )
                
                execution_time = time.time() - start_time
                
                # Registrar sucesso
                self.circuit_breaker.record_success()
                self._record_success(execution_time)
                
                # Cache do resultado
                if self.enhanced_config.enable_cache:
                    await self._cache_result(context.query, result)
                
                # Compartilhar descobertas se habilitado
                if self.enhanced_config.share_discoveries and self.memory_manager:
                    await self._share_discoveries(result)
                
                return result
                
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"Execution timeout after {self.enhanced_config.timeout_seconds}s")
                self.add_thinking(f"Timeout on attempt {attempt + 1}")
                
            except Exception as e:
                last_exception = e
                self.add_thinking(f"Error on attempt {attempt + 1}: {str(e)}")
                
                # Verificar se é retryable
                if not self._is_retryable_error(e) or attempt == self.enhanced_config.max_retries:
                    break
            
            # Aplicar backoff strategy se não for última tentativa
            if attempt < self.enhanced_config.max_retries:
                wait_time = self._calculate_backoff_time(attempt)
                self.add_thinking(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        # Registrar falha final
        self.circuit_breaker.record_failure()
        self._record_failure()
        
        return AgentResult(
            agent_id=self.agent_id,
            status=AgentState.FAILED,
            output="Failed after all retry attempts",
            error=str(last_exception) if last_exception else "Unknown error"
        )
    
    async def _execute_enhanced(self, context: AgentContext, shared_context: List[Dict]) -> AgentResult:
        """Execução enhanced com contexto compartilhado"""
        
        # Incorporar contexto compartilhado no planning
        enhanced_context = self._enhance_context_with_shared_info(context, shared_context)
        
        # Executar plan normal
        plan = await self.plan(enhanced_context)
        
        if not plan:
            return AgentResult(
                agent_id=self.agent_id,
                status=AgentState.FAILED,
                output="No plan generated",
                error="Planning phase failed"
            )
        
        # Executar plan
        try:
            self.current_state = AgentState.EXECUTING
            result_text = await self.execute(plan)
            
            return AgentResult(
                agent_id=self.agent_id,
                status=AgentState.COMPLETED,
                output=result_text,
                thinking="\n".join(self.thinking_log)
            )
            
        except Exception as e:
            return AgentResult(
                agent_id=self.agent_id,
                status=AgentState.FAILED,
                output="Execution failed",
                error=str(e),
                thinking="\n".join(self.thinking_log)
            )
    
    async def _get_shared_context(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Recupera contexto compartilhado relevante"""
        if not self.memory_manager:
            return []
        
        try:
            return await self.memory_manager.get_relevant_discoveries(
                context.query, 
                self.agent_id
            )
        except Exception as e:
            self.add_thinking(f"Failed to get shared context: {e}")
            return []
    
    def _enhance_context_with_shared_info(self, context: AgentContext, shared_context: List[Dict]) -> AgentContext:
        """Enriquece contexto com informações compartilhadas"""
        if not shared_context:
            return context
        
        # Adicionar informações compartilhadas às constraints
        shared_info = "Relevant shared discoveries: "
        for discovery in shared_context[:3]:  # Máximo 3 descobertas
            shared_info += f"[{discovery['agent_id']}] {str(discovery['discovery'])[:100]}... "
        
        enhanced_constraints = context.constraints + [shared_info]
        
        return AgentContext(
            query=context.query,
            objective=context.objective,
            constraints=enhanced_constraints
        )
    
    async def _share_discoveries(self, result: AgentResult):
        """Compartilha descobertas importantes com outros agentes"""
        if not self.memory_manager or result.status != AgentState.COMPLETED:
            return
        
        # Extrair descobertas do resultado
        discovery = {
            "agent_type": self.__class__.__name__,
            "findings": result.output[:500],  # Primeiros 500 chars
            "status": "completed",
            "quality_score": len(result.output) / 1000  # Score baseado no tamanho
        }
        
        try:
            await self.memory_manager.share_discovery(self.agent_id, discovery)
        except Exception as e:
            self.add_thinking(f"Failed to share discovery: {e}")
    
    async def _check_cache(self, query: str) -> Optional[AgentResult]:
        """Verifica cache para queries similares"""
        if not self.shared_memory:
            return None
        
        try:
            # Buscar por queries similares no cache
            cache_keys = await self.shared_memory.list_keys(prefix="cache:")
            
            for key in cache_keys:
                cached_data = await self.shared_memory.retrieve(key)
                if cached_data and self._is_similar_query(query, cached_data.get("query", "")):
                    # Retornar resultado cached
                    return AgentResult(
                        agent_id=self.agent_id,
                        status=AgentState.COMPLETED,
                        output=cached_data["result"],
                        thinking="Retrieved from cache"
                    )
        
        except Exception as e:
            self.add_thinking(f"Cache check failed: {e}")
        
        return None
    
    async def _cache_result(self, query: str, result: AgentResult):
        """Armazena resultado no cache"""
        if not self.shared_memory or result.status != AgentState.COMPLETED:
            return
        
        try:
            cache_key = f"cache:{self.agent_id}:{hash(query)}"
            cache_data = {
                "query": query,
                "result": result.output,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.shared_memory.store(
                key=cache_key,
                value=cache_data,
                metadata={"type": "cache_entry", "agent_id": self.agent_id}
            )
            
        except Exception as e:
            self.add_thinking(f"Cache storage failed: {e}")
    
    def _is_similar_query(self, query1: str, query2: str) -> bool:
        """Verifica similaridade entre queries"""
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2)) / len(words1.union(words2))
        return overlap > system_config.multiagent.similarity_threshold
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determina se um erro é retryable"""
        retryable_patterns = [
            "timeout", "connection", "rate limit", "temporary", 
            "unavailable", "too many requests", "network"
        ]
        
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def _calculate_backoff_time(self, attempt: int) -> float:
        """Calcula tempo de backoff baseado na estratégia"""
        if self.enhanced_config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return min(system_config.multiagent.exponential_backoff_max, 2 ** attempt)
        elif self.enhanced_config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            return min(system_config.multiagent.linear_backoff_max, (attempt + 1) * 5)
        else:
            return system_config.multiagent.immediate_retry_delay
    
    def _record_success(self, execution_time: float):
        """Registra métricas de sucesso"""
        self.execution_count += 1
        self.success_count += 1
        self.total_execution_time += execution_time
    
    def _record_failure(self):
        """Registra métricas de falha"""
        self.execution_count += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance"""
        success_rate = self.success_count / self.execution_count if self.execution_count > 0 else 0.0
        avg_execution_time = self.total_execution_time / self.success_count if self.success_count > 0 else 0.0
        
        return {
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failures": self.circuit_breaker.failure_count
        }