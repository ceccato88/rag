"""Tests for multimodal retriever agent."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from rag_agents.agents.retriever import (
    MultimodalRetrieverAgent, RetrieverConfig
)
from rag_agents.agents.base import AgentContext, AgentState
from rag_agents.models.rag_models import DocumentCandidate


class TestRetrieverConfig:
    """Test RetrieverConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RetrieverConfig()
        
        assert config.max_candidates == 5
        assert config.similarity_threshold == 0.7
        assert config.collection_name == "pdf_documents"
        assert config.voyage_api_key is None
        assert config.astra_db_endpoint is None
        assert config.astra_db_token is None
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetrieverConfig(
            max_candidates=10,
            similarity_threshold=0.8,
            collection_name="custom_docs",
            voyage_api_key="test_key",
            astra_db_endpoint="test_endpoint",
            astra_db_token="test_token"
        )
        
        assert config.max_candidates == 10
        assert config.similarity_threshold == 0.8
        assert config.collection_name == "custom_docs"
        assert config.voyage_api_key == "test_key"
        assert config.astra_db_endpoint == "test_endpoint"
        assert config.astra_db_token == "test_token"


class TestMultimodalRetrieverAgent:
    """Test MultimodalRetrieverAgent functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return RetrieverConfig(
            max_candidates=5,
            similarity_threshold=0.7,
            voyage_api_key="test_voyage_key",
            astra_db_endpoint="test_endpoint", 
            astra_db_token="test_token"
        )
    
    @pytest.fixture
    def mock_context(self):
        """Create test context."""
        return AgentContext(
            query="What are the main components of the Zep architecture?",
            objective="Understand Zep system architecture",
            constraints=["Focus on technical details"]
        )
    
    def test_agent_initialization(self, config):
        """Test agent initialization with config."""
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        
        assert agent.name == "TestRetriever"
        assert agent.config == config
        assert agent.state == AgentState.IDLE
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.retriever.voyageai.Client')
    @patch('rag_agents.agents.retriever.DataAPIClient')
    async def test_plan_creation(self, mock_astra, mock_voyage, config, mock_context):
        """Test planning phase."""
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        
        plan = await agent.plan(mock_context)
        
        assert isinstance(plan, dict)
        assert "query" in plan
        assert "max_candidates" in plan
        assert plan["query"] == mock_context.query
        assert plan["max_candidates"] == config.max_candidates
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.retriever.voyageai.Client')
    @patch('rag_agents.agents.retriever.DataAPIClient')
    async def test_successful_retrieval(self, mock_astra, mock_voyage, config, mock_context):
        """Test successful document retrieval."""
        # Setup mocks
        mock_voyage_client = Mock()
        mock_voyage.return_value = mock_voyage_client
        
        # Mock embedding response
        mock_voyage_client.multimodal_embed.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]]
        )
        
        # Mock Astra DB response
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_collection = Mock()
        mock_astra_client.get_collection.return_value = mock_collection
        
        # Mock search results
        mock_documents = [
            {
                "_id": "doc1",
                "content": "Document about Zep architecture components",
                "metadata": {"source": "zep_docs.pdf", "page": 1},
                "$similarity": 0.85
            },
            {
                "_id": "doc2", 
                "content": "Technical details about Zep system design",
                "metadata": {"source": "zep_tech.pdf", "page": 5},
                "$similarity": 0.78
            }
        ]
        
        mock_collection.find = AsyncMock(return_value=mock_documents)
        
        # Create agent and run
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        result = await agent.run(mock_context)
        
        # Verify results
        assert result.status == AgentState.COMPLETED
        assert isinstance(result.output, list)
        assert len(result.output) == 2
        
        # Check first document
        doc1 = result.output[0]
        assert isinstance(doc1, DocumentCandidate)
        assert doc1.document_id == "doc1"
        assert "Zep architecture" in doc1.content
        assert doc1.similarity_score == 0.85
        assert doc1.metadata["source"] == "zep_docs.pdf"
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.retriever.voyageai.Client')
    @patch('rag_agents.agents.retriever.DataAPIClient')
    async def test_no_documents_found(self, mock_astra, mock_voyage, config, mock_context):
        """Test behavior when no documents are found."""
        # Setup mocks
        mock_voyage_client = Mock()
        mock_voyage.return_value = mock_voyage_client
        mock_voyage_client.multimodal_embed.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3]]
        )
        
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_collection = Mock()
        mock_astra_client.get_collection.return_value = mock_collection
        mock_collection.find = AsyncMock(return_value=[])
        
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.COMPLETED
        assert isinstance(result.output, list)
        assert len(result.output) == 0
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.retriever.voyageai.Client')
    @patch('rag_agents.agents.retriever.DataAPIClient')
    async def test_voyage_api_error(self, mock_astra, mock_voyage, config, mock_context):
        """Test handling of Voyage API errors."""
        # Setup mock to raise exception
        mock_voyage_client = Mock()
        mock_voyage.return_value = mock_voyage_client
        mock_voyage_client.multimodal_embed.side_effect = Exception("Voyage API error")
        
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.FAILED
        assert "Voyage API error" in result.error
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.retriever.voyageai.Client')
    @patch('rag_agents.agents.retriever.DataAPIClient')
    async def test_astra_db_error(self, mock_astra, mock_voyage, config, mock_context):
        """Test handling of Astra DB errors."""
        # Setup mocks
        mock_voyage_client = Mock()
        mock_voyage.return_value = mock_voyage_client
        mock_voyage_client.multimodal_embed.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3]]
        )
        
        # Make Astra DB raise exception
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_astra_client.get_collection.side_effect = Exception("Astra DB connection error")
        
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        result = await agent.run(mock_context)
        
        assert result.status == AgentState.FAILED
        assert "Astra DB connection error" in result.error
    
    @pytest.mark.asyncio
    @patch('rag_agents.agents.retriever.voyageai.Client')
    @patch('rag_agents.agents.retriever.DataAPIClient')
    async def test_similarity_threshold_filtering(self, mock_astra, mock_voyage, mock_context):
        """Test that documents below similarity threshold are filtered out."""
        config = RetrieverConfig(
            similarity_threshold=0.8,  # High threshold
            voyage_api_key="test_key",
            astra_db_endpoint="test_endpoint",
            astra_db_token="test_token"
        )
        
        # Setup mocks
        mock_voyage_client = Mock()
        mock_voyage.return_value = mock_voyage_client
        mock_voyage_client.multimodal_embed.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3]]
        )
        
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_collection = Mock()
        mock_astra_client.get_collection.return_value = mock_collection
        
        # Mock documents with various similarity scores
        mock_documents = [
            {
                "_id": "doc1",
                "content": "High relevance document",
                "metadata": {},
                "$similarity": 0.9  # Above threshold
            },
            {
                "_id": "doc2",
                "content": "Low relevance document", 
                "metadata": {},
                "$similarity": 0.7  # Below threshold
            },
            {
                "_id": "doc3",
                "content": "Medium relevance document",
                "metadata": {},
                "$similarity": 0.85  # Above threshold
            }
        ]
        
        mock_collection.find = AsyncMock(return_value=mock_documents)
        
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        result = await agent.run(mock_context)
        
        # Should only return documents above threshold
        assert result.status == AgentState.COMPLETED
        assert len(result.output) == 2  # Only doc1 and doc3
        assert all(doc.similarity_score >= 0.8 for doc in result.output)
    
    @pytest.mark.asyncio
    async def test_missing_configuration(self):
        """Test behavior with missing configuration."""
        config = RetrieverConfig()  # Missing API keys
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        
        context = AgentContext(
            query="test query",
            objective="test objective"
        )
        
        result = await agent.run(context)
        assert result.status == AgentState.FAILED
        assert "configuration" in result.error.lower() or "api" in result.error.lower()
    
    def test_document_candidate_creation(self, config):
        """Test DocumentCandidate creation from raw data."""
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        
        raw_doc = {
            "_id": "test_doc_123",
            "content": "This is test document content with technical details.",
            "metadata": {
                "source": "technical_manual.pdf",
                "page": 42,
                "section": "Architecture"
            },
            "$similarity": 0.85
        }
        
        doc_candidate = agent._create_document_candidate(raw_doc)
        
        assert isinstance(doc_candidate, DocumentCandidate)
        assert doc_candidate.document_id == "test_doc_123"
        assert doc_candidate.content == "This is test document content with technical details."
        assert doc_candidate.metadata["source"] == "technical_manual.pdf"
        assert doc_candidate.metadata["page"] == 42
        assert doc_candidate.similarity_score == 0.85
        assert doc_candidate.content_type == "text"  # Default
    
    def test_content_type_detection(self, config):
        """Test content type detection logic."""
        agent = MultimodalRetrieverAgent(config=config, name="TestRetriever")
        
        # Test text content
        text_doc = {
            "_id": "text_doc",
            "content": "Pure text content without any visual elements.",
            "metadata": {},
            "$similarity": 0.8
        }
        
        doc = agent._create_document_candidate(text_doc)
        assert doc.content_type == "text"
        
        # Test content with image indicators
        image_doc = {
            "_id": "image_doc", 
            "content": "Document with diagram and figure references.",
            "metadata": {"has_images": True},
            "$similarity": 0.8
        }
        
        doc = agent._create_document_candidate(image_doc)
        # Implementation should detect visual content
        # This would need actual implementation to test properly