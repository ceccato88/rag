#!/usr/bin/env python3
"""
Testes unitários para sistema de agentes
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from multi_agent_researcher.src.researcher.agents.openai_lead_researcher import OpenAILeadResearcher
from multi_agent_researcher.src.researcher.agents.enhanced_rag_subagent import RAGResearchSubagent
from multi_agent_researcher.src.researcher.models.structured_models import AgentContext, ResearchTask


class TestOpenAILeadResearcher:
    """Testes para Lead Researcher"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.researcher = OpenAILeadResearcher()
    
    def test_researcher_initialization(self):
        """Testa inicialização do researcher"""
        assert self.researcher.agent_id is not None
        assert hasattr(self.researcher, 'reasoner')
        assert self.researcher.reasoner.agent_name.startswith("OpenAI Lead Researcher")
    
    def test_focus_area_selection_patterns(self):
        """Testa seleção de focus areas por padrões"""
        # Query conceitual
        conceptual_query = "What is Zep?"
        areas = self.researcher._select_focus_areas(conceptual_query)
        assert "conceptual" in areas
        
        # Query técnica
        technical_query = "How to implement Zep architecture?"
        areas = self.researcher._select_focus_areas(technical_query)
        assert "technical" in areas
        
        # Query comparativa
        comparative_query = "Zep vs MemGPT comparison"
        areas = self.researcher._select_focus_areas(comparative_query)
        assert "comparative" in areas
        
        # Query de exemplos
        examples_query = "Show me examples of Zep usage"
        areas = self.researcher._select_focus_areas(examples_query)
        assert "examples" in areas
    
    def test_focus_area_limits(self):
        """Testa limites de focus areas"""
        query = "What is Zep?"
        areas = self.researcher._select_focus_areas(query)
        
        # Não deve exceder max_subagents
        assert len(areas) <= 3
        
        # Deve ter pelo menos 1 area
        assert len(areas) >= 1
    
    def test_sophisticated_assumptions_creation(self):
        """Testa criação de assumptions sofisticadas"""
        query = "How does Zep implement temporal knowledge graphs?"
        assumptions = self.researcher._create_sophisticated_assumptions(query)
        
        assert isinstance(assumptions, list)
        assert len(assumptions) > 0
        
        # Deve conter assumptions relevantes
        assumption_text = " ".join(assumptions).lower()
        assert any(term in assumption_text for term in ["user", "technical", "implementation"])
    
    @patch('multi_agent_researcher.src.researcher.agents.openai_lead_researcher.instructor')
    def test_llm_decomposition(self, mock_instructor):
        """Testa decomposição LLM"""
        # Mock do instructor
        mock_client = MagicMock()
        mock_instructor.from_openai.return_value = mock_client
        
        mock_decomposition = MagicMock()
        mock_decomposition.tasks = [
            MagicMock(query="Task 1", focus="conceptual", reasoning="Reasoning 1"),
            MagicMock(query="Task 2", focus="technical", reasoning="Reasoning 2")
        ]
        mock_client.chat.completions.create.return_value = mock_decomposition
        
        context = AgentContext(
            query="Test query",
            agent_id="test-id",
            objective="Test objective",
            max_subagents=2
        )
        
        tasks = self.researcher._llm_decomposition(context)
        
        assert len(tasks) == 2
        assert tasks[0]["focus"] == "conceptual"
        assert tasks[1]["focus"] == "technical"
    
    @patch('openai.OpenAI')
    def test_advanced_ai_synthesis(self, mock_openai):
        """Testa síntese AI avançada"""
        # Mock do OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Synthesized result"
        mock_client.chat.completions.create.return_value = mock_response
        
        tasks = [{"query": "Test query"}]
        results = [{"result": "Test result"}]
        
        synthesis = self.researcher._advanced_ai_synthesis(tasks, results)
        
        assert synthesis is not None
        assert isinstance(synthesis, str)
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_plan_method(self):
        """Testa método de planejamento"""
        context = AgentContext(
            query="What is Zep temporal knowledge graph?",
            agent_id="test-id",
            objective="Research Zep",
            max_subagents=2
        )
        
        with patch.object(self.researcher, '_heuristic_decomposition') as mock_heuristic:
            mock_heuristic.return_value = [
                {"query": "Task 1", "focus": "conceptual"},
                {"query": "Task 2", "focus": "technical"}
            ]
            
            tasks = await self.researcher.plan(context)
            
            assert len(tasks) == 2
            assert tasks[0]["focus"] == "conceptual"
            assert tasks[1]["focus"] == "technical"


class TestEnhancedRAGSubagent:
    """Testes para RAG Subagent"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.subagent = RAGResearchSubagent(focus="technical")
    
    def test_subagent_initialization(self):
        """Testa inicialização do subagent"""
        assert self.subagent.focus == "technical"
        assert hasattr(self.subagent, 'rag_tool')
    
    @pytest.mark.asyncio
    async def test_subagent_run(self):
        """Testa execução do subagent"""
        task = ResearchTask(
            query="How to implement Zep?",
            focus="technical",
            reasoning="Technical implementation details needed"
        )
        
        context = AgentContext(
            query="How to implement Zep?",
            agent_id="test-id",
            objective="Technical research",
            max_subagents=1
        )
        
        with patch.object(self.subagent.rag_tool, 'search_documents') as mock_search:
            mock_search.return_value = {
                "documents": [{"content": "Test document", "similarity": 0.9}],
                "summary": "Test summary"
            }
            
            result = await self.subagent.run(context)
            
            assert result is not None
            assert "result" in result
            assert "focus" in result
            assert result["focus"] == "technical"


class TestMultiAgentIntegration:
    """Testes de integração do sistema multi-agente"""
    
    @pytest.mark.asyncio
    async def test_coordinator_subagent_integration(self):
        """Testa integração coordenador-subagente"""
        researcher = OpenAILeadResearcher()
        
        context = AgentContext(
            query="What is Zep?",
            agent_id="integration-test",
            objective="Test integration",
            max_subagents=2
        )
        
        # Mock dos subagentes
        with patch('multi_agent_researcher.src.researcher.agents.enhanced_rag_subagent.RAGResearchSubagent') as mock_subagent_class:
            mock_subagent = AsyncMock()
            mock_subagent.run.return_value = {
                "result": "Test result",
                "focus": "conceptual",
                "success": True
            }
            mock_subagent_class.return_value = mock_subagent
            
            # Mock da síntese
            with patch.object(researcher, '_advanced_ai_synthesis') as mock_synthesis:
                mock_synthesis.return_value = "Final synthesized result"
                
                # Simula execução completa
                tasks = await researcher.plan(context)
                assert len(tasks) >= 1
                
                # Testa que o reasoner foi usado
                assert len(researcher.reasoner.reasoning_history) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])