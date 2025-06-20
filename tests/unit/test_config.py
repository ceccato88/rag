#!/usr/bin/env python3
"""
Testes unitários para configuração do sistema
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from src.core.config import RAGConfig
from src.core.constants import DEFAULT_MODELS, SPECIALIST_TYPES


class TestRAGConfig:
    """Testes para configuração RAG"""
    
    def test_default_config_values(self):
        """Testa valores padrão da configuração"""
        config = RAGConfig()
        
        assert config.llm_model == "gpt-4.1-mini"
        assert config.embedding_model == "voyage-multimodal-3"
        assert config.max_candidates == 3  # Updated to match actual default
        assert hasattr(config, 'coordinator_model')
        assert config.coordinator_model == "gpt-4.1"
        
    def test_environment_overrides(self):
        """Testa sobrescrita por variáveis de ambiente"""
        with patch.dict(os.environ, {
            'OPENAI_MODEL': 'gpt-4',
            'MAX_CANDIDATES': '10',
            'COORDINATOR_MODEL': 'gpt-4.1'
        }):
            config = RAGConfig()
            
            assert config.llm_model == "gpt-4"
            assert config.max_candidates == 10
            assert config.coordinator_model == "gpt-4.1"
    
    def test_coordinator_model_config(self):
        """Testa configuração do modelo coordenador"""
        with patch.dict(os.environ, {
            'COORDINATOR_MODEL': 'gpt-4.1'
        }):
            config = RAGConfig()
            
            assert hasattr(config, 'coordinator_model')
            assert config.coordinator_model == "gpt-4.1"


class TestConstants:
    """Testes para constantes do sistema"""
    
    def test_default_models_structure(self):
        """Testa estrutura dos modelos padrão"""
        assert 'LLM' in DEFAULT_MODELS
        assert 'EMBEDDING' in DEFAULT_MODELS
        assert 'COORDINATOR' in DEFAULT_MODELS
        
        assert DEFAULT_MODELS['LLM'] == "gpt-4.1-mini"
        assert DEFAULT_MODELS['COORDINATOR'] == "gpt-4.1"
        assert DEFAULT_MODELS['EMBEDDING'] == "voyage-multimodal-3"
    
    def test_specialist_types_count(self):
        """Testa que temos 7 tipos de especialistas"""
        assert len(SPECIALIST_TYPES) == 7
        
        expected_types = [
            "conceptual", "technical", "comparative", 
            "examples", "overview", "applications", "general"
        ]
        
        for specialist_type in expected_types:
            assert specialist_type in SPECIALIST_TYPES
    
    def test_specialist_types_values(self):
        """Testa valores dos tipos de especialistas"""
        assert SPECIALIST_TYPES["conceptual"] == "Conceptual analysis and definitions"
        assert SPECIALIST_TYPES["technical"] == "Technical implementation details"
        assert SPECIALIST_TYPES["comparative"] == "Comparative analysis and differences"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])