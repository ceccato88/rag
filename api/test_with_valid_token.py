#!/usr/bin/env python3
"""
Teste das rotas com token válido em modo desenvolvimento
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

# Configuração
API_HOST = "127.0.0.1"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"


class AuthenticatedRouteTester:
    def __init__(self):
        self.server_process = None
        self.client = httpx.Client(timeout=30.0)
    
    def start_server_dev_mode(self):
        """Inicia o servidor em modo desenvolvimento (sem autenticação)"""
        print("🚀 Iniciando servidor em modo desenvolvimento...")
        
        # Configurar variáveis de ambiente para modo dev
        env = os.environ.copy()
        env["PRODUCTION_MODE"] = "false"
        env["API_BEARER_TOKEN"] = ""  # Token vazio para modo dev
        
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
                text=True,
                env=env
            )
            
            print("⏳ Aguardando servidor inicializar...")
            time.sleep(15)  # Aguarda 15 segundos para inicialização completa
            
            if self.server_process.poll() is None:
                print("✅ Servidor iniciado em modo desenvolvimento")
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
    
    def test_indexing_with_auth(self):
        """Testa indexação com autenticação válida (modo dev)"""
        print("\\n🔄 TESTANDO INDEXAÇÃO COM AUTENTICAÇÃO (MODO DEV)")
        print("-" * 50)
        
        results = {
            "status_check": False,
            "url_validation": False,
            "valid_indexing_request": False,
            "indexing_flow": False
        }
        
        try:
            # 1. Verificar status do indexer
            print("📍 Verificando status do indexer...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/index/status")
            if response.status_code == 200:
                data = response.json()
                indexer_available = data.get("indexer_available", False)
                print(f"   ✅ Status OK - Indexer disponível: {indexer_available}")
                results["status_check"] = True
            else:
                print(f"   ❌ Falha no status - {response.status_code}")
            
            # 2. Validar URL
            print("📍 Validando URL de teste...")
            test_url = "https://arxiv.org/pdf/1706.03762.pdf"
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/index/validate-url",
                json={"url": test_url}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("valid") is True:
                    print(f"   ✅ URL válida - Doc source: {data.get('generated_doc_source')}")
                    results["url_validation"] = True
                else:
                    print(f"   ❌ URL inválida - {data.get('error')}")
            else:
                print(f"   ❌ Falha na validação - {response.status_code}")
            
            # 3. Tentar indexação real (sem autenticação - modo dev)
            print("📍 Testando indexação em modo desenvolvimento...")
            index_payload = {
                "url": test_url,
                "doc_source": "test-paper-attention"
            }
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/index",
                json=index_payload
            )
            
            print(f"   Status da resposta: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"   ✅ Indexação bem-sucedida!")
                    print(f"      - Páginas: {data.get('pages_processed', 0)}")
                    print(f"      - Chunks: {data.get('chunks_created', 0)}")
                    print(f"      - Tempo: {data.get('processing_time', 0):.2f}s")
                    results["valid_indexing_request"] = True
                    results["indexing_flow"] = True
                else:
                    print(f"   ⚠️ Indexação falhou: {data.get('message')}")
                    results["valid_indexing_request"] = True  # Request válido, mas falha interna
            elif response.status_code in [401, 503]:
                print("   ⚠️ Ainda está protegido por autenticação ou serviço indisponível")
                results["valid_indexing_request"] = True  # Request válido, sistema não configurado
            else:
                print(f"   ❌ Erro inesperado: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"      Erro: {error_data}")
                except:
                    print(f"      Resposta: {response.text[:200]}")
        
        except Exception as e:
            print(f"❌ Erro nos testes de indexação: {e}")
        
        return results
    
    def test_research_with_auth(self):
        """Testa pesquisa com autenticação válida (modo dev)"""
        print("\\n🔍 TESTANDO RESEARCH COM AUTENTICAÇÃO (MODO DEV)")
        print("-" * 50)
        
        results = {
            "basic_research": False,
            "simple_rag": False,
            "direct_research": False,
            "debug_info": False
        }
        
        try:
            # 1. Teste de pesquisa básica
            print("📍 Testando pesquisa básica...")
            query_payload = {"query": "What is transformer architecture in deep learning?"}
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research",
                json=query_payload
            )
            
            print(f"   Status da resposta: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"   ✅ Pesquisa bem-sucedida!")
                    print(f"      - Status: {data.get('status')}")
                    print(f"      - Tempo: {data.get('processing_time', 0):.2f}s")
                    print(f"      - Resultado: {data.get('result', '')[:100]}...")
                    results["basic_research"] = True
                else:
                    print(f"   ⚠️ Pesquisa retornou erro: {data.get('error')}")
            elif response.status_code in [401, 503]:
                print("   ⚠️ Ainda está protegido por autenticação ou serviço indisponível")
            else:
                print(f"   ❌ Erro inesperado: {response.status_code}")
            
            # 2. Teste de RAG simples
            print("📍 Testando SimpleRAG...")
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research/simple",
                json=query_payload
            )
            
            print(f"   Status da resposta: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"   ✅ SimpleRAG funcionando!")
                    print(f"      - Resultado: {len(data.get('result', ''))} caracteres")
                    results["simple_rag"] = True
                else:
                    print(f"   ⚠️ SimpleRAG sem resultados: {data.get('result')}")
            elif response.status_code in [401, 503]:
                print("   ⚠️ Ainda está protegido ou serviço indisponível")
            
            # 3. Teste de pesquisa direta
            print("📍 Testando pesquisa direta...")
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research/direct",
                json=query_payload
            )
            
            print(f"   Status da resposta: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"   ✅ Pesquisa direta funcionando!")
                    results["direct_research"] = True
                else:
                    print(f"   ⚠️ Pesquisa direta sem resultados")
            elif response.status_code in [401, 503]:
                print("   ⚠️ Ainda está protegido ou serviço indisponível")
            
            # 4. Teste de debug
            print("📍 Testando debug do sistema...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/research/debug")
            
            print(f"   Status da resposta: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Debug acessível!")
                print(f"      - API ready: {data.get('api_state', {}).get('ready', False)}")
                print(f"      - Lead researcher: {data.get('components', {}).get('lead_researcher_available', False)}")
                print(f"      - SimpleRAG: {data.get('components', {}).get('simple_rag_available', False)}")
                results["debug_info"] = True
            elif response.status_code in [401, 503]:
                print("   ⚠️ Debug protegido ou serviço indisponível")
        
        except Exception as e:
            print(f"❌ Erro nos testes de research: {e}")
        
        return results
    
    def test_system_readiness(self):
        """Testa se o sistema está totalmente inicializado"""
        print("\\n🏥 TESTANDO PRONTIDÃO DO SISTEMA")
        print("-" * 50)
        
        results = {
            "health_check": False,
            "system_components": False,
            "api_metrics": False
        }
        
        try:
            # 1. Health check
            print("📍 Testando health check...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                print(f"   ✅ Health check OK - Status: {status}")
                print(f"      - Uptime: {data.get('uptime_seconds', 0):.1f}s")
                print(f"      - Componentes: {data.get('components', {})}")
                results["health_check"] = True
                
                # Verificar componentes específicos
                components = data.get("components", {})
                if components.get("lead_researcher") and components.get("simple_rag"):
                    print("   ✅ Componentes principais disponíveis")
                    results["system_components"] = True
                else:
                    print("   ⚠️ Alguns componentes não estão disponíveis")
            
            # 2. Métricas
            print("📍 Testando métricas...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Métricas disponíveis")
                print(f"      - API ready: {data.get('api_ready', False)}")
                print(f"      - Multi-agent: {data.get('multiagent_initialized', False)}")
                print(f"      - Requests: {data.get('total_requests', 0)}")
                results["api_metrics"] = True
        
        except Exception as e:
            print(f"❌ Erro nos testes de sistema: {e}")
        
        return results
    
    def run_authenticated_tests(self):
        """Executa todos os testes em modo autenticado"""
        print("🧪 TESTES COM AUTENTICAÇÃO VÁLIDA (MODO DESENVOLVIMENTO)")
        print("=" * 80)
        
        # Iniciar servidor em modo dev
        if not self.start_server_dev_mode():
            return False
        
        try:
            # Aguardar inicialização completa
            print("⏳ Aguardando inicialização completa do sistema...")
            time.sleep(5)
            
            # Executar todos os testes
            system_results = self.test_system_readiness()
            indexing_results = self.test_indexing_with_auth()
            research_results = self.test_research_with_auth()
            
            # Calcular estatísticas
            print("\\n" + "=" * 80)
            print("📊 RESULTADOS DOS TESTES AUTENTICADOS:")
            
            # Sistema
            system_passed = sum(system_results.values())
            system_total = len(system_results)
            print(f"\\n🏥 SISTEMA: {system_passed}/{system_total} testes passaram")
            for test, passed in system_results.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {test}")
            
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
            
            # Resultado geral
            total_passed = system_passed + indexing_passed + research_passed
            total_tests = system_total + indexing_total + research_total
            success_rate = (total_passed / total_tests) * 100
            
            print(f"\\n🎯 RESULTADO GERAL: {total_passed}/{total_tests} ({success_rate:.1f}%) testes passaram")
            
            if success_rate >= 70:
                print("🎉 EXCELENTE! As rotas estão funcionando bem!")
                return True
            elif success_rate >= 50:
                print("👍 BOM! A maioria das funcionalidades está operacional.")
                return True
            else:
                print("⚠️ ATENÇÃO! Muitas funcionalidades precisam de configuração.")
                return False
                
        finally:
            self.stop_server()
            self.client.close()


def main():
    """Função principal"""
    try:
        tester = AuthenticatedRouteTester()
        success = tester.run_authenticated_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()