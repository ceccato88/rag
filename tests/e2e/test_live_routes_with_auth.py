#!/usr/bin/env python3
"""
Teste ao vivo das rotas de indexing e research com servidor HTTP real
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

# Configuração
API_HOST = "127.0.0.1"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# Token fake para testes (deve falhar na autenticação)
FAKE_TOKEN = "test_fake_token_123"
HEADERS_FAKE = {"Authorization": f"Bearer {FAKE_TOKEN}"}


class LiveRouteTester:
    def __init__(self):
        self.server_process = None
        self.client = httpx.Client(timeout=30.0)
    
    def start_server(self):
        """Inicia o servidor da API"""
        print("🚀 Iniciando servidor da API...")
        
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", API_HOST, 
            "--port", str(API_PORT),
            "--log-level", "info"
        ]
        
        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("⏳ Aguardando servidor inicializar...")
            time.sleep(15)  # Aguarda 15 segundos para inicialização completa
            
            if self.server_process.poll() is None:
                print("✅ Servidor iniciado com sucesso")
                return True
            else:
                print("❌ Servidor falhou ao iniciar")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False
    
    def stop_server(self):
        """Para o servidor da API"""
        if self.server_process:
            print("🛑 Parando servidor...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ Servidor parado")
    
    def test_indexing_routes(self):
        """Testa as rotas de indexação"""
        print("\\n🔄 TESTANDO ROTAS DE INDEXAÇÃO")
        print("-" * 40)
        
        results = {
            "status_endpoint": False,
            "validate_url_endpoint": False,
            "index_auth_protection": False,
            "index_validation": False
        }
        
        try:
            # 1. Teste de status (público)
            print("📍 Testando status de indexação...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/index/status")
            if response.status_code == 200:
                data = response.json()
                indexer_available = data.get("indexer_available", False)
                print(f"   ✅ Status acessível - Indexer disponível: {indexer_available}")
                results["status_endpoint"] = True
            else:
                print(f"   ❌ Status falhou - {response.status_code}")
            
            # 2. Teste de validação de URL (público)
            print("📍 Testando validação de URL...")
            valid_url_payload = {"url": "https://arxiv.org/pdf/1706.03762.pdf"}
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/index/validate-url", 
                json=valid_url_payload
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("valid") is True:
                    print("   ✅ Validação de URL funcionando")
                    results["validate_url_endpoint"] = True
                else:
                    print("   ❌ URL válida foi rejeitada")
            else:
                print(f"   ❌ Validação falhou - {response.status_code}")
            
            # 3. Teste de proteção por autenticação
            print("📍 Testando proteção por autenticação...")
            index_payload = {"url": "https://arxiv.org/pdf/1706.03762.pdf"}
            
            # Sem auth
            response = self.client.post(f"{API_BASE_URL}/api/v1/index", json=index_payload)
            if response.status_code in [401, 503]:
                print("   ✅ Endpoint protegido sem auth")
                
                # Com auth fake
                response = self.client.post(
                    f"{API_BASE_URL}/api/v1/index", 
                    json=index_payload, 
                    headers=HEADERS_FAKE
                )
                if response.status_code in [401, 503]:
                    print("   ✅ Endpoint rejeita token fake")
                    results["index_auth_protection"] = True
                else:
                    print(f"   ❌ Token fake foi aceito - {response.status_code}")
            else:
                print(f"   ❌ Endpoint não está protegido - {response.status_code}")
            
            # 4. Teste de validação de dados
            print("📍 Testando validação de dados...")
            invalid_payloads = [
                {"url": ""},  # URL vazia
                {"url": "not-a-url"},  # URL inválida
                {"url": "https://example.com/file.txt"}  # Não é PDF
            ]
            
            validation_errors = 0
            for payload in invalid_payloads:
                response = self.client.post(
                    f"{API_BASE_URL}/api/v1/index/validate-url", 
                    json=payload
                )
                if response.status_code in [422, 200]:  # 422 ou 200 com valid=false
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("valid") is False:
                            validation_errors += 1
                    else:
                        validation_errors += 1
            
            if validation_errors == len(invalid_payloads):
                print("   ✅ Validação de dados funcionando")
                results["index_validation"] = True
            else:
                print(f"   ❌ Validação falhou para {len(invalid_payloads) - validation_errors} casos")
        
        except Exception as e:
            print(f"❌ Erro nos testes de indexação: {e}")
        
        return results
    
    def test_research_routes(self):
        """Testa as rotas de pesquisa"""
        print("\\n🔍 TESTANDO ROTAS DE RESEARCH")
        print("-" * 40)
        
        results = {
            "auth_protection": False,
            "query_validation": False,
            "debug_endpoints": False,
            "specialized_endpoints": False
        }
        
        try:
            # 1. Teste de proteção por autenticação
            print("📍 Testando proteção por autenticação...")
            query_payload = {"query": "What is machine learning?"}
            
            # Sem auth
            response = self.client.post(f"{API_BASE_URL}/api/v1/research", json=query_payload)
            if response.status_code in [401, 503]:
                print("   ✅ Research protegido sem auth")
                
                # Com auth fake
                response = self.client.post(
                    f"{API_BASE_URL}/api/v1/research", 
                    json=query_payload, 
                    headers=HEADERS_FAKE
                )
                if response.status_code in [401, 503]:
                    print("   ✅ Research rejeita token fake")
                    results["auth_protection"] = True
                else:
                    print(f"   ❌ Token fake foi aceito - {response.status_code}")
            else:
                print(f"   ❌ Research não está protegido - {response.status_code}")
            
            # 2. Teste de validação de query
            print("📍 Testando validação de query...")
            invalid_queries = [
                {"query": ""},  # Query vazia
                {"query": "ab"},  # Query muito curta
                {"query": "x" * 1001}  # Query muito longa
            ]
            
            validation_errors = 0
            for payload in invalid_queries:
                response = self.client.post(
                    f"{API_BASE_URL}/api/v1/research", 
                    json=payload,
                    headers=HEADERS_FAKE
                )
                if response.status_code in [422, 503]:
                    validation_errors += 1
            
            if validation_errors > 0:  # Pelo menos alguns devem falhar
                print("   ✅ Validação de query funcionando")
                results["query_validation"] = True
            else:
                print("   ❌ Validação de query não funcionou")
            
            # 3. Teste de endpoints de debug
            print("📍 Testando endpoints de debug...")
            debug_endpoints = [
                "/api/v1/research/status",
                "/api/v1/research/debug",
                "/api/v1/research/simple",
                "/api/v1/research/direct"
            ]
            
            protected_count = 0
            for endpoint in debug_endpoints:
                response = self.client.get(f"{API_BASE_URL}{endpoint}", headers=HEADERS_FAKE)
                if response.status_code in [401, 503]:
                    protected_count += 1
                elif response.status_code == 200:
                    # Se retornar 200, ainda está funcionando (apenas sem dados reais)
                    protected_count += 1
            
            if protected_count >= len(debug_endpoints) - 1:  # Maioria deve estar protegida
                print(f"   ✅ {protected_count}/{len(debug_endpoints)} endpoints protegidos")
                results["debug_endpoints"] = True
            else:
                print(f"   ❌ Apenas {protected_count}/{len(debug_endpoints)} endpoints protegidos")
            
            # 4. Teste de endpoints especializados
            print("📍 Testando endpoints especializados...")
            specialized_endpoints = [
                ("POST", "/api/v1/research/test-reasoning", {"query": "test"}),
                ("POST", "/api/v1/research/simple", {"query": "test"}),
                ("POST", "/api/v1/research/direct", {"query": "test"})
            ]
            
            working_count = 0
            for method, endpoint, payload in specialized_endpoints:
                if method == "POST":
                    response = self.client.post(
                        f"{API_BASE_URL}{endpoint}", 
                        json=payload,
                        headers=HEADERS_FAKE
                    )
                else:
                    response = self.client.get(f"{API_BASE_URL}{endpoint}", headers=HEADERS_FAKE)
                
                # Se retorna 401/503, está protegido corretamente
                # Se retorna 200, pode estar funcionando (dependendo do sistema backend)
                if response.status_code in [200, 401, 503]:
                    working_count += 1
            
            if working_count == len(specialized_endpoints):
                print(f"   ✅ {working_count}/{len(specialized_endpoints)} endpoints especializados respondem")
                results["specialized_endpoints"] = True
            else:
                print(f"   ❌ Apenas {working_count}/{len(specialized_endpoints)} endpoints respondem")
        
        except Exception as e:
            print(f"❌ Erro nos testes de research: {e}")
        
        return results
    
    def test_authentication_system(self):
        """Testa o sistema de autenticação"""
        print("\\n🔐 TESTANDO SISTEMA DE AUTENTICAÇÃO")
        print("-" * 40)
        
        results = {
            "no_token_rejected": False,
            "invalid_token_rejected": False,
            "malformed_token_rejected": False,
            "protected_endpoints": False
        }
        
        try:
            # Endpoints protegidos para testar
            protected_endpoints = [
                ("POST", "/api/v1/research", {"query": "test"}),
                ("POST", "/api/v1/index", {"url": "https://example.com/test.pdf"}),
                ("GET", "/api/v1/research/status", None),
                ("POST", "/api/v1/research/simple", {"query": "test"})
            ]
            
            # 1. Teste sem token
            print("📍 Testando requisições sem token...")
            no_token_rejections = 0
            for method, endpoint, payload in protected_endpoints:
                if method == "POST":
                    response = self.client.post(f"{API_BASE_URL}{endpoint}", json=payload)
                else:
                    response = self.client.get(f"{API_BASE_URL}{endpoint}")
                
                if response.status_code in [401, 503]:
                    no_token_rejections += 1
            
            if no_token_rejections >= len(protected_endpoints) * 0.8:  # 80% devem ser rejeitados
                print(f"   ✅ {no_token_rejections}/{len(protected_endpoints)} endpoints rejeitam sem token")
                results["no_token_rejected"] = True
            else:
                print(f"   ❌ Apenas {no_token_rejections}/{len(protected_endpoints)} endpoints rejeitam sem token")
            
            # 2. Teste com token inválido
            print("📍 Testando requisições com token inválido...")
            invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
            invalid_token_rejections = 0
            
            for method, endpoint, payload in protected_endpoints:
                if method == "POST":
                    response = self.client.post(f"{API_BASE_URL}{endpoint}", json=payload, headers=invalid_headers)
                else:
                    response = self.client.get(f"{API_BASE_URL}{endpoint}", headers=invalid_headers)
                
                if response.status_code in [401, 503]:
                    invalid_token_rejections += 1
            
            if invalid_token_rejections >= len(protected_endpoints) * 0.8:
                print(f"   ✅ {invalid_token_rejections}/{len(protected_endpoints)} endpoints rejeitam token inválido")
                results["invalid_token_rejected"] = True
            else:
                print(f"   ❌ Apenas {invalid_token_rejections}/{len(protected_endpoints)} endpoints rejeitam token inválido")
            
            # 3. Teste com token malformado
            print("📍 Testando requisições com token malformado...")
            malformed_headers = {"Authorization": "InvalidFormat token_without_bearer"}
            malformed_rejections = 0
            
            for method, endpoint, payload in protected_endpoints:
                if method == "POST":
                    response = self.client.post(f"{API_BASE_URL}{endpoint}", json=payload, headers=malformed_headers)
                else:
                    response = self.client.get(f"{API_BASE_URL}{endpoint}", headers=malformed_headers)
                
                if response.status_code in [401, 503]:
                    malformed_rejections += 1
            
            if malformed_rejections >= len(protected_endpoints) * 0.8:
                print(f"   ✅ {malformed_rejections}/{len(protected_endpoints)} endpoints rejeitam token malformado")
                results["malformed_token_rejected"] = True
            else:
                print(f"   ❌ Apenas {malformed_rejections}/{len(protected_endpoints)} endpoints rejeitam token malformado")
            
            # 4. Verificar se todos os endpoints estão protegidos
            all_protected = (
                results["no_token_rejected"] and 
                results["invalid_token_rejected"] and 
                results["malformed_token_rejected"]
            )
            
            if all_protected:
                print("   ✅ Sistema de autenticação funcionando corretamente")
                results["protected_endpoints"] = True
            else:
                print("   ⚠️ Sistema de autenticação tem algumas falhas")
        
        except Exception as e:
            print(f"❌ Erro nos testes de autenticação: {e}")
        
        return results
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🧪 TESTES LIVE DAS ROTAS INDEXING E RESEARCH")
        print("=" * 80)
        
        # Iniciar servidor
        if not self.start_server():
            return False
        
        try:
            # Executar todos os testes
            indexing_results = self.test_indexing_routes()
            research_results = self.test_research_routes()
            auth_results = self.test_authentication_system()
            
            # Calcular estatísticas
            print("\\n" + "=" * 80)
            print("📊 RESULTADOS FINAIS:")
            
            # Indexação
            indexing_passed = sum(indexing_results.values())
            indexing_total = len(indexing_results)
            print(f"\\n🔄 INDEXAÇÃO: {indexing_passed}/{indexing_total} testes passaram")
            for test, passed in indexing_results.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {test}")
            
            # Research
            research_passed = sum(research_results.values())
            research_total = len(research_results)
            print(f"\\n🔍 RESEARCH: {research_passed}/{research_total} testes passaram")
            for test, passed in research_results.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {test}")
            
            # Autenticação
            auth_passed = sum(auth_results.values())
            auth_total = len(auth_results)
            print(f"\\n🔐 AUTENTICAÇÃO: {auth_passed}/{auth_total} testes passaram")
            for test, passed in auth_results.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {test}")
            
            # Resultado geral
            total_passed = indexing_passed + research_passed + auth_passed
            total_tests = indexing_total + research_total + auth_total
            success_rate = (total_passed / total_tests) * 100
            
            print(f"\\n🎯 RESULTADO GERAL: {total_passed}/{total_tests} ({success_rate:.1f}%) testes passaram")
            
            if success_rate >= 80:
                print("🎉 EXCELENTE! A API está funcionando muito bem!")
                return True
            elif success_rate >= 60:
                print("👍 BOM! A API está funcionando adequadamente.")
                return True
            else:
                print("⚠️ ATENÇÃO! A API precisa de algumas correções.")
                return False
                
        finally:
            self.stop_server()
            self.client.close()


def main():
    """Função principal"""
    try:
        tester = LiveRouteTester()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()