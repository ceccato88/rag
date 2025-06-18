"""Test configuration and fixtures."""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import all config classes
from rag_agents.agents.retriever import RetrieverConfig
from rag_agents.agents.reranker import RerankerConfig
from rag_agents.agents.context_analyzer import ContextAnalyzerConfig
from rag_agents.agents.answer_generator import AnswerGeneratorConfig
from rag_agents.agents.lead_rag import LeadRAGConfig
from rag_agents.agents.base import AgentContext, AgentState
from rag_agents.models.rag_models import (
    DocumentCandidate, RankedDocuments, RankingAnalysis, 
    ContextAnalysis, StructuredAnswer, RAGDecomposition, SearchStrategy
)


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "mock: mark test as using mocked services"
    )

@pytest.fixture
def mock_context():
    """Mock agent context."""
    return AgentContext(
        query="What is machine learning?",
        objective="Provide comprehensive information about machine learning"
    )


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        DocumentCandidate(
            id="doc1",
            content="Machine learning is a subset of artificial intelligence.",
            metadata={"page": 1, "source": "test.pdf"},
            score=0.95
        ),
        DocumentCandidate(
            id="doc2", 
            content="Deep learning uses neural networks with multiple layers.",
            metadata={"page": 2, "source": "test.pdf"},
            score=0.88
        ),
        DocumentCandidate(
            id="doc3",
            content="Supervised learning requires labeled training data.",
            metadata={"page": 3, "source": "test.pdf"},
            score=0.82
        )
    ]


@pytest.fixture
def mock_ranked_documents(sample_documents):
    """Mock ranked documents."""
    return RankedDocuments(
        documents=sample_documents,
        ranking_analysis=RankingAnalysis(
            ranking_rationale="Documents ranked by relevance to machine learning query",
            confidence_score=0.9,
            ranking_factors=["semantic similarity", "content quality", "source reliability"]
        ),
        total_candidates=10,
        processing_time=0.5
    )


@pytest.fixture
def mock_context_analysis():
    """Mock context analysis."""
    return ContextAnalysis(
        query_complexity="medium",
        domain_areas=["machine learning", "artificial intelligence"],
        information_gaps=["practical examples", "recent developments"],
        user_intent="educational",
        required_detail_level="comprehensive",
        suggested_structure=["definition", "types", "applications", "examples"],
        confidence_score=0.85,
        processing_notes=["Query is well-formed and specific"]
    )


@pytest.fixture  
def mock_structured_answer():
    """Mock structured answer."""
    return StructuredAnswer(
        main_response="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
        key_points=[
            "Machine learning is part of AI",
            "Learns from data and experience", 
            "Improves performance over time",
            "Doesn't require explicit programming"
        ],
        supporting_evidence=[
            "According to the documents, machine learning algorithms can identify patterns in data",
            "Deep learning, a subset of ML, uses neural networks"
        ],
        confidence_level="high",
        limitations=["Limited to available training data", "May have biases"],
        related_topics=["artificial intelligence", "deep learning", "neural networks"],
        sources_used=["doc1", "doc2", "doc3"],
        processing_notes=["Answer synthesized from multiple relevant sources"]
    )


@pytest.fixture
def mock_rag_decomposition():
    """Mock RAG decomposition."""
    return RAGDecomposition(
        query_type="informational",
        key_aspects=["definition", "types", "applications"],
        search_strategies=[
            SearchStrategy(
                primary_queries=["machine learning definition", "types of machine learning"],
                secondary_queries=["ML applications", "ML vs AI"],
                visual_queries=["ML diagram", "ML workflow"]
            )
        ],
        ranking_criteria=[
            "relevance to query",
            "source credibility", 
            "content freshness"
        ],
        visual_requirements=["diagrams", "flowcharts"],
        response_format="comprehensive"
    )

@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    return datetime.now(timezone.utc)