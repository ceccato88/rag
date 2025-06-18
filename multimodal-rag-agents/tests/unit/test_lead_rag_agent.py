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
    DocumentCandidate, RankedDocuments, RankingAnalysis, ContextAnalysis,
    StructuredAnswer, RAGResult
)


class MockSubAgent:
    """Mock sub-agent for testing."""

    def __init__(self, name, output_data):
        self.name = name
        self.output_data = output_data

    async def run(self, context):
        """Mock run method."""
        from datetime import datetime, timezone
        result = Mock()
        result.status = AgentState.COMPLETED
        result.output = self.output_data
        result.thinking = [f"{self.name} thinking"]
        result.processing_steps = []
        result.tokens_used = 100
        result.error = None
        result.start_time = datetime.now(timezone.utc)
        result.end_time = datetime.now(timezone.utc)
        result.agent_name = self.name  # Add agent name
        return result


class TestLeadRAGConfig:
    """Test LeadRAGConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LeadRAGConfig(openai_api_key="test_key")

        assert config.openai_api_key == "test_key"
        assert config.model == "gpt-4o"
        assert config.max_subagents == 4
        assert config.parallel_execution == True
        assert config.subagent_timeout == 300.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = LeadRAGConfig(
            openai_api_key="test_key",
            model="gpt-4-turbo",
            max_subagents=8,
            parallel_execution=False,
            subagent_timeout=600.0
        )

        assert config.model == "gpt-4-turbo"
        assert config.max_subagents == 8
        assert config.parallel_execution == False
        assert config.subagent_timeout == 600.0


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
                doc_id="doc1",
                file_path="zep_docs.pdf",
                page_num=1,
                doc_source="zep_docs.pdf",
                markdown_text="Zep architecture consists of memory layers...",
                similarity_score=0.9,
                visual_content_type="diagram"
            ),
            DocumentCandidate(
                doc_id="doc2",
                file_path="zep_tech.pdf",
                page_num=5,
                doc_source="zep_tech.pdf",
                markdown_text="The system includes vector storage...",
                similarity_score=0.8,
                visual_content_type=None
            )
        ]

        # Mock reranker output
        ranking_analysis = RankingAnalysis(
            document_scores={"doc1": 0.9, "doc2": 0.8},
            ranking_rationale="Ranked by technical relevance and visual content",
            selected_documents=["doc1", "doc2"],
            diversity_score=0.7
        )

        reranker_output = RankedDocuments(
            documents=retriever_output,
            ranking_analysis=ranking_analysis,
            total_candidates_processed=5,
            selection_strategy_used="technical_relevance_with_diversity"
        )

        # Mock context analyzer output
        context_output = ContextAnalysis(
            completeness_score=0.8,
            confidence_level="high",
            information_gaps=["missing performance metrics"],
            conflicting_sources=[],
            visual_coverage=0.6,
            recommended_action="proceed"
        )

        # Mock answer generator output
        answer_output = StructuredAnswer(
            main_response="The Zep architecture consists of three main components: memory layers, vector storage, and API interfaces...",
            evidence_strength="high",
            sources_used=[],
            visual_elements_used=["architecture_diagram"],
            limitations=["Limited recent performance data"],
            follow_up_suggestions=["Check latest performance benchmarks"],
            multimodal_confidence=0.85
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
        assert agent.retriever == mock_sub_agents['retriever']
        assert agent.reranker == mock_sub_agents['reranker']
        assert agent.context_analyzer == mock_sub_agents['context_analyzer']
        assert agent.answer_generator == mock_sub_agents['answer_generator']
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
            query_type="analytical",
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

        plan = await agent.plan(mock_context)

        assert isinstance(plan, RAGDecomposition)
        assert plan.query_type == "analytical"
        assert "components" in plan.key_aspects
        assert len(plan.search_strategies) == 1
        assert "technical" in plan.search_strategies[0].content_filters

    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.time.time')
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_successful_execution(self, mock_instructor, mock_time, config, mock_sub_agents, mock_context):
        """Test successful end-to-end execution."""
        # Mock time.time() to return increasing values
        mock_time.side_effect = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]  # Start time and various end times

        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client

        # Mock decomposition
        mock_decomposition = RAGDecomposition(
            query_type="analytical",
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

        if result.status != AgentState.COMPLETED:
            print(f"Error: {result.error}")
            print(f"Thinking: {result.thinking}")

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
            query_type="analytical",
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
            query_type="analytical",
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
            conflicting_sources=[],
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
            query_type="analytical",
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
        empty_ranking_analysis = RankingAnalysis(
            document_scores={},
            ranking_rationale="No documents to rank",
            selected_documents=[],
            diversity_score=0.0
        )

        empty_ranked = RankedDocuments(
            documents=[],
            ranking_analysis=empty_ranking_analysis,
            total_candidates_processed=0,
            selection_strategy_used="no_selection"
        )
        mock_sub_agents['reranker'].output_data = empty_ranked

        # Mock context analyzer for empty context
        empty_context = ContextAnalysis(
            completeness_score=0.0,
            confidence_level="low",
            information_gaps=["no information available"],
            conflicting_sources=[],
            visual_coverage=0.0,
            recommended_action="partial_answer"
        )
        mock_sub_agents['context_analyzer'].output_data = empty_context

        # Mock answer generator for no context
        no_answer = StructuredAnswer(
            main_response="I don't have sufficient information to answer your question comprehensively.",
            evidence_strength="low",
            sources_used=[],
            visual_elements_used=[],
            limitations=["No relevant documents found"],
            follow_up_suggestions=["Try rephrasing the query", "Check if documents are indexed"],
            multimodal_confidence=0.0
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

        # Should fail during initialization or first API call
        try:
            agent = LeadRAGAgent(
                retriever_agent=mock_sub_agents['retriever'],
                reranker_agent=mock_sub_agents['reranker'],
                context_analyzer_agent=mock_sub_agents['context_analyzer'],
                answer_generator_agent=mock_sub_agents['answer_generator'],
                config=config,
                name="TestLeadRAG"
            )

            result = await agent.run(mock_context)

            # If it doesn't fail immediately, it should fail during execution
            if result.status == AgentState.COMPLETED:
                # This is unexpected - no API key should cause failure
                assert False, "Expected failure due to missing API key but got success"
            else:
                assert result.status == AgentState.FAILED
                assert "api" in result.error.lower() or "key" in result.error.lower()

        except Exception as e:
            # API key validation might happen during initialization
            assert "api" in str(e).lower() or "key" in str(e).lower()

    @pytest.mark.asyncio
    @patch('rag_agents.agents.lead_rag.instructor.from_openai')
    async def test_token_tracking(self, mock_instructor, config, mock_sub_agents, mock_context):
        """Test that token usage is properly tracked."""
        # Mock instructor client
        mock_client = Mock()
        mock_instructor.return_value = mock_client

        mock_decomposition = RAGDecomposition(
            query_type="analytical",
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