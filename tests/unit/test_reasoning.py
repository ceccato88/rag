#!/usr/bin/env python3
"""
Testes unitários para ReAct Reasoning
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from multi_agent_researcher.src.researcher.reasoning.react_reasoning import (
    ReActReasoner, 
    ReasoningStep,
    FactGathering,
    TaskPlan,
    ValidationResult
)


class TestReActReasoner:
    """Testes para ReAct Reasoning"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.reasoner = ReActReasoner("Test Agent")
    
    def test_reasoner_initialization(self):
        """Testa inicialização do reasoner"""
        assert self.reasoner.agent_name == "Test Agent"
        assert len(self.reasoner.reasoning_history) == 0
        assert self.reasoner.iteration_count == 0
    
    def test_add_reasoning_step(self):
        """Testa adição de step de reasoning"""
        step = self.reasoner.add_reasoning_step(
            step_type="planning",
            content="Test planning step",
            observations="Test observation",
            next_action="Next action"
        )
        
        assert isinstance(step, ReasoningStep)
        assert step.step_type == "planning"
        assert step.content == "Test planning step"
        assert step.observations == "Test observation"
        assert step.next_action == "Next action"
        
        assert len(self.reasoner.reasoning_history) == 1
        assert self.reasoner.reasoning_history[0] == step
    
    def test_fact_gathering(self):
        """Testa processo de fact gathering"""
        facts = self.reasoner.gather_facts(
            task="Test task",
            context="Test context"
        )
        
        assert isinstance(facts, FactGathering)
        assert isinstance(facts.given_facts, list)
        assert isinstance(facts.recalled_facts, list)
        assert isinstance(facts.assumptions, list)
        
        # Deve ter adicionado um step de reasoning
        assert len(self.reasoner.reasoning_history) == 1
        assert self.reasoner.reasoning_history[0].step_type == "fact_gathering"
    
    def test_create_plan(self):
        """Testa criação de plano"""
        plan = self.reasoner.create_plan(
            objective="Test objective",
            available_resources=["resource1", "resource2"]
        )
        
        assert isinstance(plan, TaskPlan)
        assert plan.objective == "Test objective"
        assert isinstance(plan.steps, list)
        assert len(plan.steps) > 0
        assert plan.resources_needed == ["resource1", "resource2"]
        
        # Deve ter adicionado um step de reasoning
        planning_steps = [s for s in self.reasoner.reasoning_history if s.step_type == "planning"]
        assert len(planning_steps) == 1
    
    def test_execute_step(self):
        """Testa execução de step"""
        step = self.reasoner.execute_step(
            step_description="Test step",
            action_taken="Test action",
            result="Test result"
        )
        
        assert isinstance(step, ReasoningStep)
        assert step.step_type == "execution"
        assert "Test step" in step.content
        assert "Test action" in step.observations
        assert "Test result" in step.observations
        
        assert self.reasoner.iteration_count == 1
    
    def test_validate_progress(self):
        """Testa validação de progresso"""
        # Adiciona alguns steps primeiro
        self.reasoner.add_reasoning_step("execution", "Step 1", "Obs 1", "Next 1")
        self.reasoner.add_reasoning_step("execution", "Step 2", "Obs 2", "Next 2")
        
        validation = self.reasoner.validate_progress("Original task")
        
        assert isinstance(validation, ValidationResult)
        assert isinstance(validation.is_task_completed, bool)
        assert isinstance(validation.is_in_loop, bool)
        assert isinstance(validation.confidence_level, float)
        assert 0 <= validation.confidence_level <= 1
    
    def test_loop_detection(self):
        """Testa detecção de loops"""
        # Simula um loop adicionando steps repetitivos
        for i in range(5):
            self.reasoner.add_reasoning_step("execution", f"Step {i}", "Same obs", "Same action")
            self.reasoner.iteration_count += 1
        
        is_loop = self.reasoner._detect_reasoning_loop()
        assert isinstance(is_loop, bool)
    
    def test_confidence_calculation(self):
        """Testa cálculo de confiança"""
        # Adiciona alguns steps de diferentes tipos
        self.reasoner.add_reasoning_step("execution", "Exec 1", "Obs", "Next")
        self.reasoner.add_reasoning_step("validation", "Valid 1", "Obs", "Next")
        self.reasoner.add_reasoning_step("execution", "Exec 2", "Obs", "Next")
        
        confidence = self.reasoner._calculate_confidence()
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    def test_reasoning_trace_generation(self):
        """Testa geração de trace de reasoning"""
        # Adiciona alguns steps
        self.reasoner.add_reasoning_step("fact_gathering", "Gathering facts", "Facts found", "Plan next")
        self.reasoner.add_reasoning_step("planning", "Creating plan", "Plan created", "Execute")
        self.reasoner.add_reasoning_step("execution", "Executing", "Action done", "Validate")
        
        trace = self.reasoner.get_reasoning_trace()
        
        assert isinstance(trace, str)
        assert "Trace de Raciocínio" in trace
        assert "FACT_GATHERING" in trace
        assert "PLANNING" in trace
        assert "EXECUTION" in trace
    
    def test_reflect_and_adjust(self):
        """Testa reflexão e ajuste"""
        # Adiciona alguns steps primeiro
        self.reasoner.add_reasoning_step("execution", "Failed step", "Error occurred", "Retry")
        
        improved_plan = self.reasoner.reflect_and_adjust("timeout occurred")
        
        assert isinstance(improved_plan, TaskPlan)
        
        # Deve ter adicionado um step de reflection
        reflection_steps = [s for s in self.reasoner.reasoning_history if s.step_type == "reflection"]
        assert len(reflection_steps) == 1


class TestReasoningIntegration:
    """Testes de integração do reasoning"""
    
    def test_full_reasoning_cycle(self):
        """Testa ciclo completo de reasoning"""
        reasoner = ReActReasoner("Integration Test Agent")
        
        # 1. Fact gathering
        facts = reasoner.gather_facts("Test task", "Test context")
        assert len(reasoner.reasoning_history) == 1
        
        # 2. Planning
        plan = reasoner.create_plan("Test objective", ["resource1"])
        assert len(reasoner.reasoning_history) == 2
        
        # 3. Execution
        step = reasoner.execute_step("Execute plan", "Action taken", "Success")
        assert len(reasoner.reasoning_history) == 3
        
        # 4. Validation
        validation = reasoner.validate_progress("Test task")
        assert isinstance(validation, ValidationResult)
        
        # 5. Trace generation
        trace = reasoner.get_reasoning_trace()
        assert "Passo 1" in trace
        assert "Passo 2" in trace
        assert "Passo 3" in trace


if __name__ == "__main__":
    pytest.main([__file__, "-v"])