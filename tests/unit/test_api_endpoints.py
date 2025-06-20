#!/usr/bin/env python3
"""
Testes unitários para endpoints da API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from api.main import app
from api.models.schemas import ResearchQuery, SimpleQuery, IndexQuery


class TestAPIEndpoints:
    """Testes para endpoints da API"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.client = TestClient(app)
        self.valid_token = "test-bearer-token"
        self.headers = {"Authorization": f"Bearer {self.valid_token}"}
    
    def test_health_endpoint(self):
        """Testa endpoint de health (sem autenticação)"""
        response = self.client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "uptime_seconds" in data
        assert "components" in data
        assert "metrics" in data
    
    def test_health_endpoint_components(self):
        """Testa componentes do health check"""
        response = self.client.get("/api/v1/health")
        data = response.json()
        
        components = data["components"]
        assert "memory" in components
        assert "simple_rag" in components
        assert "lead_researcher" in components
        
        # Todos os componentes devem ser boolean
        for component, status in components.items():
            assert isinstance(status, bool)
    
    def test_unauthorized_requests(self):
        """Testa requisições não autorizadas"""
        endpoints = [
            "/api/v1/research",
            "/api/v1/simple", 
            "/api/v1/index",
            "/api/v1/stats"
        ]
        
        for endpoint in endpoints:
            response = self.client.post(endpoint, json={})
            assert response.status_code == 401
    
    def test_invalid_bearer_token(self):
        """Testa token inválido"""
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        
        response = self.client.post(
            "/api/v1/research",
            json={"query": "test", "use_multiagent": True},
            headers=invalid_headers
        )
        
        assert response.status_code == 401
    
    @patch('api.core.config.config.API_BEARER_TOKEN', 'test-bearer-token')
    @patch('api.routers.research.lead_researcher')
    def test_research_endpoint_success(self, mock_researcher):
        """Testa endpoint de research com sucesso"""
        # Mock do researcher
        mock_researcher.run_research.return_value = {
            "result": "Test research result",
            "agent_id": "test-agent-123",
            "status": "COMPLETED",
            "processing_time": 12.5
        }
        
        query_data = {
            "query": "What is Zep?",
            "use_multiagent": True,
            "max_subagents": 2
        }
        
        response = self.client.post(
            "/api/v1/research",
            json=query_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["query"] == "What is Zep?"
        assert "result" in data
        assert "agent_id" in data
        assert "processing_time" in data
    
    @patch('api.core.config.config.API_BEARER_TOKEN', 'test-bearer-token')
    def test_research_endpoint_validation(self):
        """Testa validação do endpoint de research"""
        # Query faltando
        response = self.client.post(
            "/api/v1/research",
            json={"use_multiagent": True},
            headers=self.headers
        )
        assert response.status_code == 422
        
        # use_multiagent faltando
        response = self.client.post(
            "/api/v1/research", 
            json={"query": "test"},
            headers=self.headers
        )
        assert response.status_code == 422
        
        # max_subagents inválido
        response = self.client.post(
            "/api/v1/research",
            json={
                "query": "test",
                "use_multiagent": True,
                "max_subagents": 10  # Acima do limite
            },
            headers=self.headers
        )
        assert response.status_code == 422
    
    @patch('api.core.config.config.API_BEARER_TOKEN', 'test-bearer-token')
    @patch('api.routers.research.simple_rag')
    def test_simple_endpoint_success(self, mock_simple_rag):
        """Testa endpoint simple com sucesso"""
        mock_simple_rag.search_documents.return_value = {
            "documents": [{"content": "Test doc", "similarity": 0.9}],
            "summary": "Test summary"
        }
        
        query_data = {
            "query": "What is Zep?",
            "collection_name": "pdf_documents",
            "top_k": 5
        }
        
        response = self.client.post(
            "/api/v1/simple",
            json=query_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["query"] == "What is Zep?"
        assert "result" in data
        assert "sources" in data
    
    @patch('api.core.config.config.API_BEARER_TOKEN', 'test-bearer-token')
    @patch('src.core.indexer.PDFIndexer')
    def test_index_endpoint_success(self, mock_indexer_class):
        """Testa endpoint de indexação com sucesso"""
        mock_indexer = MagicMock()
        mock_indexer_class.return_value = mock_indexer
        mock_indexer.index_pdf_from_url.return_value = {
            "pages_processed": 12,
            "images_extracted": 12,
            "text_chunks": 45
        }
        
        index_data = {
            "pdf_url": "https://example.com/test.pdf",
            "collection_name": "test_docs",
            "extract_images": True
        }
        
        response = self.client.post(
            "/api/v1/index",
            json=index_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "details" in data
        assert data["details"]["pages_processed"] == 12
    
    @patch('api.core.config.config.API_BEARER_TOKEN', 'test-bearer-token')
    def test_stats_endpoint(self):
        """Testa endpoint de estatísticas"""
        response = self.client.get("/api/v1/stats", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "system_stats" in data
        assert "agent_stats" in data
        assert "model_usage" in data


class TestAPIModels:
    """Testes para modelos/schemas da API"""
    
    def test_research_query_validation(self):
        """Testa validação do ResearchQuery"""
        # Query válida
        valid_query = ResearchQuery(
            query="What is Zep?",
            use_multiagent=True,
            max_subagents=2
        )
        assert valid_query.query == "What is Zep?"
        assert valid_query.use_multiagent is True
        assert valid_query.max_subagents == 2
        
        # Testa valores padrão
        default_query = ResearchQuery(
            query="Test query",
            use_multiagent=True
        )
        assert default_query.max_subagents == 3
        assert default_query.timeout == 300
    
    def test_simple_query_validation(self):
        """Testa validação do SimpleQuery"""
        valid_query = SimpleQuery(query="Test query")
        assert valid_query.query == "Test query"
        assert valid_query.collection_name == "pdf_documents"
        assert valid_query.top_k == 5
    
    def test_index_query_validation(self):
        """Testa validação do IndexQuery"""
        valid_query = IndexQuery(
            pdf_url="https://example.com/test.pdf"
        )
        assert valid_query.pdf_url == "https://example.com/test.pdf"
        assert valid_query.collection_name == "pdf_documents"
        assert valid_query.extract_images is True


class TestAPIErrorHandling:
    """Testes para tratamento de erros da API"""
    
    def setup_method(self):
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test-token"}
    
    @patch('api.core.config.config.API_BEARER_TOKEN', 'test-token')
    @patch('api.routers.research.lead_researcher')
    def test_research_timeout_error(self, mock_researcher):
        """Testa erro de timeout na research"""
        import asyncio
        mock_researcher.run_research.side_effect = asyncio.TimeoutError("Timeout")
        
        response = self.client.post(
            "/api/v1/research",
            json={"query": "test", "use_multiagent": True},
            headers=self.headers
        )
        
        assert response.status_code == 504
        data = response.json()
        assert data["error"] is True
        assert "timeout" in data["message"].lower()
    
    @patch('api.core.config.config.API_BEARER_TOKEN', 'test-token')
    @patch('api.routers.research.lead_researcher')
    def test_research_general_error(self, mock_researcher):
        """Testa erro geral na research"""
        mock_researcher.run_research.side_effect = Exception("Test error")
        
        response = self.client.post(
            "/api/v1/research",
            json={"query": "test", "use_multiagent": True},
            headers=self.headers
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"] is True
        assert "erro interno" in data["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])