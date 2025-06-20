#!/usr/bin/env python3
"""
Teste completo do pipeline RAG Multi-Agent System
Testa desde a indexação até a pesquisa multi-agente
"""
import asyncio
import json
import time
import requests
from pathlib import Path
import sys
import os
import subprocess
import tempfile
import socket
import atexit
from typing import Dict, List, Any

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

class FullPipelineTester:
    """Testador completo do pipeline RAG Multi-Agent"""
    
    def __init__(self, base_url: str = "http://localhost:8000", bearer_token: str = None, auto_start_api: bool = True):
        self.base_url = base_url
        self.bearer_token = bearer_token or self._get_bearer_token()
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.test_results = []
        self.collection_name = f"test_pipeline_{int(time.time())}"
        self.api_process = None
        self.auto_start_api = auto_start_api
        
        # Registra cleanup automático
        atexit.register(self.cleanup)
        
        # Verifica se API está rodando, senão inicia
        if self.auto_start_api and not self._is_api_running():
            self._start_api()
        
        # URLs de teste para indexação
        self.test_documents = [
            {
                "name": "Zep Paper",
                "url": "https://arxiv.org/pdf/2501.13956",
                "expected_pages": 12,
                "test_queries": [
                    "What is Zep?",
                    "How does Zep implement temporal knowledge graphs?",
                    "What are the advantages of Zep for AI agents?"
                ]
            }
        ]
    
    def _get_bearer_token(self) -> str:
        """Obtém token do arquivo .env"""
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("API_BEARER_TOKEN="):
                        return line.split("=", 1)[1].strip()
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
            "duration": duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def check_api_health(self) -> bool:
        """Verifica se a API está funcionando"""
        print("🏥 Verificando saúde da API...")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", {})
                
                all_healthy = all(components.values())
                
                self.log_test(
                    "API Health Check",
                    all_healthy,
                    f"Status: {data.get('status')}, Components: {components}",
                    duration
                )
                return all_healthy
            else:
                self.log_test("API Health Check", False, f"Status: {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_test("API Health Check", False, f"Erro: {str(e)}", time.time() - start_time)
            return False
    
    def clean_test_environment(self):
        """Limpa ambiente de teste"""
        print("🧹 Limpando ambiente de teste...")
        
        # Deleta collection de teste se existir
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/documents/{self.collection_name}",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                print(f"    Collection {self.collection_name} deletada")
            else:
                print(f"    Collection {self.collection_name} não existia ou erro ao deletar")
        except Exception as e:
            print(f"    Erro ao deletar collection: {e}")
        
        # Deleta imagens de teste
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/images",
                headers=self.headers,
                timeout=30
            )
            print("    Imagens temporárias limpas")
        except Exception as e:
            print(f"    Erro ao limpar imagens: {e}")
    
    def test_document_indexing(self) -> bool:
        """Testa indexação de documentos"""
        print("\n📚 Testando Indexação de Documentos...")
        
        all_success = True
        
        for doc in self.test_documents:
            print(f"\n📄 Indexando: {doc['name']}")
            start_time = time.time()
            
            try:
                index_data = {
                    "pdf_url": doc["url"],
                    "collection_name": self.collection_name,
                    "extract_images": True
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/index",
                    json=index_data,
                    headers=self.headers,
                    timeout=300  # 5 minutos para indexação
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        details = data.get("details", {})
                        pages_processed = details.get("pages_processed", 0)
                        images_extracted = details.get("images_extracted", 0)
                        text_chunks = details.get("text_chunks", 0)
                        
                        # Verifica se o número de páginas está correto
                        pages_ok = pages_processed >= doc["expected_pages"] * 0.8  # 80% tolerance
                        
                        self.log_test(
                            f"Indexing - {doc['name']}",
                            pages_ok,
                            f"Pages: {pages_processed}/{doc['expected_pages']}, Images: {images_extracted}, Chunks: {text_chunks}",
                            duration
                        )
                        
                        if not pages_ok:
                            all_success = False
                    else:
                        self.log_test(f"Indexing - {doc['name']}", False, data.get("message", "Unknown error"), duration)
                        all_success = False
                else:
                    self.log_test(f"Indexing - {doc['name']}", False, f"Status: {response.status_code}", duration)
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Indexing - {doc['name']}", False, f"Erro: {str(e)}", time.time() - start_time)
                all_success = False
        
        return all_success
    
    def test_document_verification(self) -> bool:
        """Verifica se documentos foram indexados corretamente"""
        print("\n🔍 Verificando Indexação...")
        start_time = time.time()
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/documents/{self.collection_name}",
                headers=self.headers,
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                total_documents = data.get("total_documents", 0)
                documents = data.get("documents", [])
                
                success = total_documents > 0
                
                self.log_test(
                    "Document Verification",
                    success,
                    f"Total documents: {total_documents}, Collections: {len(documents)}",
                    duration
                )
                return success
            else:
                self.log_test("Document Verification", False, f"Status: {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_test("Document Verification", False, f"Erro: {str(e)}", time.time() - start_time)
            return False
    
    def test_simple_rag_search(self) -> bool:
        """Testa busca RAG simples"""
        print("\n🔍 Testando Busca RAG Simples...")
        
        all_success = True
        
        # Usa queries dos documentos de teste
        test_queries = []
        for doc in self.test_documents:
            test_queries.extend(doc["test_queries"])
        
        for i, query in enumerate(test_queries):
            start_time = time.time()
            
            try:
                query_data = {
                    "query": query,
                    "collection_name": self.collection_name,
                    "top_k": 5
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/simple",
                    json=query_data,
                    headers=self.headers,
                    timeout=60
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        sources = data.get("sources", [])
                        result_length = len(data.get("result", ""))
                        
                        # Verifica se encontrou documentos e gerou resposta
                        has_sources = len(sources) > 0
                        has_content = result_length > 100  # Resposta mínima de 100 chars
                        
                        success = has_sources and has_content
                        
                        self.log_test(
                            f"Simple RAG - Query {i+1}",
                            success,
                            f"Sources: {len(sources)}, Response length: {result_length} chars",
                            duration
                        )
                        
                        if not success:
                            all_success = False
                    else:
                        self.log_test(f"Simple RAG - Query {i+1}", False, data.get("message", "Unknown error"), duration)
                        all_success = False
                else:
                    self.log_test(f"Simple RAG - Query {i+1}", False, f"Status: {response.status_code}", duration)
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Simple RAG - Query {i+1}", False, f"Erro: {str(e)}", time.time() - start_time)
                all_success = False
        
        return all_success
    
    def test_multiagent_research(self) -> bool:
        """Testa sistema multi-agente completo"""
        print("\n🤖 Testando Sistema Multi-Agente...")
        
        all_success = True
        
        # Queries específicas para testar diferentes focus areas
        multiagent_queries = [
            {
                "query": "What is Zep and how does it work?",
                "expected_focus": ["conceptual", "overview"],
                "max_subagents": 2
            },
            {
                "query": "How to implement Zep temporal knowledge graphs in Python?",
                "expected_focus": ["technical", "examples"],
                "max_subagents": 2
            },
            {
                "query": "Compare Zep with other memory systems for AI agents",
                "expected_focus": ["comparative"],
                "max_subagents": 2
            },
            {
                "query": "Show me practical examples of Zep in production environments",
                "expected_focus": ["examples", "applications"],
                "max_subagents": 2
            },
            {
                "query": "Give me a comprehensive overview of Zep architecture",
                "expected_focus": ["overview", "general"],
                "max_subagents": 3
            }
        ]
        
        for i, test_case in enumerate(multiagent_queries):
            print(f"\n🧠 Multi-Agent Test {i+1}: {test_case['query'][:50]}...")
            start_time = time.time()
            
            try:
                query_data = {
                    "query": test_case["query"],
                    "use_multiagent": True,
                    "max_subagents": test_case["max_subagents"],
                    "timeout": 180
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/research",
                    json=query_data,
                    headers=self.headers,
                    timeout=200  # Timeout maior para multi-agent
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        result = data.get("result", "")
                        agent_id = data.get("agent_id", "")
                        status = data.get("status", "")
                        processing_time = data.get("processing_time", 0)
                        
                        # Verifica indicadores de qualidade multi-agente
                        quality_checks = {
                            "gpt_4_1_coordinator": "gpt-4.1" in result,
                            "advanced_synthesis": "Advanced AI Critical Analysis" in result,
                            "subagents_processed": "Subagents Processed" in result,
                            "reasoning_trace": "Research Metadata" in result,
                            "coordinator_model": "Coordinator Model" in result
                        }
                        
                        passed_checks = sum(quality_checks.values())
                        total_checks = len(quality_checks)
                        
                        success = (
                            status == "COMPLETED" and
                            passed_checks >= total_checks * 0.6 and  # 60% dos checks passaram
                            len(result) > 300 and  # Resposta substantiva
                            processing_time < 180  # Tempo razoável
                        )
                        
                        self.log_test(
                            f"Multi-Agent Test {i+1}",
                            success,
                            f"Status: {status}, Quality: {passed_checks}/{total_checks}, Time: {processing_time:.1f}s, Length: {len(result)} chars",
                            duration
                        )
                        
                        if not success:
                            all_success = False
                    else:
                        self.log_test(f"Multi-Agent Test {i+1}", False, data.get("message", "Unknown error"), duration)
                        all_success = False
                else:
                    self.log_test(f"Multi-Agent Test {i+1}", False, f"Status: {response.status_code}", duration)
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Multi-Agent Test {i+1}", False, f"Erro: {str(e)}", time.time() - start_time)
                all_success = False
        
        return all_success
    
    def test_reasoning_continuity(self):
        """Testa continuidade do reasoning ReAct"""
        print("\n🧠 Testando Continuidade do Reasoning...")
        start_time = time.time()
        
        try:
            # Query complexa que deve gerar reasoning detalhado
            query_data = {
                "query": "Analyze how Zep's temporal knowledge graph architecture compares to traditional memory systems and explain implementation considerations",
                "use_multiagent": True,
                "max_subagents": 3,
                "timeout": 150
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/research",
                json=query_data,
                headers=self.headers,
                timeout=180
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", "")
                    
                    # Verifica elementos de reasoning
                    reasoning_elements = {
                        "coordinator_model": "Coordinator Model" in result,
                        "synthesis_method": "Synthesis Method" in result,
                        "subagents_metadata": "Subagents Processed" in result,
                        "decomposition_info": "Decomposition" in result,
                        "success_rate": "Success Rate" in result
                    }
                    
                    reasoning_score = sum(reasoning_elements.values())
                    
                    self.log_test(
                        "Reasoning Continuity",
                        reasoning_score >= 3,  # Pelo menos 3 elementos de reasoning
                        f"Reasoning elements: {reasoning_score}/5 - {reasoning_elements}",
                        duration
                    )
                else:
                    self.log_test("Reasoning Continuity", False, data.get("message"), duration)
            else:
                self.log_test("Reasoning Continuity", False, f"Status: {response.status_code}", duration)
                
        except Exception as e:
            self.log_test("Reasoning Continuity", False, f"Erro: {str(e)}", time.time() - start_time)
    
    def test_performance_metrics(self):
        """Testa métricas de performance"""
        print("\n⚡ Testando Performance...")
        
        # Testa múltiplas queries simultâneas (stress test)
        queries = [
            "What is Zep?",
            "How does temporal knowledge work?",
            "Implementation details of Zep"
        ]
        
        start_time = time.time()
        successful_requests = 0
        total_response_time = 0
        
        for query in queries:
            try:
                query_start = time.time()
                response = self.session.post(
                    f"{self.base_url}/api/v1/simple",
                    json={"query": query, "collection_name": self.collection_name, "top_k": 3},
                    headers=self.headers,
                    timeout=60
                )
                query_duration = time.time() - query_start
                total_response_time += query_duration
                
                if response.status_code == 200 and response.json().get("success"):
                    successful_requests += 1
                    
            except Exception:
                pass
        
        total_duration = time.time() - start_time
        average_response_time = total_response_time / len(queries) if queries else 0
        success_rate = (successful_requests / len(queries)) * 100
        
        self.log_test(
            "Performance Stress Test",
            success_rate >= 80 and average_response_time < 30,
            f"Success: {success_rate:.1f}%, Avg response: {average_response_time:.2f}s",
            total_duration
        )
    
    def generate_comprehensive_report(self):
        """Gera relatório abrangente"""
        print("\n📊 Gerando Relatório Abrangente...")
        
        # Calcula métricas gerais
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Agrupa por categoria
        categories = {}
        for result in self.test_results:
            category = result["name"].split(" - ")[0].split(" ")[0]
            if category not in categories:
                categories[category] = {"passed": 0, "total": 0, "duration": 0}
            
            categories[category]["total"] += 1
            categories[category]["duration"] += result["duration"]
            if result["success"]:
                categories[category]["passed"] += 1
        
        # Report estruturado
        report = {
            "pipeline_test_summary": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "collection_name": self.collection_name,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2)
            },
            "category_breakdown": {},
            "detailed_results": self.test_results,
            "recommendations": []
        }
        
        # Breakdown por categoria
        for category, stats in categories.items():
            cat_success_rate = (stats["passed"] / stats["total"]) * 100
            report["category_breakdown"][category] = {
                "success_rate": round(cat_success_rate, 2),
                "passed": stats["passed"],
                "total": stats["total"],
                "avg_duration": round(stats["duration"] / stats["total"], 2)
            }
        
        # Recomendações baseadas nos resultados
        if success_rate < 80:
            report["recommendations"].append("Sistema precisa de investigação - taxa de sucesso abaixo de 80%")
        
        if any(cat["success_rate"] < 50 for cat in report["category_breakdown"].values()):
            report["recommendations"].append("Algumas categorias têm baixa performance - verificar logs detalhados")
        
        indexing_cat = report["category_breakdown"].get("Indexing", {})
        if indexing_cat.get("success_rate", 100) < 90:
            report["recommendations"].append("Problemas na indexação - verificar conectividade e recursos")
        
        multiagent_cat = report["category_breakdown"].get("Multi-Agent", {})
        if multiagent_cat.get("avg_duration", 0) > 60:
            report["recommendations"].append("Sistema multi-agente lento - considerar otimizações")
        
        # Salva relatório
        report_path = Path(__file__).parent.parent / "logs" / "full_pipeline_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📝 Relatório completo salvo em: {report_path}")
        return report
    
    def run_full_pipeline_test(self):
        """Executa teste completo do pipeline"""
        print("🚀 INICIANDO TESTE COMPLETO DO PIPELINE RAG MULTI-AGENT")
        print("="*60)
        
        total_start_time = time.time()
        
        # 1. Verificar saúde da API
        if not self.check_api_health():
            print("❌ API não está saudável. Abortando testes.")
            return False
        
        # 2. Limpar ambiente
        self.clean_test_environment()
        
        # 3. Teste de indexação
        indexing_success = self.test_document_indexing()
        
        # 4. Verificar indexação
        verification_success = self.test_document_verification()
        
        # 5. Teste RAG simples
        simple_rag_success = self.test_simple_rag_search()
        
        # 6. Teste multi-agente
        multiagent_success = self.test_multiagent_research()
        
        # 7. Teste de reasoning
        self.test_reasoning_continuity()
        
        # 8. Teste de performance
        self.test_performance_metrics()
        
        # 9. Limpar ambiente de teste
        print("\n🧹 Limpando ambiente de teste...")
        self.clean_test_environment()
        
        total_duration = time.time() - total_start_time
        
        # 10. Gerar relatório
        report = self.generate_comprehensive_report()
        
        # Resultado final
        print(f"\n🏁 TESTE COMPLETO FINALIZADO")
        print(f"{'='*60}")
        print(f"Tempo total: {total_duration:.2f}s")
        print(f"Taxa de sucesso: {report['pipeline_test_summary']['success_rate']:.1f}%")
        
        # Status por categoria
        print("\n📋 Resultado por Categoria:")
        for category, stats in report["category_breakdown"].items():
            status = "✅" if stats["success_rate"] >= 80 else "⚠️" if stats["success_rate"] >= 60 else "❌"
            print(f"{status} {category}: {stats['success_rate']:.1f}% ({stats['passed']}/{stats['total']})")
        
        # Recomendações
        if report["recommendations"]:
            print("\n💡 Recomendações:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")
        
        # Verifica se pipeline está funcionando
        critical_components = [indexing_success, verification_success, simple_rag_success, multiagent_success]
        pipeline_working = all(critical_components)
        
        if pipeline_working:
            print("\n🎉 PIPELINE ESTÁ FUNCIONANDO CORRETAMENTE!")
            return True
        else:
            print("\n❌ PIPELINE TEM PROBLEMAS CRÍTICOS")
            return False


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste completo do pipeline RAG Multi-Agent")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base da API")
    parser.add_argument("--token", help="Bearer token para autenticação")
    parser.add_argument("--collection", help="Nome da collection de teste (opcional)")
    parser.add_argument("--no-auto-start", action="store_true", help="Não inicia a API automaticamente")
    
    args = parser.parse_args()
    
    tester = FullPipelineTester(
        base_url=args.url, 
        bearer_token=args.token,
        auto_start_api=not args.no_auto_start
    )
    
    if args.collection:
        tester.collection_name = args.collection
    
    success = tester.run_full_pipeline_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()