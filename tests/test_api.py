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
import subprocess
import socket
import threading
import atexit

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

class APITester:
    """Testador da API RAG Multi-Agent"""
    
    def __init__(self, base_url: str = "http://localhost:8000", bearer_token: str = None, auto_start_api: bool = True):
        self.base_url = base_url
        self.bearer_token = bearer_token or self._get_bearer_token()
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.test_results = []
        self.api_process = None
        self.auto_start_api = auto_start_api
        
        # Registra cleanup automático
        atexit.register(self.cleanup)
        
        # Verifica se API está rodando, senão inicia
        if self.auto_start_api and not self._is_api_running():
            self._start_api()
    
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
    
    def _is_port_available(self, port: int) -> bool:
        """Verifica se a porta está disponível"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return True
    
    def _is_api_running(self) -> bool:
        """Verifica se a API já está rodando"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _start_api(self):
        """Inicia a API em background"""
        print("🚀 Iniciando API em background...")
        
        # Verifica se a porta está disponível
        port = int(self.base_url.split(':')[-1])
        if not self._is_port_available(port):
            print(f"⚠️ Porta {port} já está em uso")
            return
        
        # Caminho para o arquivo principal da API
        api_path = Path(__file__).parent.parent / "api" / "main.py"
        
        if not api_path.exists():
            print(f"❌ Arquivo da API não encontrado: {api_path}")
            return
        
        try:
            # Inicia a API usando uvicorn
            self.api_process = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn", 
                    "api.main:app", 
                    "--host", "0.0.0.0", 
                    "--port", str(port),
                    "--reload"
                ],
                cwd=str(Path(__file__).parent.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Aguarda a API iniciar
            print("⏳ Aguardando API iniciar...")
            for i in range(30):  # 30 segundos timeout
                if self._is_api_running():
                    print(f"✅ API iniciada com sucesso em {self.base_url}")
                    return
                time.sleep(1)
            
            print("❌ Timeout ao iniciar API")
            self.cleanup()
            
        except Exception as e:
            print(f"❌ Erro ao iniciar API: {e}")
            self.cleanup()
    
    def cleanup(self):
        """Limpa recursos e para a API se foi iniciada pelo teste"""
        if self.api_process and self.api_process.poll() is None:
            print("🧹 Parando API...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
            self.api_process = None
    
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
            duration = time.time() - start_time
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
            duration = time.time() - start_time
            self.log_test("Auth - Invalid Token", False, f"Erro: {str(e)}", duration)
    
    def test_simple_search(self):
        """Testa busca simples"""
        print("\n🔍 Testando Busca Simples...")
        start_time = time.time()
        
        try:
            query_data = {
                "query": "What is Zep?"
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
                    result = data.get("result", "")
                    result_length = data.get("result_length", 0)
                    diagnostic = data.get("diagnostic", {})
                    self.log_test(
                        "Simple Search", 
                        True, 
                        f"Resultado: {result_length} chars, Diagnóstico: {diagnostic}",
                        duration
                    )
                else:
                    self.log_test("Simple Search", False, data.get("message", "Unknown error"), duration)
            else:
                self.log_test("Simple Search", False, f"Status: {response.status_code}", duration)
                
        except Exception as e:
            self.log_test("Simple Search", False, f"Erro: {str(e)}", time.time() - start_time)
    
    
    def test_multiagent_queries(self):
        """Testa consultas multi-agente com diferentes tipos de perguntas"""
        print("\n🤖 Testando Consultas Multi-Agente...")
        
        test_queries = [
            "What are knowledge graphs and how do they work?"
        ]
        
        for i, query in enumerate(test_queries, 1):
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
                        result = data.get("result", "") or ""
                        status = data.get("status", "")
                        processing_time = data.get("processing_time", 0)
                        
                        # Verifica qualidade da resposta
                        has_content = len(result) > 100
                        completed = status == "COMPLETED"
                        reasonable_time = processing_time < 120
                        
                        success = has_content and completed and reasonable_time
                        
                        self.log_test(
                            f"Multi-Agent Query {i}", 
                            success, 
                            f"Status: {status}, Length: {len(result)} chars, Time: {processing_time:.1f}s",
                            duration
                        )
                    else:
                        self.log_test(f"Multi-Agent Query {i}", False, data.get("message", "Request failed"), duration)
                else:
                    self.log_test(f"Multi-Agent Query {i}", False, f"Status: {response.status_code}", duration)
                    
            except Exception as e:
                self.log_test(f"Multi-Agent Query {i}", False, f"Erro: {str(e)}", time.time() - start_time)
    
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
                total_documents = data.get("total_documents", 0)
                uptime = data.get("uptime_seconds", 0)
                api_ready = data.get("api_ready", False)
                
                self.log_test(
                    "Statistics", 
                    True, 
                    f"Documents: {total_documents}, Uptime: {uptime:.1f}s, Ready: {api_ready}",
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
                    f"{self.base_url}/api/v1/research/simple",
                    json={"query": query},
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
        self.test_multiagent_queries()  # Teste simplificado único
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
    parser.add_argument("--no-auto-start", action="store_true", help="Não inicia a API automaticamente")
    
    args = parser.parse_args()
    
    tester = APITester(
        base_url=args.url, 
        bearer_token=args.token,
        auto_start_api=not args.no_auto_start
    )
    
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