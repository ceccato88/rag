#!/usr/bin/env python3
"""
Script de teste da API RAG Multi-Agent System
Testa todos os endpoints principais com dados reais
"""
import asyncio
import json
import time
import requests
from pathlib import Path
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

class APITester:
    """Testador da API RAG Multi-Agent"""
    
    def __init__(self, base_url: str = "http://localhost:8000", bearer_token: str = None):
        self.base_url = base_url
        self.bearer_token = bearer_token or self._get_bearer_token()
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.test_results = []
    
    def _get_bearer_token(self) -> str:
        """Obtém token do arquivo .env"""
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("API_BEARER_TOKEN="):
                        return line.split("=", 1)[1].strip()
        
        # Fallback para token de teste
        return "test-token-12345"
    
    def log_test(self, name: str, success: bool, details: str = "", duration: float = 0):
        """Registra resultado do teste"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name} ({duration:.2f}s)")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "duration": duration
        })
    
    def test_health_endpoint(self):
        """Testa endpoint de health"""
        print("\n🏥 Testando Health Endpoint...")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", {})
                
                # Verifica componentes essenciais
                required_components = ["memory", "simple_rag", "lead_researcher"]
                missing_components = [comp for comp in required_components if not components.get(comp)]
                
                if missing_components:
                    self.log_test(
                        "Health Check", 
                        False, 
                        f"Componentes não funcionais: {missing_components}",
                        duration
                    )
                else:
                    self.log_test(
                        "Health Check", 
                        True, 
                        f"Status: {data.get('status')}, Uptime: {data.get('uptime_seconds', 0):.1f}s",
                        duration
                    )
            else:
                self.log_test("Health Check", False, f"Status: {response.status_code}", duration)
                
        except Exception as e:
            self.log_test("Health Check", False, f"Erro: {str(e)}", time.time() - start_time)
    
    def test_authentication(self):
        """Testa autenticação da API"""
        print("\n🔐 Testando Autenticação...")
        
        # Teste sem token
        start_time = time.time()
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/research",
                json={"query": "test", "use_multiagent": True},
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Auth - No Token", True, "Rejeitou corretamente sem token", duration)
            else:
                self.log_test("Auth - No Token", False, f"Status inesperado: {response.status_code}", duration)
        except Exception as e:
            self.log_test("Auth - No Token", False, f"Erro: {str(e)}", duration)
        
        # Teste com token inválido
        start_time = time.time()
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/research",
                json={"query": "test", "use_multiagent": True},
                headers={"Authorization": "Bearer invalid-token", "Content-Type": "application/json"},
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Auth - Invalid Token", True, "Rejeitou token inválido", duration)
            else:
                self.log_test("Auth - Invalid Token", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("Auth - Invalid Token", False, f"Erro: {str(e)}", duration)
    
    def test_simple_search(self):
        """Testa busca simples"""
        print("\n🔍 Testando Busca Simples...")
        start_time = time.time()
        
        try:
            query_data = {
                "query": "What is Zep?",
                "collection_name": "pdf_documents",
                "top_k": 3
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/research/simple",
                json=query_data,
                headers=self.headers,
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    sources = data.get("sources", [])
                    self.log_test(
                        "Simple Search", 
                        True, 
                        f"Encontrados {len(sources)} documentos",
                        duration
                    )
                else:
                    self.log_test("Simple Search", False, data.get("message", "Unknown error"), duration)
            else:
                self.log_test("Simple Search", False, f"Status: {response.status_code}", duration)
                
        except Exception as e:
            self.log_test("Simple Search", False, f"Erro: {str(e)}", time.time() - start_time)
    
    def test_multiagent_research(self):
        """Testa pesquisa multi-agente"""
        print("\n🤖 Testando Pesquisa Multi-Agente...")
        start_time = time.time()
        
        try:
            query_data = {
                "query": "How does Zep implement temporal knowledge graphs for AI agent memory?",
                "use_multiagent": True,
                "max_subagents": 2,
                "timeout": 120
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/research",
                json=query_data,
                headers=self.headers,
                timeout=150  # Timeout maior para multi-agent
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", "")
                    agent_id = data.get("agent_id", "")
                    status = data.get("status", "")
                    processing_time = data.get("processing_time", 0)
                    
                    # Verifica indicadores de qualidade
                    quality_indicators = []
                    if "gpt-4.1" in result:
                        quality_indicators.append("Coordinator GPT-4.1")
                    if "Advanced AI Critical Analysis" in result:
                        quality_indicators.append("Advanced Synthesis")
                    if "Subagents Processed" in result:
                        quality_indicators.append("Multi-agent Execution")
                    
                    self.log_test(
                        "Multi-Agent Research", 
                        True, 
                        f"Status: {status}, Agent: {agent_id[:8]}..., Time: {processing_time:.1f}s, Quality: {len(quality_indicators)}/3",
                        duration
                    )
                else:
                    self.log_test("Multi-Agent Research", False, data.get("message", "Unknown error"), duration)
            else:
                self.log_test("Multi-Agent Research", False, f"Status: {response.status_code}", duration)
                
        except Exception as e:
            self.log_test("Multi-Agent Research", False, f"Erro: {str(e)}", time.time() - start_time)
    
    def test_focus_areas(self):
        """Testa diferentes focus areas"""
        print("\n🎯 Testando Focus Areas...")
        
        test_queries = [
            ("Conceptual", "What are temporal knowledge graphs?"),
            ("Technical", "How to implement Zep in Python?"),
            ("Comparative", "Zep vs MemGPT comparison for chatbots")
        ]
        
        for focus_name, query in test_queries:
            start_time = time.time()
            try:
                query_data = {
                    "query": query,
                    "use_multiagent": True,
                    "max_subagents": 2,
                    "timeout": 60
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/research",
                    json=query_data,
                    headers=self.headers,
                    timeout=80
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        result = data.get("result", "")
                        # Verifica se o focus foi utilizado
                        focus_mentioned = focus_name.lower() in result.lower()
                        self.log_test(
                            f"Focus Area - {focus_name}", 
                            True, 
                            f"Focus detectado: {focus_mentioned}",
                            duration
                        )
                    else:
                        self.log_test(f"Focus Area - {focus_name}", False, "Request failed", duration)
                else:
                    self.log_test(f"Focus Area - {focus_name}", False, f"Status: {response.status_code}", duration)
                    
            except Exception as e:
                self.log_test(f"Focus Area - {focus_name}", False, f"Erro: {str(e)}", time.time() - start_time)
    
    def test_document_management(self):
        """Testa endpoints de gerenciamento de documentos"""
        print("\n📚 Testando Gerenciamento de Documentos...")
        
        # Listar documentos
        start_time = time.time()
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/stats",
                headers=self.headers,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                total_docs = data.get("total_documents", 0)
                self.log_test("Document List", True, f"Total: {total_docs} documentos", duration)
            else:
                self.log_test("Document List", False, f"Status: {response.status_code}", duration)
                
        except Exception as e:
            self.log_test("Document List", False, f"Erro: {str(e)}", time.time() - start_time)
    
    def test_statistics(self):
        """Testa endpoint de estatísticas"""
        print("\n📊 Testando Estatísticas...")
        start_time = time.time()
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/stats",
                headers=self.headers,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                system_stats = data.get("system_stats", {})
                agent_stats = data.get("agent_stats", {})
                
                total_queries = system_stats.get("total_queries", 0)
                multiagent_queries = system_stats.get("multiagent_queries", 0)
                
                self.log_test(
                    "Statistics", 
                    True, 
                    f"Total queries: {total_queries}, Multi-agent: {multiagent_queries}",
                    duration
                )
            else:
                self.log_test("Statistics", False, f"Status: {response.status_code}", duration)
                
        except Exception as e:
            self.log_test("Statistics", False, f"Erro: {str(e)}", time.time() - start_time)
    
    def test_performance_stress(self):
        """Teste de stress/performance"""
        print("\n⚡ Testando Performance (Stress Test)...")
        
        # Múltiplas requisições simultâneas
        queries = [
            "What is Zep?",
            "How does temporal knowledge work?",
            "Explain Zep architecture"
        ]
        
        start_time = time.time()
        successful_requests = 0
        
        for i, query in enumerate(queries):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/simple",
                    json={"query": query, "top_k": 3},
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200 and response.json().get("success"):
                    successful_requests += 1
                    
            except Exception:
                pass
        
        duration = time.time() - start_time
        success_rate = (successful_requests / len(queries)) * 100
        
        self.log_test(
            "Stress Test", 
            success_rate >= 70,  # 70% success rate mínimo
            f"Success rate: {success_rate:.1f}% ({successful_requests}/{len(queries)})",
            duration
        )
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando Testes da API RAG Multi-Agent System")
        print(f"Base URL: {self.base_url}")
        print(f"Bearer Token: {self.bearer_token[:10]}..." if self.bearer_token else "No token")
        
        total_start_time = time.time()
        
        # Executa todos os testes
        self.test_health_endpoint()
        self.test_authentication()
        self.test_simple_search()
        self.test_multiagent_research()
        self.test_focus_areas()
        self.test_document_management()
        self.test_statistics()
        self.test_performance_stress()
        
        total_duration = time.time() - total_start_time
        
        # Relatório final
        passed_tests = sum(1 for r in self.test_results if r["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 RELATÓRIO FINAL")
        print(f"{'='*50}")
        print(f"Total de testes: {total_tests}")
        print(f"Testes aprovados: {passed_tests}")
        print(f"Testes falhados: {total_tests - passed_tests}")
        print(f"Taxa de sucesso: {success_rate:.1f}%")
        print(f"Tempo total: {total_duration:.2f}s")
        
        # Salva relatório em arquivo
        self.save_report()
        
        # Status final
        if success_rate >= 80:
            print("\n🎉 API está funcionando bem!")
            return True
        elif success_rate >= 60:
            print("\n⚠️ API tem alguns problemas, mas está funcional")
            return True
        else:
            print("\n❌ API tem problemas críticos")
            return False
    
    def save_report(self):
        """Salva relatório em arquivo"""
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r["success"]),
            "results": self.test_results
        }
        
        report_path = Path(__file__).parent.parent / "logs" / "api_test_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📝 Relatório salvo em: {report_path}")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Testa API RAG Multi-Agent System")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base da API")
    parser.add_argument("--token", help="Bearer token para autenticação")
    parser.add_argument("--quick", action="store_true", help="Executa apenas testes básicos")
    
    args = parser.parse_args()
    
    tester = APITester(base_url=args.url, bearer_token=args.token)
    
    if args.quick:
        print("🏃 Modo rápido - apenas testes essenciais")
        tester.test_health_endpoint()
        tester.test_authentication()
        tester.test_simple_search()
    else:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()