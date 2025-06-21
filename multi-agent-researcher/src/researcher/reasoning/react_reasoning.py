"""
ReAct (Reasoning + Acting) pattern implementation for structured reasoning.
Substitui o sistema "thinking" do Anthropic por uma abordagem estruturada de raciocínio.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../../"))

# Import do logger multi-agente (com fallback caso não esteja disponível)
try:
    from researcher.utils.multiagent_logger import get_multiagent_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


class ReasoningStep(BaseModel):
    """Um passo individual no processo de raciocínio."""
    step_type: str  # "fact_gathering", "planning", "execution", "validation", "reflection"
    timestamp: datetime
    content: str
    observations: Optional[str] = None
    next_action: Optional[str] = None


class FactGathering(BaseModel):
    """Coleta de fatos para fundamentar o raciocínio."""
    given_facts: List[str]  # Fatos explicitamente fornecidos
    recalled_facts: List[str]  # Fatos lembrados do conhecimento/assumidos
    assumptions: List[str]  # Suposições bem fundamentadas


class TaskPlan(BaseModel):
    """Plano estruturado para abordar a tarefa."""
    objective: str
    steps: List[str]
    expected_outcome: str
    resources_needed: List[str]


class ValidationResult(BaseModel):
    """Resultado da validação do progresso."""
    is_task_completed: bool
    is_in_loop: bool
    progress_summary: str
    next_instruction: Optional[str] = None
    confidence_level: float  # 0.0 a 1.0


class ReActReasoner:
    """
    Implementa o padrão ReAct para raciocínio estruturado.
    Substitui o sistema "thinking" do Anthropic.
    """
    
    def __init__(self, agent_name: str = "ReAct Agent"):
        self.agent_name = agent_name
        self.reasoning_history: List[ReasoningStep] = []
        self.current_facts: Optional[FactGathering] = None
        self.current_plan: Optional[TaskPlan] = None
        self.iteration_count = 0
        self.max_iterations = 10
        
        # Configurar logger se disponível
        if LOGGER_AVAILABLE:
            self.logger = get_multiagent_logger(f"ReActReasoner-{agent_name}")
        else:
            self.logger = None
    
    def add_reasoning_step(
        self, 
        step_type: str, 
        content: str, 
        observations: Optional[str] = None,
        next_action: Optional[str] = None
    ):
        """Adiciona um passo de raciocínio ao histórico."""
        step = ReasoningStep(
            step_type=step_type,
            timestamp=datetime.now(),
            content=content,
            observations=observations,
            next_action=next_action
        )
        self.reasoning_history.append(step)
        
        # Log usando o logger multi-agente se disponível
        if self.logger:
            self.logger.reasoning_step(step_type, content, observations, next_action)
        
        return step
    
    def gather_facts(self, task: str, context: str = "") -> FactGathering:
        """
        Etapa 1: Coleta de fatos.
        Fundamenta o raciocínio em conhecimento verificado.
        """
        self.add_reasoning_step(
            "fact_gathering",
            f"Coletando fatos para a tarefa: {task}",
            context,
            "Analisar fatos dados e relembrar conhecimento relevante"
        )
        
        # Estrutura base para coleta de fatos
        facts = FactGathering(
            given_facts=[],
            recalled_facts=[],
            assumptions=[]
        )
        
        self.current_facts = facts
        return facts
    
    def create_plan(self, objective: str, available_resources: List[str] = None) -> TaskPlan:
        """
        Etapa 2: Planejamento.
        Quebra problemas complexos em sub-tarefas gerenciáveis.
        """
        self.add_reasoning_step(
            "planning",
            f"Criando plano para: {objective}",
            f"Recursos disponíveis: {available_resources or []}",
            "Desenvolver plano estruturado em etapas"
        )
        
        plan = TaskPlan(
            objective=objective,
            steps=[],
            expected_outcome="",
            resources_needed=available_resources or []
        )
        
        self.current_plan = plan
        return plan
    
    def execute_step(self, step_description: str, action_taken: str, result: str) -> ReasoningStep:
        """
        Etapa 3: Execução.
        Executa as ações definidas no plano.
        """
        step = self.add_reasoning_step(
            "execution",
            f"Executando: {step_description}",
            f"Ação: {action_taken}\nResultado: {result}",
            "Avaliar resultado e determinar próximo passo"
        )
        
        self.iteration_count += 1
        return step
    
    def validate_progress(self, original_task: str) -> ValidationResult:
        """
        Etapa 4: Validação.
        Verifica o progresso em direção ao objetivo final.
        """
        # Analisa se a tarefa foi completada
        is_completed = self._assess_task_completion(original_task)
        
        # Detecta loops
        is_in_loop = self._detect_reasoning_loop()
        
        # Gera resumo do progresso
        progress = self._summarize_progress()
        
        # Determina próxima instrução
        next_instruction = None if is_completed else self._determine_next_action()
        
        # Calcula nível de confiança
        confidence = self._calculate_confidence()
        
        validation = ValidationResult(
            is_task_completed=is_completed,
            is_in_loop=is_in_loop,
            progress_summary=progress,
            next_instruction=next_instruction,
            confidence_level=confidence
        )
        
        self.add_reasoning_step(
            "validation",
            f"Validação: {'Tarefa completa' if is_completed else 'Em progresso'}",
            f"Confiança: {confidence:.2f}, Loop: {is_in_loop}",
            next_instruction
        )
        
        return validation
    
    def reflect_and_adjust(self, what_went_wrong: str) -> TaskPlan:
        """
        Etapa 5: Reflexão e ajuste.
        Atualiza fatos e replaneja quando necessário.
        """
        self.add_reasoning_step(
            "reflection",
            f"Refletindo sobre problemas: {what_went_wrong}",
            "Analisando falhas e ajustando abordagem",
            "Recriar plano melhorado"
        )
        
        # Atualiza o plano atual com base na reflexão
        if self.current_plan:
            # Aqui seria implementada a lógica de melhoria do plano
            pass
        
        return self.current_plan
    
    def get_reasoning_trace(self) -> str:
        """Retorna um trace legível do processo de raciocínio."""
        trace = f"=== Trace de Raciocínio - {self.agent_name} ===\n\n"
        
        for i, step in enumerate(self.reasoning_history, 1):
            trace += f"🔍 Passo {i}: {step.step_type.upper()}\n"
            trace += f"⏰ {step.timestamp.strftime('%H:%M:%S')}\n"
            trace += f"💭 {step.content}\n"
            
            if step.observations:
                trace += f"👁️ Observações: {step.observations}\n"
            
            if step.next_action:
                trace += f"➡️ Próxima ação: {step.next_action}\n"
            
            trace += "\n" + "─" * 50 + "\n\n"
        
        return trace
    
    def _assess_task_completion(self, original_task: str) -> bool:
        """Avalia se a tarefa original foi completada."""
        # Lógica simples: verifica se houve execuções suficientes
        execution_steps = [s for s in self.reasoning_history if s.step_type == "execution"]
        return len(execution_steps) > 0 and self.iteration_count >= 1
    
    def _detect_reasoning_loop(self) -> bool:
        """Detecta se o raciocínio está em loop."""
        if len(self.reasoning_history) < 4:
            return False
        
        # Verifica os últimos 4 passos para padrões repetitivos
        recent_steps = self.reasoning_history[-4:]
        step_types = [s.step_type for s in recent_steps]
        
        # Se há repetição excessiva do mesmo tipo de passo
        return len(set(step_types)) <= 2 and self.iteration_count > 3
    
    def _summarize_progress(self) -> str:
        """Gera um resumo do progresso atual."""
        total_steps = len(self.reasoning_history)
        execution_steps = len([s for s in self.reasoning_history if s.step_type == "execution"])
        
        return f"Executados {total_steps} passos de raciocínio, incluindo {execution_steps} execuções"
    
    def _determine_next_action(self) -> Optional[str]:
        """Determina a próxima ação baseada no contexto atual."""
        if not self.reasoning_history:
            return "Iniciar coleta de fatos"
        
        last_step = self.reasoning_history[-1]
        
        if last_step.step_type == "fact_gathering":
            return "Criar plano baseado nos fatos coletados"
        elif last_step.step_type == "planning":
            return "Executar primeiro passo do plano"
        elif last_step.step_type == "execution":
            return "Validar progresso e continuar execução"
        elif last_step.step_type == "validation":
            return "Executar próximo passo do plano"
        else:
            return "Continuar com o processo"
    
    def _calculate_confidence(self) -> float:
        """Calcula nível de confiança baseado no progresso."""
        if not self.reasoning_history:
            return 0.0
        
        # Fatores que aumentam confiança
        execution_steps = len([s for s in self.reasoning_history if s.step_type == "execution"])
        validation_steps = len([s for s in self.reasoning_history if s.step_type == "validation"])
        
        # Fatores que diminuem confiança
        reflection_steps = len([s for s in self.reasoning_history if s.step_type == "reflection"])
        is_in_loop = self._detect_reasoning_loop()
        
        base_confidence = min(1.0, (execution_steps * 0.3 + validation_steps * 0.2))
        loop_penalty = 0.3 if is_in_loop else 0.0
        reflection_penalty = reflection_steps * 0.1
        
        return max(0.0, base_confidence - loop_penalty - reflection_penalty)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o estado do reasoner para dicionário."""
        return {
            "agent_name": self.agent_name,
            "iteration_count": self.iteration_count,
            "reasoning_history": [step.model_dump() for step in self.reasoning_history],
            "current_facts": self.current_facts.model_dump() if self.current_facts else None,
            "current_plan": self.current_plan.model_dump() if self.current_plan else None
        }
