"""
Testes funcionais para o módulo search.py
Testa o pipeline RAG completo e funcionalidades de pesquisa.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from typing import Dict, List, Any


class TestSearchFunctionality:
    """Testes das funcionalidades principais de pesquisa"""
    
    def test_setup_rag_logging(self):
        """Testa configuração de logging do RAG"""
        from search import setup_rag_logging
        
        # Test that the function executes without error
        setup_rag_logging()
        assert True  # Function executed successfully
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_rag_initialization(self, mock_openai, mock_voyage, mock_astra):
        """Testa inicialização da classe RAG"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []  # Mock the connectivity test
        
        rag = ProductionConversationalRAG()
        
        # Verify initialization
        assert rag.collection == mock_collection
        assert hasattr(rag, 'openai_client')
        assert hasattr(rag, 'voyage_client')
        assert hasattr(rag, 'chat_history')
        assert rag.chat_history == []
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_conversational_ask_method(self, mock_openai, mock_voyage, mock_astra):
        """Testa o método ask() conversacional principal"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Mock simple greeting response
        with patch.object(rag.query_transformer, 'transform_query', return_value="greeting"):
            with patch.object(rag.query_transformer, 'needs_rag', return_value=False):
                response = rag.ask("Hello!")
                
                assert isinstance(response, str)
                assert len(response) > 0
                assert len(rag.chat_history) == 2  # User + assistant messages
    
    @patch('search.DataAPIClient') 
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_search_and_answer_pipeline(self, mock_openai, mock_voyage, mock_astra):
        """Testa o pipeline search_and_answer completo"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Mock embedding - usando 1024 dimensões para passar na validação
        mock_voyage_client = Mock()
        mock_embedding_response = Mock()
        mock_embedding_response.embeddings = [[0.1] * 1024]  # 1024 dimensões
        mock_voyage_client.multimodal_embed.return_value = mock_embedding_response
        rag.voyage_client = mock_voyage_client
        
        # Mock search candidates
        mock_candidates = [
            {
                "file_path": "/test/doc1_page_1.png",
                "page_num": 1,
                "doc_source": "test_doc",
                "markdown_text": "Test content about machine learning",
                "similarity_score": 0.95  # Correct field name used in search_candidates method
            }
        ]
        mock_collection.find.return_value = mock_candidates
        
        # Mock reranking
        with patch.object(rag, 'rerank_with_gpt', return_value=(mock_candidates, "Relevant page")):
            with patch.object(rag, 'verify_relevance', return_value=True):
                with patch.object(rag, 'generate_conversational_answer', return_value="Generated answer"):
                    
                    result = rag.search_and_answer("What is machine learning?")
                    
                    assert "answer" in result
                    assert "selected_pages" in result
                    assert "total_candidates" in result
                    assert result["answer"] == "Generated answer"
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client') 
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_get_query_embedding(self, mock_openai, mock_voyage, mock_astra):
        """Testa geração de embeddings de query"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Mock voyage client
        mock_voyage_client = Mock()
        mock_response = Mock()
        mock_response.embeddings = [[0.1] * 1024]  # Embedding de 1024 dimensões
        mock_voyage_client.multimodal_embed.return_value = mock_response
        rag.voyage_client = mock_voyage_client
        
        embedding = rag.get_query_embedding("test query")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1024
        assert all(isinstance(x, float) for x in embedding)
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_search_candidates(self, mock_openai, mock_voyage, mock_astra):
        """Testa busca de candidatos no banco"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Mock search results
        mock_results = [
            {
                "file_path": "/test/doc1_page_1.png",
                "page_num": 1,
                "doc_source": "test_doc",
                "markdown_text": "Test content",
                "similarity_score": 0.95  # This matches what search_candidates returns
            }
        ]
        mock_collection.find.return_value = mock_results
        
        candidates = rag.search_candidates([0.1, 0.2, 0.3])
        
        assert isinstance(candidates, list)
        assert len(candidates) == 1
        assert "similarity_score" in candidates[0]
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')  
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_chat_history_management(self, mock_openai, mock_voyage, mock_astra):
        """Testa gerenciamento do histórico de chat"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Test initial state
        assert rag.get_chat_history() == []
        
        # Add some history manually
        rag.chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        history = rag.get_chat_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        
        # Test clear history
        rag.clear_history()
        assert rag.get_chat_history() == []


class TestSearchErrorHandling:
    """Testes de tratamento de erros no sistema de busca"""
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_search_with_no_results(self, mock_openai, mock_voyage, mock_astra):
        """Testa busca que não retorna resultados"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Mock empty search results
        with patch.object(rag, 'get_query_embedding', return_value=[0.1, 0.2, 0.3]):
            with patch.object(rag, 'search_candidates', return_value=[]):
                
                result = rag.search_and_answer("query with no results")
                
                assert "error" in result
                assert "Nenhuma página relevante encontrada" in result["error"]
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_embedding_error_handling(self, mock_openai, mock_voyage, mock_astra):
        """Testa tratamento de erro na geração de embeddings"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Mock embedding error
        with patch.object(rag, 'get_query_embedding', side_effect=Exception("Embedding failed")):
            
            result = rag.search_and_answer("test query")
            
            assert "error" in result
            assert "Embedding falhou" in result["error"]


class TestSearchPerformance:
    """Testes de performance do sistema de busca"""
    
    @patch('search.DataAPIClient')
    @patch('search.voyageai.Client')
    @patch('search.OpenAI')
    @patch.dict('os.environ', {
        'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
        'ASTRA_DB_APPLICATION_TOKEN': 'test_token',
        'VOYAGE_API_KEY': 'voyage_key',
        'OPENAI_API_KEY': 'openai_key'
    })
    def test_search_response_time(self, mock_openai, mock_voyage, mock_astra):
        """Testa tempo de resposta da busca"""
        from search import ProductionConversationalRAG
        
        # Setup mocks
        mock_astra_client = Mock()
        mock_astra.return_value = mock_astra_client
        mock_database = Mock()
        mock_collection = Mock()
        mock_astra_client.get_database.return_value = mock_database
        mock_database.get_collection.return_value = mock_collection
        mock_collection.find.return_value = []
        
        rag = ProductionConversationalRAG()
        
        # Test simple non-RAG response time
        with patch.object(rag.query_transformer, 'transform_query', return_value="greeting"):
            with patch.object(rag.query_transformer, 'needs_rag', return_value=False):
                start_time = time.time()
                response = rag.ask("Hello")
                response_time = time.time() - start_time
                
                assert response_time < 1.0  # Should be fast for simple responses
                assert isinstance(response, str)


class TestProductionQueryTransformer:
    """Testes do transformador de queries em produção"""
    
    @patch('search.OpenAI')
    def test_query_transformer_initialization(self, mock_openai):
        """Testa inicialização do transformador de queries"""
        from search import ProductionQueryTransformer
        
        mock_client = Mock()
        transformer = ProductionQueryTransformer(mock_client)
        
        assert transformer.openai_client == mock_client
        assert hasattr(transformer, 'transformation_cache')  # The actual attribute name
        assert hasattr(transformer, 'greeting_patterns')
        assert hasattr(transformer, 'thank_patterns')
    
    @patch('search.OpenAI')
    def test_needs_rag_method(self, mock_openai):
        """Testa método needs_rag"""
        from search import ProductionQueryTransformer
        
        mock_client = Mock()
        transformer = ProductionQueryTransformer(mock_client)
        
        # Test queries that don't need RAG (contain "not applicable")
        assert not transformer.needs_rag("not applicable")
        assert not transformer.needs_rag("This is not applicable")
        
        # Test queries that need RAG (don't contain "not applicable")
        assert transformer.needs_rag("explain the algorithm")
        assert transformer.needs_rag("what is the paper about")
        assert transformer.needs_rag("show me the performance results")
    
    @patch('search.OpenAI')
    def test_clean_query_method(self, mock_openai):
        """Testa método clean_query"""
        from search import ProductionQueryTransformer
        
        mock_client = Mock()
        transformer = ProductionQueryTransformer(mock_client)
        
        # Test query cleaning
        clean = transformer.clean_query("What is machine learning?")
        assert isinstance(clean, str)
        assert len(clean) > 0
