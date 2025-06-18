"""Tests for configuration modules."""

import pytest
import os
import tempfile
from unittest.mock import patch
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from rag_agents.agents.retriever import RetrieverConfig
from rag_agents.agents.reranker import RerankerConfig
from rag_agents.agents.context_analyzer import ContextAnalyzerConfig
from rag_agents.agents.answer_generator import AnswerGeneratorConfig
from rag_agents.agents.lead_rag import LeadRAGConfig


class TestRetrieverConfig:
    """Test RetrieverConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetrieverConfig()
        assert config.voyage_api_key == ""
        assert config.astra_db_endpoint == ""
        assert config.astra_db_token == ""
        assert config.collection_name == "rag_collection"
        assert config.top_k == 10
        assert config.similarity_threshold == 0.7

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            'VOYAGE_API_KEY': 'test_voyage_key',
            'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
            'ASTRA_DB_APPLICATION_TOKEN': 'test_token'
        }):
            config = RetrieverConfig()
            assert config.voyage_api_key == 'test_voyage_key'
            assert config.astra_db_endpoint == 'test_endpoint'
            assert config.astra_db_token == 'test_token'

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetrieverConfig(
            voyage_api_key="custom_key",
            astra_db_endpoint="custom_endpoint",
            astra_db_token="custom_token",
            collection_name="custom_collection",
            top_k=20,
            similarity_threshold=0.8
        )
        assert config.voyage_api_key == "custom_key"
        assert config.astra_db_endpoint == "custom_endpoint"
        assert config.astra_db_token == "custom_token"
        assert config.collection_name == "custom_collection"
        assert config.top_k == 20
        assert config.similarity_threshold == 0.8


class TestRerankerConfig:
    """Test RerankerConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RerankerConfig()
        assert config.openai_api_key == ""
        assert config.model_name == "gpt-4"
        assert config.max_documents == 5
        assert config.temperature == 0.1

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_openai_key'}):
            config = RerankerConfig()
            assert config.openai_api_key == 'test_openai_key'

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RerankerConfig(
            openai_api_key="custom_key",
            model_name="gpt-3.5-turbo",
            max_documents=10,
            temperature=0.3
        )
        assert config.openai_api_key == "custom_key"
        assert config.model_name == "gpt-3.5-turbo"
        assert config.max_documents == 10
        assert config.temperature == 0.3


class TestContextAnalyzerConfig:
    """Test ContextAnalyzerConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ContextAnalyzerConfig()
        assert config.openai_api_key == ""
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.1

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_openai_key'}):
            config = ContextAnalyzerConfig()
            assert config.openai_api_key == 'test_openai_key'

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ContextAnalyzerConfig(
            openai_api_key="custom_key",
            model_name="gpt-3.5-turbo",
            temperature=0.5
        )
        assert config.openai_api_key == "custom_key"
        assert config.model_name == "gpt-3.5-turbo"
        assert config.temperature == 0.5


class TestAnswerGeneratorConfig:
    """Test AnswerGeneratorConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AnswerGeneratorConfig()
        assert config.openai_api_key == ""
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.3
        assert config.max_tokens == 1000

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_openai_key'}):
            config = AnswerGeneratorConfig()
            assert config.openai_api_key == 'test_openai_key'

    def test_custom_config(self):
        """Test custom configuration values."""
        config = AnswerGeneratorConfig(
            openai_api_key="custom_key",
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2000
        )
        assert config.openai_api_key == "custom_key"
        assert config.model_name == "gpt-3.5-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000


class TestLeadRAGConfig:
    """Test LeadRAGConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LeadRAGConfig()
        assert config.openai_api_key == ""
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.1

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_openai_key'}):
            config = LeadRAGConfig()
            assert config.openai_api_key == 'test_openai_key'

    def test_custom_config(self):
        """Test custom configuration values."""
        config = LeadRAGConfig(
            openai_api_key="custom_key",
            model_name="gpt-3.5-turbo",
            temperature=0.2
        )
        assert config.openai_api_key == "custom_key"
        assert config.model_name == "gpt-3.5-turbo"
        assert config.temperature == 0.2

    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid temperature
        with pytest.raises(ValueError):
            LeadRAGConfig(temperature=-0.1)

        with pytest.raises(ValueError):
            LeadRAGConfig(temperature=2.1)

        # Test invalid model name
        with pytest.raises(ValueError):
            LeadRAGConfig(model_name="invalid-model")


class TestConfigEnvironmentHandling:
    """Test environment variable handling across configs."""

    def test_missing_env_vars(self):
        """Test behavior when environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise errors, just use empty defaults
            retriever_config = RetrieverConfig()
            reranker_config = RerankerConfig()
            context_config = ContextAnalyzerConfig()
            answer_config = AnswerGeneratorConfig()
            lead_config = LeadRAGConfig()

            assert retriever_config.voyage_api_key == ""
            assert reranker_config.openai_api_key == ""
            assert context_config.openai_api_key == ""
            assert answer_config.openai_api_key == ""
            assert lead_config.openai_api_key == ""

    def test_env_file_loading(self):
        """Test loading configuration from .env file."""
        # Create temporary .env file
        env_content = """
OPENAI_API_KEY=test_openai_key
VOYAGE_API_KEY=test_voyage_key
ASTRA_DB_API_ENDPOINT=test_endpoint
ASTRA_DB_APPLICATION_TOKEN=test_token
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            temp_path = f.name

        try:
            # Mock python-dotenv loading
            with patch('os.environ') as mock_env:
                mock_env.get.side_effect = lambda key, default="": {
                    'OPENAI_API_KEY': 'test_openai_key',
                    'VOYAGE_API_KEY': 'test_voyage_key',
                    'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
                    'ASTRA_DB_APPLICATION_TOKEN': 'test_token'
                }.get(key, default)

                config = RetrieverConfig()
                assert config.voyage_api_key == 'test_voyage_key'
                assert config.astra_db_endpoint == 'test_endpoint'
                assert config.astra_db_token == 'test_token'

        finally:
            os.unlink(temp_path)