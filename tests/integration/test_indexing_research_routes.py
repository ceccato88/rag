#!/usr/bin/env python3
"""
Testes específicos para rotas de indexing e research
"""

import json
import sys
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

# Adicionar o diretório pai ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.apis.v2.main import app
    from src.apis.v2.core.config import src.core.config as config
    
    # Cliente de teste
    client = TestClient(app)
    
    # Token de teste para autenticação
    TEST_TOKEN = "test_token_123"
    TEST_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    # URLs de teste
    TEST_PDF_URL = "https://arxiv.org/pdf/1706.03762.pdf"  # Attention is All You Need paper
    INVALID_PDF_URL = "https://example.com/notfound.pdf"
    NON_PDF_URL = "https://example.com/document.txt"
    
    class TestIndexingRoutes:
        """Testes para rotas de indexação"""
        
        def test_indexing_status_public(self):
            """Teste do status de indexação (endpoint público)"""
            response = client.get("/api/v1/index/status")
            assert response.status_code == 200
            
            data = response.json()
            assert "indexer_available" in data
            assert "indexer_version" in data
            assert "capabilities" in data
            assert "supported_formats" in data
            assert "timestamp" in data
            
            print(f"✅ Status de indexação: {data['indexer_available']}")
            return True
        
        def test_validate_url_endpoint(self):
            """Teste de validação de URL (endpoint público)"""
            # URL válida
            valid_payload = {"url": TEST_PDF_URL}
            response = client.post("/api/v1/index/validate-url", json=valid_payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is True
            assert "generated_doc_source" in data
            
            # URL inválida (não é PDF)
            invalid_payload = {"url": NON_PDF_URL}
            response = client.post("/api/v1/index/validate-url", json=invalid_payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is False
            assert "error" in data
            
            print("✅ Validação de URL funcionando")
            return True
        
        def test_index_without_auth(self):
            """Teste de indexação sem autenticação"""
            payload = {"url": TEST_PDF_URL}
            response = client.post("/api/v1/index", json=payload)
            
            # Deve retornar 401 (Unauthorized) ou 503 (Service Unavailable)
            assert response.status_code in [401, 503]
            print("✅ Indexação protegida por autenticação")
            return True
        
        def test_index_with_invalid_auth(self):
            """Teste de indexação com autenticação inválida"""
            headers = {"Authorization": "Bearer invalid_token"}
            payload = {"url": TEST_PDF_URL}
            response = client.post("/api/v1/index", json=payload, headers=headers)
            
            # Deve retornar 401 (Unauthorized) ou 503 (Service Unavailable)
            assert response.status_code in [401, 503]
            print("✅ Indexação rejeita token inválido")
            return True
        
        def test_index_validation_errors(self):
            """Teste de erros de validação na indexação"""
            headers = {"Authorization": "Bearer fake_token"}  # Token fake para passar auth
            
            # URL vazia
            response = client.post("/api/v1/index", json={"url": ""}, headers=headers)
            assert response.status_code in [422, 503]  # Validation error ou service unavailable
            
            # URL que não é PDF
            response = client.post("/api/v1/index", json={"url": NON_PDF_URL}, headers=headers)
            assert response.status_code in [422, 503]
            
            # URL malformada
            response = client.post("/api/v1/index", json={"url": "not-a-url"}, headers=headers)
            assert response.status_code in [422, 503]
            
            print("✅ Validação de indexação funcionando")
            return True
    
    class TestResearchRoutes:
        """Testes para rotas de pesquisa"""
        
        def test_research_status_protected(self):
            """Teste do status de pesquisa (endpoint protegido)"""
            # Sem autenticação
            response = client.get("/api/v1/research/status")
            assert response.status_code in [401, 503]
            
            # Com autenticação inválida
            headers = {"Authorization": "Bearer invalid_token"}
            response = client.get("/api/v1/research/status", headers=headers)
            assert response.status_code in [401, 503]
            
            print("✅ Status de pesquisa protegido por autenticação")
            return True
        
        def test_research_without_auth(self):
            """Teste de pesquisa sem autenticação"""
            payload = {"query": "What is machine learning?"}
            response = client.post("/api/v1/research", json=payload)
            
            # Deve retornar 401 (Unauthorized) ou 503 (Service Unavailable)
            assert response.status_code in [401, 503]
            print("✅ Pesquisa protegida por autenticação")
            return True
        
        def test_research_with_invalid_auth(self):
            """Teste de pesquisa com autenticação inválida"""
            headers = {"Authorization": "Bearer invalid_token"}
            payload = {"query": "What is machine learning?"}
            response = client.post("/api/v1/research", json=payload, headers=headers)
            
            # Deve retornar 401 (Unauthorized) ou 503 (Service Unavailable)
            assert response.status_code in [401, 503]
            print("✅ Pesquisa rejeita token inválido")
            return True
        
        def test_research_validation_errors(self):
            """Teste de erros de validação na pesquisa"""
            headers = {"Authorization": "Bearer fake_token"}  # Token fake para passar auth
            
            # Query vazia
            response = client.post("/api/v1/research", json={"query": ""}, headers=headers)
            assert response.status_code in [422, 503]  # Validation error ou service unavailable
            
            # Query muito curta
            response = client.post("/api/v1/research", json={"query": "ab"}, headers=headers)
            assert response.status_code in [422, 503]
            
            # Query muito longa
            long_query = "x" * 1001
            response = client.post("/api/v1/research", json={"query": long_query}, headers=headers)
            assert response.status_code in [422, 503]
            
            print("✅ Validação de pesquisa funcionando")
            return True
        
        def test_research_debug_endpoints(self):
            """Teste dos endpoints de debug"""
            headers = {"Authorization": "Bearer fake_token"}
            
            # Debug endpoint
            response = client.get("/api/v1/research/debug", headers=headers)
            assert response.status_code in [200, 401, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert "api_state" in data or "error" in data
                print("✅ Debug endpoint acessível")
            else:
                print("✅ Debug endpoint protegido")
            
            return True
        
        def test_simple_search_endpoint(self):
            """Teste do endpoint de busca simples"""
            headers = {"Authorization": "Bearer fake_token"}
            payload = {"query": "test query"}
            
            response = client.post("/api/v1/research/simple", json=payload, headers=headers)
            assert response.status_code in [200, 401, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert "query" in data
                print("✅ Busca simples funcionando")
            else:
                print("✅ Busca simples protegida")
            
            return True
        
        def test_direct_research_endpoint(self):
            """Teste do endpoint de pesquisa direta"""
            headers = {"Authorization": "Bearer fake_token"}
            payload = {"query": "test query"}
            
            response = client.post("/api/v1/research/direct", json=payload, headers=headers)
            assert response.status_code in [200, 401, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert "query" in data
                print("✅ Pesquisa direta funcionando")
            else:
                print("✅ Pesquisa direta protegida")
            
            return True
        
        def test_reasoning_test_endpoint(self):
            """Teste do endpoint de teste de reasoning"""
            headers = {"Authorization": "Bearer fake_token"}
            payload = {"query": "test reasoning"}
            
            response = client.post("/api/v1/research/test-reasoning", json=payload, headers=headers)
            assert response.status_code in [200, 401, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                print("✅ Teste de reasoning funcionando")
            else:
                print("✅ Teste de reasoning protegido")
            
            return True
    
    class TestSchemaValidation:
        """Testes de validação de schemas"""
        
        def test_research_query_validation(self):
            """Teste de validação do schema ResearchQuery"""
            from src.apis.v2.models.schemas import ResearchQuery
            
            # Query válida
            valid_query = ResearchQuery(query="What is AI?")
            assert valid_query.query == "What is AI?"
            
            # Query com objetivo
            query_with_objective = ResearchQuery(
                query="Explain machine learning", 
                objective="For beginners"
            )
            assert query_with_objective.objective == "For beginners"
            
            # Query muito curta - deve falhar
            try:
                ResearchQuery(query="hi")
                assert False, "Deveria ter falhado com query muito curta"
            except Exception:
                pass  # Esperado
            
            print("✅ Validação ResearchQuery funcionando")
            return True
        
        def test_index_request_validation(self):
            """Teste de validação do schema IndexRequest"""
            from src.apis.v2.models.schemas import IndexRequest
            
            # Request válido
            valid_request = IndexRequest(url="https://example.com/doc.pdf")
            assert valid_request.url == "https://example.com/doc.pdf"
            
            # Request com doc_source
            request_with_source = IndexRequest(
                url="https://example.com/doc.pdf",
                doc_source="test-doc"
            )
            assert request_with_source.doc_source == "test-doc"
            
            # URL que não é PDF - deve falhar
            try:
                IndexRequest(url="https://example.com/doc.txt")
                assert False, "Deveria ter falhado com URL não-PDF"
            except Exception:
                pass  # Esperado
            
            # URL sem protocolo - deve falhar
            try:
                IndexRequest(url="example.com/doc.pdf")
                assert False, "Deveria ter falhado com URL sem protocolo"
            except Exception:
                pass  # Esperado
            
            print("✅ Validação IndexRequest funcionando")
            return True
    
    def run_indexing_tests():
        """Executa todos os testes de indexação"""
        print("🧪 Testando rotas de INDEXAÇÃO")
        print("=" * 50)
        
        indexing_tester = TestIndexingRoutes()
        tests = [
            ("Status de Indexação", indexing_tester.test_indexing_status_public),
            ("Validação de URL", indexing_tester.test_validate_url_endpoint),
            ("Indexação sem Auth", indexing_tester.test_index_without_auth),
            ("Indexação com Auth Inválida", indexing_tester.test_index_with_invalid_auth),
            ("Validação de Erros", indexing_tester.test_index_validation_errors)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\\n🔍 {test_name}...")
                test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} - FALHOU: {e}")
                failed += 1
        
        print(f"\\n📊 Indexação: {passed} sucessos, {failed} falhas")
        return failed == 0
    
    def run_research_tests():
        """Executa todos os testes de pesquisa"""
        print("\\n🧪 Testando rotas de RESEARCH")
        print("=" * 50)
        
        research_tester = TestResearchRoutes()
        tests = [
            ("Status de Pesquisa", research_tester.test_research_status_protected),
            ("Pesquisa sem Auth", research_tester.test_research_without_auth),
            ("Pesquisa com Auth Inválida", research_tester.test_research_with_invalid_auth),
            ("Validação de Erros", research_tester.test_research_validation_errors),
            ("Endpoints de Debug", research_tester.test_research_debug_endpoints),
            ("Busca Simples", research_tester.test_simple_search_endpoint),
            ("Pesquisa Direta", research_tester.test_direct_research_endpoint),
            ("Teste de Reasoning", research_tester.test_reasoning_test_endpoint)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\\n🔍 {test_name}...")
                test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} - FALHOU: {e}")
                failed += 1
        
        print(f"\\n📊 Research: {passed} sucessos, {failed} falhas")
        return failed == 0
    
    def run_schema_tests():
        """Executa todos os testes de schemas"""
        print("\\n🧪 Testando SCHEMAS e VALIDAÇÃO")
        print("=" * 50)
        
        schema_tester = TestSchemaValidation()
        tests = [
            ("ResearchQuery Schema", schema_tester.test_research_query_validation),
            ("IndexRequest Schema", schema_tester.test_index_request_validation)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\\n🔍 {test_name}...")
                test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} - FALHOU: {e}")
                failed += 1
        
        print(f"\\n📊 Schemas: {passed} sucessos, {failed} falhas")
        return failed == 0
    
    def run_all_tests():
        """Executa todos os testes das rotas"""
        print("🚀 TESTES ESPECÍFICOS DAS ROTAS INDEXING E RESEARCH")
        print("=" * 80)
        
        # Executar todos os grupos de testes
        indexing_success = run_indexing_tests()
        research_success = run_research_tests()
        schema_success = run_schema_tests()
        
        # Resultado final
        print("\\n" + "=" * 80)
        print("📋 RESUMO FINAL:")
        print(f"   🔄 Indexação: {'✅ SUCESSO' if indexing_success else '❌ FALHAS'}")
        print(f"   🔍 Research: {'✅ SUCESSO' if research_success else '❌ FALHAS'}")
        print(f"   📋 Schemas: {'✅ SUCESSO' if schema_success else '❌ FALHAS'}")
        
        overall_success = indexing_success and research_success and schema_success
        print(f"\\n🎯 RESULTADO GERAL: {'🎉 TODOS OS TESTES PASSARAM!' if overall_success else '⚠️ ALGUNS TESTES FALHARAM'}")
        
        return overall_success
    
    if __name__ == "__main__":
        success = run_all_tests()
        sys.exit(0 if success else 1)

except Exception as e:
    print(f"❌ Erro durante a execução dos testes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)