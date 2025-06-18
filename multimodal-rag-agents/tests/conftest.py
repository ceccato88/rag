"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    client.chat.completions.create = Mock()
    return client


@pytest.fixture  
def mock_voyage_client():
    """Mock Voyage AI client for testing."""
    client = Mock()
    client.multimodal_embed = Mock()
    return client


@pytest.fixture
def mock_astra_client():
    """Mock Astra DB client for testing."""
    client = Mock()
    collection = Mock()
    client.get_collection.return_value = collection
    return client, collection


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "_id": "doc_001",
            "content": "This is a sample document about AI architecture. It contains technical details about system components and their interactions.",
            "metadata": {
                "source": "ai_architecture.pdf",
                "page": 1,
                "section": "Introduction",
                "has_images": True
            },
            "$similarity": 0.9
        },
        {
            "_id": "doc_002", 
            "content": "Another document discussing machine learning models and their implementation in production systems.",
            "metadata": {
                "source": "ml_production.pdf",
                "page": 5,
                "section": "Implementation",
                "has_images": False
            },
            "$similarity": 0.8
        },
        {
            "_id": "doc_003",
            "content": "Technical documentation about vector databases and embedding techniques for semantic search.",
            "metadata": {
                "source": "vector_db_guide.pdf",
                "page": 12,
                "section": "Vector Search",
                "has_images": True
            },
            "$similarity": 0.75
        }
    ]


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    env_content = """
# Test environment configuration
OPENAI_API_KEY=test_openai_key_12345
VOYAGE_API_KEY=test_voyage_key_67890
ASTRA_DB_API_ENDPOINT=https://test-db-id.apps.astra.datastax.com
ASTRA_DB_APPLICATION_TOKEN=AstraCS:test_application_token
COLLECTION_NAME=test_documents
IMAGE_DIR=test_images
LLM_MODEL=gpt-4o
MAX_CANDIDATES=5
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_environment_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test_openai_key",
        "VOYAGE_API_KEY": "test_voyage_key", 
        "ASTRA_DB_API_ENDPOINT": "https://test.astra.datastax.com",
        "ASTRA_DB_APPLICATION_TOKEN": "AstraCS:test_token",
        "COLLECTION_NAME": "test_collection",
        "IMAGE_DIR": "test_images"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_query_context():
    """Sample query context for testing."""
    from rag_agents.agents.base import AgentContext
    
    return AgentContext(
        query="What are the key components of a multimodal RAG system?",
        objective="Understand the architecture and components of multimodal RAG systems",
        constraints=[
            "Focus on technical implementation",
            "Include visual processing capabilities",
            "Explain component interactions"
        ],
        metadata={
            "query_type": "technical",
            "complexity": "medium",
            "expected_response_length": "detailed"
        }
    )


@pytest.fixture
def sample_rag_decomposition():
    """Sample RAG decomposition for testing."""
    from rag_agents.models.rag_models import (
        RAGDecomposition, SearchStrategy, RankingCriterion
    )
    
    return RAGDecomposition(
        query_type="technical_analysis",
        key_aspects=["architecture", "components", "multimodal_processing"],
        search_strategies=[
            SearchStrategy(
                primary_queries=["multimodal RAG architecture", "RAG system components"],
                fallback_queries=["retrieval augmented generation", "multimodal AI systems"],
                content_filters=["technical", "architecture", "implementation"],
                max_candidates=5
            )
        ],
        ranking_criteria=[
            RankingCriterion(
                aspect="technical_depth",
                weight=0.4,
                evaluation_method="content_analysis"
            ),
            RankingCriterion(
                aspect="relevance_to_multimodal",
                weight=0.3,
                evaluation_method="semantic_similarity"
            ),
            RankingCriterion(
                aspect="implementation_details",
                weight=0.3,
                evaluation_method="keyword_matching"
            )
        ],
        visual_requirements=["architecture_diagrams", "component_flows"],
        response_format="detailed_technical_explanation"
    )


@pytest.fixture
def sample_document_candidates():
    """Sample document candidates for testing."""
    from rag_agents.models.rag_models import DocumentCandidate
    
    return [
        DocumentCandidate(
            doc_id="multimodal_rag_001",
            file_path="/path/to/multimodal_ai.pdf",
            page_num=3,
            doc_source="multimodal_ai.pdf",
            markdown_text="Multimodal RAG systems integrate text and visual processing capabilities to provide comprehensive retrieval and generation. The architecture typically includes separate encoders for different modalities.",
            similarity_score=0.92,
            visual_content_type="text_with_diagrams"
        ),
        DocumentCandidate(
            doc_id="rag_components_002",
            file_path="/path/to/rag_fundamentals.pdf",
            page_num=7,
            doc_source="rag_fundamentals.pdf",
            markdown_text="The key components of a RAG system include the retrieval mechanism, the knowledge base, and the generation model. Each component plays a crucial role in the overall system performance.",
            similarity_score=0.87,
            visual_content_type=None
        ),
        DocumentCandidate(
            doc_id="visual_processing_003",
            file_path="/path/to/visual_ai_processing.pdf",
            page_num=15,
            doc_source="visual_ai_processing.pdf",
            markdown_text="Visual processing in RAG systems requires specialized encoders that can handle images, diagrams, and charts. Integration with text processing creates powerful multimodal capabilities.",
            similarity_score=0.84,
            visual_content_type="text_with_images"
        )
    ]


@pytest.fixture
def sample_structured_answer():
    """Sample structured answer for testing."""
    from rag_agents.models.rag_models import StructuredAnswer, SourceCitation
    
    return StructuredAnswer(
        main_response="""A multimodal RAG system consists of several key components working together:

1. **Multimodal Encoder**: Processes both text and visual content (images, diagrams, charts)
2. **Vector Database**: Stores embeddings for efficient similarity search across modalities  
3. **Retrieval Engine**: Finds relevant documents based on semantic similarity
4. **Context Processor**: Analyzes and filters retrieved content for relevance
5. **Generation Model**: Creates responses incorporating both textual and visual information

These components work together to enable comprehensive understanding and generation capabilities that go beyond traditional text-only RAG systems.""",
        sources_used=[
            SourceCitation(
                document="multimodal_ai.pdf",
                page_number=3,
                content_type="text_with_diagrams",
                excerpt="The architecture typically includes separate encoders for different modalities."
            ),
            SourceCitation(
                document="rag_fundamentals.pdf",
                page_number=7,
                content_type="text",
                excerpt="The key components include the retrieval mechanism, knowledge base, and generation model."
            )
        ],
        multimodal_confidence=0.89,
        evidence_strength="strong",
        visual_elements_used=["architecture_diagram", "component_flowchart"],
        limitations=["Limited coverage of latest embedding techniques"],
        follow_up_suggestions=[
            "Explore specific implementation frameworks",
            "Review performance benchmarks for multimodal systems"
        ]
    )


# Pytest markers for organizing tests
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