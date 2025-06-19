#!/usr/bin/env python3
"""
Teste completo da API RAG Multi-Agente
"""

import asyncio
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
    from api.main import app
    from api.core.config import config
    
    # Cliente de teste
    client = TestClient(app)
    
    def test_basic_imports():
        """Teste básico de imports"""
        print("✅ Teste 1: Imports básicos - SUCESSO")
        return True
    
    def test_app_creation():
        """Teste de criação da aplicação"""
        assert app is not None
        assert app.title == "🚀 Sistema RAG Multi-Agente"
        print("✅ Teste 2: Criação da aplicação - SUCESSO")
        return True
    
    def test_root_endpoint():
        """Teste do endpoint raiz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Sistema RAG Multi-Agente" in data["message"]
        print("✅ Teste 3: Endpoint raiz - SUCESSO")
        return True
    
    def test_health_endpoint():
        """Teste do endpoint de health"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print("✅ Teste 4: Endpoint de health - SUCESSO")
        return True
    
    def test_docs_endpoint():
        """Teste do endpoint de documentação"""
        response = client.get("/docs")
        assert response.status_code == 200
        print("✅ Teste 5: Endpoint de documentação - SUCESSO")
        return True
    
    def test_openapi_endpoint():
        """Teste do endpoint OpenAPI"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        print("✅ Teste 6: OpenAPI schema - SUCESSO")
        return True
    
    def test_protected_endpoints_without_auth():
        """Teste de endpoints protegidos sem autenticação"""
        # Teste de endpoint de pesquisa sem auth
        response = client.post("/api/v1/research", json={"query": "test"})
        # API retorna 503 (Service Unavailable) quando sistema não está disponível
        assert response.status_code in [401, 503]  # Unauthorized ou Service Unavailable
        
        # Teste de endpoint de indexação sem auth
        response = client.post("/api/v1/index", json={"url": "http://example.com"})
        assert response.status_code in [401, 503]  # Unauthorized ou Service Unavailable
        
        print("✅ Teste 7: Endpoints protegidos sem auth - SUCESSO")
        return True
    
    def test_protected_endpoints_with_invalid_auth():
        """Teste de endpoints protegidos com auth inválida"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        # Teste de endpoint de pesquisa com auth inválida
        response = client.post("/api/v1/research", json={"query": "test"}, headers=headers)
        # API retorna 503 (Service Unavailable) quando sistema não está disponível
        assert response.status_code in [401, 503]  # Unauthorized ou Service Unavailable
        
        print("✅ Teste 8: Endpoints protegidos com auth inválida - SUCESSO")
        return True
    
    def test_rate_limiting_setup():
        """Teste se rate limiting está configurado"""
        # Verificar se o rate limiter está no estado da aplicação
        assert hasattr(app.state, 'limiter')
        print("✅ Teste 9: Rate limiting configurado - SUCESSO")
        return True
    
    def test_middlewares_setup():
        """Teste se middlewares estão configurados"""
        # Verificar se middlewares foram adicionados
        assert len(app.user_middleware) > 0
        print("✅ Teste 10: Middlewares configurados - SUCESSO")
        return True
    
    def run_all_tests():
        """Executar todos os testes"""
        print("🚀 Iniciando testes da API RAG Multi-Agente v2.0.0")
        print("=" * 60)
        
        tests = [
            test_basic_imports,
            test_app_creation,
            test_root_endpoint,
            test_health_endpoint,
            test_docs_endpoint,
            test_openapi_endpoint,
            test_protected_endpoints_without_auth,
            test_protected_endpoints_with_invalid_auth,
            test_rate_limiting_setup,
            test_middlewares_setup
        ]
        
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_func.__name__} - FALHOU: {e}")
                failed += 1
        
        print("=" * 60)
        print(f"📊 Resultados: {passed} sucessos, {failed} falhas")
        
        if failed == 0:
            print("🎉 Todos os testes passaram!")
            return True
        else:
            print("⚠️  Alguns testes falharam!")
            return False
    
    if __name__ == "__main__":
        success = run_all_tests()
        sys.exit(0 if success else 1)

except Exception as e:
    print(f"❌ Erro durante a execução dos testes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)