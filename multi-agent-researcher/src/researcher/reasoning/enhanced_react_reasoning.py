"""
Enhanced ReAct Reasoning with Memory Integration and Advanced Features
"""

import asyncio
import hashlib
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from researcher.reasoning.react_reasoning import (
    ReActReasoner, ReasoningStep, FactGathering, TaskPlan, 
    ValidationResult
)
from researcher.memory.base import Memory, MemoryEntry


class LoopSeverity(Enum):
    """Severidade da detecção de loops"""
    NONE = "none"
    LOW = "low"  
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LoopAnalysis:
    """Análise detalhada de loops no reasoning"""
    has_loop: bool
    loop_type: str  # "content_repetition", "action_cycle", "reasoning_stuck"
    severity: LoopSeverity
    suggestion: str
    loop_entries: List[int] = field(default_factory=list)  # Índices dos steps no loop
    confidence: float = 0.0


@dataclass
class ConfidenceMetrics:
    """Métricas multidimensionais de confiança"""
    factual_confidence: float = 0.0
    logical_confidence: float = 0.0
    execution_confidence: float = 0.0
    validation_confidence: float = 0.0
    temporal_confidence: float = 0.0
    overall_confidence: float = 0.0


class EnhancedReasoningStep(BaseModel):
    """Step de reasoning aprimorado com metadados extensos"""
    step_type: str
    timestamp: datetime
    content: str
    observations: Optional[str] = None
    next_action: Optional[str] = None
    
    # Novos campos para análise avançada
    confidence_score: float = 0.0
    dependencies: List[str] = Field(default_factory=list)
    success_metrics: Dict[str, float] = Field(default_factory=dict)
    context_hash: str = ""
    execution_time: float = 0.0
    memory_usage: Optional[int] = None
    error_context: Optional[Dict[str, Any]] = None
    
    # Metadados semânticos
    semantic_tags: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    outcome_quality: Optional[float] = None
    
    @classmethod
    def from_basic_step(cls, step: ReasoningStep, **kwargs) -> "EnhancedReasoningStep":
        """Converte ReasoningStep básico para versão enhanced"""
        return cls(
            step_type=step.step_type,
            timestamp=step.timestamp,
            content=step.content,
            observations=step.observations,
            next_action=step.next_action,
            context_hash=hashlib.md5(step.content.encode()).hexdigest()[:8],
            **kwargs
        )


class ReasoningPatternDatabase:
    """Database de padrões de reasoning bem-sucedidos"""
    
    def __init__(self):
        self.successful_patterns: Dict[str, List[Dict]] = {}
        self.failure_patterns: Dict[str, List[Dict]] = {}
        
    def add_successful_pattern(self, context_type: str, reasoning_chain: List[EnhancedReasoningStep]):
        """Adiciona padrão de reasoning bem-sucedido"""
        if context_type not in self.successful_patterns:
            self.successful_patterns[context_type] = []
            
        pattern = {
            "steps": [step.step_type for step in reasoning_chain],
            "avg_confidence": sum(step.confidence_score for step in reasoning_chain) / len(reasoning_chain),
            "total_time": sum(step.execution_time for step in reasoning_chain),
            "step_count": len(reasoning_chain)
        }
        
        self.successful_patterns[context_type].append(pattern)
        
    def suggest_next_step(self, context_type: str, current_steps: List[str]) -> Optional[str]:
        """Sugere próximo step baseado em padrões históricos"""
        if context_type not in self.successful_patterns:
            return None
            
        patterns = self.successful_patterns[context_type]
        current_length = len(current_steps)
        
        # Encontrar padrões que começam como a sequência atual
        matching_patterns = []
        for pattern in patterns:
            if (len(pattern["steps"]) > current_length and 
                pattern["steps"][:current_length] == current_steps):
                matching_patterns.append(pattern)
        
        if matching_patterns:
            # Retornar próximo step do padrão com maior confiança
            best_pattern = max(matching_patterns, key=lambda p: p["avg_confidence"])
            return best_pattern["steps"][current_length]
            
        return None


class PersistentReActReasoner(ReActReasoner):
    """ReAct Reasoner com persistência e recursos avançados"""
    
    def __init__(self, agent_name: str, memory: Memory[Any]):
        super().__init__(agent_name)
        self.memory = memory
        self.session_id = str(uuid.uuid4())
        self.enhanced_history: List[EnhancedReasoningStep] = []
        self.pattern_database = ReasoningPatternDatabase()
        self.auto_checkpoint = True
        self.checkpoint_interval = 5  # Checkpoint a cada 5 steps
        
    async def add_reasoning_step(self, step_type: str, content: str, 
                               observations: Optional[str] = None,
                               next_action: Optional[str] = None,
                               **kwargs) -> EnhancedReasoningStep:
        """Adiciona step com persistência automática"""
        start_time = time.time()
        
        # Criar step básico primeiro
        basic_step = super().add_reasoning_step(step_type, content, observations, next_action)
        
        # Criar enhanced step
        enhanced_step = EnhancedReasoningStep.from_basic_step(
            basic_step,
            execution_time=time.time() - start_time,
            **kwargs
        )
        
        # Calcular métricas de confiança
        enhanced_step.confidence_score = await self._calculate_step_confidence(enhanced_step)
        
        # Adicionar à história enhanced
        self.enhanced_history.append(enhanced_step)
        
        # Persistir automaticamente
        if self.memory:
            await self._persist_step(enhanced_step)
            
        # Auto-checkpoint se necessário
        if (self.auto_checkpoint and 
            len(self.enhanced_history) % self.checkpoint_interval == 0):
            await self.create_checkpoint()
            
        return enhanced_step
    
    async def _persist_step(self, step: EnhancedReasoningStep):
        """Persiste step na memória"""
        step_key = f"reasoning:{self.session_id}:{len(self.enhanced_history)}"
        await self.memory.store(
            key=step_key,
            value=step.dict(),
            agent_id=self.agent_name,
            metadata={
                'type': 'reasoning_step',
                'step_type': step.step_type,
                'session_id': self.session_id,
                'step_number': len(self.enhanced_history),
                'confidence': step.confidence_score
            }
        )
    
    async def _calculate_step_confidence(self, step: EnhancedReasoningStep) -> float:
        """Calcula confiança multidimensional do step"""
        metrics = await self._calculate_sophisticated_confidence()
        
        # Peso baseado no tipo de step
        weights = {
            "fact_gathering": 0.2,
            "planning": 0.3,
            "execution": 0.4,
            "validation": 0.8,
            "reflection": 0.6
        }
        
        base_weight = weights.get(step.step_type, 0.5)
        
        # Confiança baseada na qualidade do conteúdo
        content_quality = min(1.0, len(step.content) / 100)  # Conteúdo mais detalhado = maior confiança
        
        # Confiança temporal (steps recentes têm maior relevância)
        time_factor = 1.0 if len(self.enhanced_history) < 5 else 0.9
        
        return base_weight * content_quality * time_factor * metrics.overall_confidence
    
    async def _calculate_sophisticated_confidence(self) -> ConfidenceMetrics:
        """Calcula métricas de confiança sofisticadas"""
        if not self.enhanced_history:
            return ConfidenceMetrics()
            
        # Análise de qualidade factual
        fact_steps = [s for s in self.enhanced_history if s.step_type == "fact_gathering"]
        factual_confidence = min(1.0, len(fact_steps) * 0.3) if fact_steps else 0.0
        
        # Análise de coerência lógica
        logical_confidence = await self._assess_reasoning_chain_coherence()
        
        # Análise de sucesso de execução
        execution_steps = [s for s in self.enhanced_history if s.step_type == "execution"]
        execution_confidence = sum(s.confidence_score for s in execution_steps) / len(execution_steps) if execution_steps else 0.0
        
        # Análise de validação
        validation_steps = [s for s in self.enhanced_history if s.step_type == "validation"]
        validation_confidence = min(1.0, len(validation_steps) * 0.4) if validation_steps else 0.0
        
        # Análise de eficiência temporal
        avg_time = sum(s.execution_time for s in self.enhanced_history) / len(self.enhanced_history)
        temporal_confidence = max(0.0, 1.0 - (avg_time / 10.0))  # Penaliza steps muito lentos
        
        # Confiança geral
        overall = (
            factual_confidence * 0.25 +
            logical_confidence * 0.30 +
            execution_confidence * 0.25 +
            validation_confidence * 0.15 +
            temporal_confidence * 0.05
        )
        
        return ConfidenceMetrics(
            factual_confidence=factual_confidence,
            logical_confidence=logical_confidence,
            execution_confidence=execution_confidence,
            validation_confidence=validation_confidence,
            temporal_confidence=temporal_confidence,
            overall_confidence=overall
        )
    
    async def _assess_reasoning_chain_coherence(self) -> float:
        """Avalia coerência da cadeia de raciocínio"""
        if len(self.enhanced_history) < 2:
            return 1.0
            
        coherence_score = 0.0
        transitions = 0
        
        # Analisar transições entre steps
        for i in range(1, len(self.enhanced_history)):
            prev_step = self.enhanced_history[i-1]
            curr_step = self.enhanced_history[i]
            
            # Verificar se a transição faz sentido
            if self._is_logical_transition(prev_step.step_type, curr_step.step_type):
                coherence_score += 1.0
            else:
                coherence_score += 0.5  # Penalidade parcial
                
            transitions += 1
        
        return coherence_score / transitions if transitions > 0 else 1.0
    
    def _is_logical_transition(self, from_type: str, to_type: str) -> bool:
        """Verifica se transição entre tipos de step é lógica"""
        logical_transitions = {
            "fact_gathering": ["planning", "fact_gathering"],
            "planning": ["execution", "planning"],
            "execution": ["validation", "execution", "planning"],
            "validation": ["reflection", "execution", "planning"],
            "reflection": ["planning", "execution"]
        }
        
        return to_type in logical_transitions.get(from_type, [])
    
    async def enhanced_loop_detection(self) -> LoopAnalysis:
        """Detecta loops com análise semântica avançada"""
        if len(self.enhanced_history) < 4:
            return LoopAnalysis(has_loop=False, loop_type="none", severity=LoopSeverity.NONE, suggestion="")
        
        # Análise de repetição de conteúdo
        content_similarity = await self._analyze_content_similarity()
        
        # Análise de ciclos de ação
        action_cycles = await self._detect_action_cycles()
        
        # Análise de reasoning travado
        reasoning_stuck = await self._detect_reasoning_stuck()
        
        # Determinar tipo e severidade do loop
        if content_similarity > 0.8:
            severity = LoopSeverity.HIGH if content_similarity > 0.9 else LoopSeverity.MEDIUM
            return LoopAnalysis(
                has_loop=True,
                loop_type="content_repetition",
                severity=severity,
                suggestion="Variar abordagem ou introduzir nova perspectiva",
                confidence=content_similarity
            )
        
        if action_cycles:
            return LoopAnalysis(
                has_loop=True,
                loop_type="action_cycle",
                severity=LoopSeverity.HIGH,
                suggestion="Quebrar ciclo com validação ou reflexão",
                loop_entries=action_cycles,
                confidence=0.9
            )
        
        if reasoning_stuck:
            return LoopAnalysis(
                has_loop=True,
                loop_type="reasoning_stuck",
                severity=LoopSeverity.MEDIUM,
                suggestion="Aplicar técnica de pensamento lateral ou buscar contexto adicional",
                confidence=0.7
            )
        
        return LoopAnalysis(has_loop=False, loop_type="none", severity=LoopSeverity.NONE, suggestion="")
    
    async def _analyze_content_similarity(self) -> float:
        """Analisa similaridade de conteúdo entre steps recentes"""
        if len(self.enhanced_history) < 4:
            return 0.0
        
        # Analisar últimos 6 steps
        recent_steps = self.enhanced_history[-6:]
        content_hashes = [step.context_hash for step in recent_steps]
        
        # Calcular similaridade
        unique_hashes = set(content_hashes)
        similarity = 1.0 - (len(unique_hashes) / len(content_hashes))
        
        return similarity
    
    async def _detect_action_cycles(self) -> List[int]:
        """Detecta ciclos de ações repetitivas"""
        if len(self.enhanced_history) < 6:
            return []
        
        # Analisar padrões de step_type
        recent_types = [step.step_type for step in self.enhanced_history[-6:]]
        
        # Procurar padrões repetitivos
        for pattern_length in [2, 3]:
            for start in range(len(recent_types) - pattern_length * 2 + 1):
                pattern = recent_types[start:start + pattern_length]
                next_pattern = recent_types[start + pattern_length:start + pattern_length * 2]
                
                if pattern == next_pattern:
                    return list(range(start, start + pattern_length * 2))
        
        return []
    
    async def _detect_reasoning_stuck(self) -> bool:
        """Detecta se reasoning está travado sem progresso"""
        if len(self.enhanced_history) < 8:
            return False
        
        # Verificar se houve progresso nos últimos steps
        recent_steps = self.enhanced_history[-8:]
        
        # Se todos os steps têm baixa confiança, pode estar travado
        avg_confidence = sum(step.confidence_score for step in recent_steps) / len(recent_steps)
        
        # Se não há steps de execução ou validação recentes, pode estar travado
        execution_or_validation = [s for s in recent_steps if s.step_type in ["execution", "validation"]]
        
        return avg_confidence < 0.3 and len(execution_or_validation) < 2
    
    async def create_checkpoint(self) -> str:
        """Cria checkpoint do estado atual do reasoning"""
        checkpoint_id = f"checkpoint:{self.session_id}:{int(time.time())}"
        
        checkpoint_data = {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "reasoning_history": [step.dict() for step in self.enhanced_history],
            "current_facts": self.current_facts.dict() if self.current_facts else None,
            "current_plan": self.current_plan.dict() if self.current_plan else None,
            "iteration_count": self.iteration_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.memory.store(
            key=checkpoint_id,
            value=checkpoint_data,
            agent_id=self.agent_name,
            metadata={
                "type": "reasoning_checkpoint",
                "session_id": self.session_id,
                "step_count": len(self.enhanced_history)
            }
        )
        
        return checkpoint_id
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """Restaura estado a partir de checkpoint"""
        try:
            checkpoint_data = await self.memory.retrieve(checkpoint_id, self.agent_name)
            if not checkpoint_data:
                return False
            
            # Restaurar estado
            self.session_id = checkpoint_data["session_id"]
            self.iteration_count = checkpoint_data["iteration_count"]
            
            # Restaurar história
            self.enhanced_history = [
                EnhancedReasoningStep(**step_data) 
                for step_data in checkpoint_data["reasoning_history"]
            ]
            
            # Reconstruir história básica para compatibilidade
            self.reasoning_history = [
                ReasoningStep(
                    step_type=step.step_type,
                    timestamp=step.timestamp,
                    content=step.content,
                    observations=step.observations,
                    next_action=step.next_action
                )
                for step in self.enhanced_history
            ]
            
            # Restaurar facts e plan se existirem
            if checkpoint_data["current_facts"]:
                self.current_facts = FactGathering(**checkpoint_data["current_facts"])
            if checkpoint_data["current_plan"]:
                self.current_plan = TaskPlan(**checkpoint_data["current_plan"])
            
            return True
            
        except Exception as e:
            print(f"Erro ao restaurar checkpoint {checkpoint_id}: {e}")
            return False
    
    async def suggest_next_step_intelligent(self, context_type: str = "general") -> Optional[str]:
        """Sugere próximo step baseado em padrões aprendidos"""
        current_steps = [step.step_type for step in self.enhanced_history]
        return self.pattern_database.suggest_next_step(context_type, current_steps)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance do reasoning"""
        if not self.enhanced_history:
            return {}
        
        total_time = sum(step.execution_time for step in self.enhanced_history)
        avg_confidence = sum(step.confidence_score for step in self.enhanced_history) / len(self.enhanced_history)
        
        step_distribution = {}
        for step in self.enhanced_history:
            step_distribution[step.step_type] = step_distribution.get(step.step_type, 0) + 1
        
        return {
            "total_execution_time": total_time,
            "average_confidence": avg_confidence,
            "step_count": len(self.enhanced_history),
            "step_distribution": step_distribution,
            "session_id": self.session_id,
            "checkpoint_count": len([s for s in self.enhanced_history if s.step_type == "checkpoint"])
        }