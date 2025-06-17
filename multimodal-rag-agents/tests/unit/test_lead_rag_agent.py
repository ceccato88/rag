"""Tests for lead RAG agent."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from rag_agents.agents.lead_rag import LeadRAGAgent, LeadRAGConfig
from rag_agents.agents.base import AgentContext, AgentState
from rag_agents.models.rag_models import (
    RAGDecomposition, SearchStrategy, RankingCriterion,
    DocumentCandidate, RankedDocuments, ContextAnalysis,
    StructuredAnswer, RAGResult
)


class MockSubAgent:
    """Mock sub-agent for testing."""
    
    def __init__(self, name, output_data):
        self.name = name
        self.output_data = output_data
        
    async def run(self, context):
        """Mock run method."""
        result = Mock()
        result.status = AgentState.COMPLETED
        result.output = self.output_data
        result.thinking = [f"{self.name} thinking"]
        result.processing_steps = []
        result.tokens_used = 100
        result.error = None
        return result


class TestLeadRAGConfig:
    """Test LeadRAGConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LeadRAGConfig(openai_api_key="test_key")
        
        assert config.openai_api_key == "test_key"
        assert config.model == "gpt-4o"
        assert config.max_tokens == 2048
        assert config.temperature == 0.1
        assert config.timeout == 300.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = LeadRAGConfig(
            openai_api_key="test_key",
            model="gpt-4-turbo",
            max_tokens=1024,
            temperature=0.2,
            timeout=600.0
        )
        
        assert config.model == "gpt-4-turbo"
        assert config.max_tokens == 1024
        assert config.temperature == 0.2
        assert config.timeout == 600.0


class TestLeadRAGAgent:
    """Test LeadRAGAgent functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return LeadRAGConfig(openai_api_key="test_openai_key")
    
    @pytest.fixture
    def mock_context(self):
        """Create test context."""
        return AgentContext(
            query="What are the main components of the Zep architecture?",
            objective="Understand Zep system architecture with visual elements",
            constraints=["Focus on technical details", "Include diagrams"]
        )
    
    @pytest.fixture
    def mock_sub_agents(self):
        """Create mock sub-agents."""
        # Mock retriever output
        retriever_output = [
            DocumentCandidate(
                document_id="doc1",
                content="Zep architecture consists of memory layers...",
                metadata={"source": "zep_docs.pdf", "page": 1},
                similarity_score=0.9,
                content_type="text_with_diagrams"
            ),
            DocumentCandidate(
                document_id="doc2",
                content="The system includes vector storage...",
                metadata={"source": "zep_tech.pdf", "page": 5},
                similarity_score=0.8,
                content_type="text"
            )
        ]
        
        # Mock reranker output
        reranker_output = RankedDocuments(
            documents=retriever_output,
            ranking_explanation="Ranked by technical relevance and visual content",
            diversity_score=0.7,
            total_candidates_considered=5
        )
        
        # Mock context analyzer output
        context_output = ContextAnalysis(
            completeness_score=0.8,
            confidence_level="high",
            information_gaps=["missing performance metrics"],
            context_conflicts=[],
            visual_coverage=0.6,
            recommended_action="proceed_with_answer"
        )
        
        # Mock answer generator output
        answer_output = StructuredAnswer(
            main_response="The Zep architecture consists of three main components: memory layers, vector storage, and API interfaces...",
            sources_used=[],
            multimodal_confidence=0.85,
            evidence_strength="strong",
            visual_elements_used=["architecture_diagram"],
            limitations=["Limited recent performance data"],
            follow_up_suggestions=["Check latest performance benchmarks"]
        )
        
        return {
            'retriever': MockSubAgent("Retriever", retriever_output),
            'reranker': MockSubAgent("Reranker", reranker_output),
            'context_analyzer': MockSubAgent("ContextAnalyzer", context_output),
            'answer_generator': MockSubAgent("AnswerGenerator", answer_output)
        }
    
    def test_agent_initialization(self, config, mock_sub_agents):
        """Test agent initialization with sub-agents."""
        agent = LeadRAGAgent(
            retriever_agent=mock_sub_agents['retriever'],
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        assert agent.name == "TestLeadRAG"
        assert agent.config == config
        assert agent.retriever_agent == mock_sub_agents['retriever']
        assert agent.reranker_agent == mock_sub_agents['reranker']
        assert agent.context_analyzer_agent == mock_sub_agents['context_analyzer']
        assert agent.answer_generator_agent == mock_sub_agents['answer_generator']
        assert agent.state == AgentState.IDLE
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_plan_creation(self, mock_instructor, config, mock_sub_agents, mock_context):
        """Test planning phase with query decomposition."""
        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client
        
        # Mock decomposition response
        mock_decomposition = RAGDecomposition(
            query_type="technical_architecture",
            key_aspects=["components", "data_flow", "integrations"],
            search_strategies=[
                SearchStrategy(
                    primary_queries=["Zep architecture components"],
                    fallback_queries=["Zep system design"],
                    content_filters=["technical", "diagrams"],
                    max_candidates=5
                )
            ],
            ranking_criteria=[
                RankingCriterion(
                    aspect="technical_depth",
                    weight=0.8,
                    evaluation_method="content_analysis"
                )
            ],
            visual_requirements=["architecture_diagrams", "flowcharts"],
            response_format="detailed_technical"
        )
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_decomposition)
        
        agent = LeadRAGAgent(
            retriever_agent=mock_sub_agents['retriever'],
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        plan = await agent.plan(mock_context)
        
        assert isinstance(plan, RAGDecomposition)
        assert plan.query_type == "technical_architecture"
        assert "components" in plan.key_aspects
        assert len(plan.search_strategies) == 1
        assert "technical" in plan.search_strategies[0].content_filters
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_successful_execution(self, mock_instructor, config, mock_sub_agents, mock_context):
        """Test successful end-to-end execution."""
        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client
        
        # Mock decomposition
        mock_decomposition = RAGDecomposition(
            query_type="technical",
            key_aspects=["architecture"],
            search_strategies=[SearchStrategy(primary_queries=["test"])],
            ranking_criteria=[],
            visual_requirements=[],
            response_format="detailed"
        )
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_decomposition)
        
        agent = LeadRAGAgent(
            retriever_agent=mock_sub_agents['retriever'],
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.COMPLETED
        assert isinstance(result.output, RAGResult)
        
        rag_result = result.output
        assert isinstance(rag_result.query_decomposition, RAGDecomposition)
        assert isinstance(rag_result.ranked_documents, RankedDocuments)
        assert isinstance(rag_result.context_analysis, ContextAnalysis)
        assert isinstance(rag_result.answer, StructuredAnswer)
        assert len(rag_result.processing_steps) >= 4  # At least 4 agents
        assert rag_result.total_tokens_used > 0
        assert rag_result.total_processing_time > 0
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_retriever_failure(self, mock_instructor, config, mock_sub_agents, mock_context):
        """Test handling of retriever agent failure."""
        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client
        
        mock_decomposition = RAGDecomposition(
            query_type="technical",
            key_aspects=["test"],
            search_strategies=[SearchStrategy(primary_queries=["test"])],
            ranking_criteria=[],
            visual_requirements=[],
            response_format="detailed"
        )
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_decomposition)
        
        # Make retriever fail
        failing_retriever = Mock()
        failing_retriever.run = AsyncMock(side_effect=Exception("Retriever failed"))
        
        agent = LeadRAGAgent(
            retriever_agent=failing_retriever,
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.FAILED
        assert "Retriever failed" in result.error
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_context_analysis_recommends_more_search(self, mock_instructor, config, mock_sub_agents, mock_context):
        """Test handling when context analyzer recommends more search."""
        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client
        
        mock_decomposition = RAGDecomposition(
            query_type="technical",
            key_aspects=["test"],
            search_strategies=[SearchStrategy(primary_queries=["test"])],
            ranking_criteria=[],
            visual_requirements=[],
            response_format="detailed"
        )
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_decomposition)
        
        # Mock context analyzer to recommend more search
        insufficient_context = ContextAnalysis(
            completeness_score=0.3,  # Low score
            confidence_level="low",
            information_gaps=["missing key information"],
            context_conflicts=[],
            visual_coverage=0.1,
            recommended_action="search_more"  # Recommends more search
        )
        
        mock_sub_agents['context_analyzer'].output_data = insufficient_context
        
        agent = LeadRAGAgent(
            retriever_agent=mock_sub_agents['retriever'],
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        result = await agent.run(mock_context)
        
        # Should still complete but with partial answer
        assert result.status == AgentState.COMPLETED
        rag_result = result.output
        assert rag_result.context_analysis.recommended_action == "search_more"
        assert rag_result.context_analysis.completeness_score == 0.3
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_no_documents_retrieved(self, mock_instructor, config, mock_sub_agents, mock_context):
        """Test handling when no documents are retrieved."""
        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client
        
        mock_decomposition = RAGDecomposition(
            query_type="technical",
            key_aspects=["test"],
            search_strategies=[SearchStrategy(primary_queries=["test"])],
            ranking_criteria=[],
            visual_requirements=[],
            response_format="detailed"
        )
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_decomposition)
        
        # Mock retriever to return no documents
        mock_sub_agents['retriever'].output_data = []
        
        # Mock reranker to return empty ranked documents
        empty_ranked = RankedDocuments(
            documents=[],
            ranking_explanation="No documents to rank",
            diversity_score=0.0,
            total_candidates_considered=0
        )
        mock_sub_agents['reranker'].output_data = empty_ranked
        
        # Mock context analyzer for empty context
        empty_context = ContextAnalysis(
            completeness_score=0.0,
            confidence_level="none",
            information_gaps=["no information available"],
            context_conflicts=[],
            visual_coverage=0.0,
            recommended_action="no_answer_possible"
        )
        mock_sub_agents['context_analyzer'].output_data = empty_context
        
        # Mock answer generator for no context
        no_answer = StructuredAnswer(
            main_response="I don't have sufficient information to answer your question comprehensively.",
            sources_used=[],
            multimodal_confidence=0.0,
            evidence_strength="none",
            visual_elements_used=[],
            limitations=["No relevant documents found"],
            follow_up_suggestions=["Try rephrasing the query", "Check if documents are indexed"]
        )
        mock_sub_agents['answer_generator'].output_data = no_answer
        
        agent = LeadRAGAgent(
            retriever_agent=mock_sub_agents['retriever'],
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.COMPLETED
        rag_result = result.output
        assert len(rag_result.ranked_documents.documents) == 0
        assert rag_result.context_analysis.completeness_score == 0.0
        assert "don't have sufficient information" in rag_result.answer.main_response
    
    @pytest.mark.asyncio
    async def test_missing_openai_key(self, mock_sub_agents, mock_context):
        """Test behavior with missing OpenAI API key."""
        config = LeadRAGConfig(openai_api_key="")  # Empty key
        
        agent = LeadRAGAgent(
            retriever_agent=mock_sub_agents['retriever'],
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.FAILED
        assert "api key" in result.error.lower()
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_token_tracking(self, mock_instructor, config, mock_sub_agents, mock_context):
        """Test that token usage is properly tracked."""
        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client
        
        mock_decomposition = RAGDecomposition(
            query_type="technical",
            key_aspects=["test"],
            search_strategies=[SearchStrategy(primary_queries=["test"])],
            ranking_criteria=[],
            visual_requirements=[],
            response_format="detailed"
        )
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_decomposition)
        
        agent = LeadRAGAgent(
            retriever_agent=mock_sub_agents['retriever'],
            reranker_agent=mock_sub_agents['reranker'],
            context_analyzer_agent=mock_sub_agents['context_analyzer'],
            answer_generator_agent=mock_sub_agents['answer_generator'],
            config=config,
            name="TestLeadRAG"
        )
        
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.COMPLETED
        assert result.tokens_used > 0
        
        rag_result = result.output
        assert rag_result.total_tokens_used > 0
        # Should include tokens from lead agent + all sub-agents
        assert rag_result.total_tokens_used >= 400  # 4 sub-agents * 100 tokens each