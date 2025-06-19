#!/usr/bin/env python3
"""
Teste específico sobre Zep (camada de memória) usando o PDF indexado
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


class ZepMemoryTester:
    def __init__(self):
        self.server_process = None
        self.client = httpx.Client(timeout=120.0)  # Timeout maior para consultas complexas
    
    def start_server_dev_mode(self):
        """Inicia o servidor em modo desenvolvimento"""
        print("🚀 Iniciando servidor para teste do Zep...")
        
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
            time.sleep(15)  # Aguarda inicialização
            
            if self.server_process.poll() is None:
                print("✅ Servidor iniciado")
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
    
    def test_simple_rag_zep_search(self):
        """Testa busca simples sobre Zep"""
        print("\\n🔍 TESTE SIMPLERAG - BUSCA SOBRE ZEP")
        print("-" * 60)
        
        zep_queries = [
            "What is Zep memory layer?",
            "How does Zep work?",
            "Zep features and capabilities",
            "Zep architecture"
        ]
        
        results = []
        
        for i, query in enumerate(zep_queries, 1):
            print(f"\\n📍 Query {i}: {query}")
            try:
                response = self.client.post(
                    f"{API_BASE_URL}/api/v1/research/simple",
                    json={"query": query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    result = data.get("result", "")
                    result_length = data.get("result_length", len(result))
                    processing_time = data.get("processing_time", 0)
                    
                    print(f"   ✅ Status: {success}")
                    print(f"   📊 Tamanho: {result_length} caracteres")
                    print(f"   ⏱️ Tempo: {processing_time:.3f}s")
                    
                    if result and "zep" in result.lower():
                        print("   🎯 Contém informações sobre Zep!")
                        print(f"   📄 Preview: {result[:200]}...")
                    elif result:
                        print(f"   📄 Resultado: {result[:150]}...")
                    else:
                        print("   ⚠️ Nenhum resultado")
                    
                    results.append({
                        "query": query,
                        "success": success,
                        "has_zep_content": "zep" in result.lower() if result else False,
                        "result_length": result_length,
                        "processing_time": processing_time,
                        "result": result
                    })
                else:
                    print(f"   ❌ Erro: {response.status_code}")
                    results.append({
                        "query": query,
                        "success": False,
                        "has_zep_content": False,
                        "result_length": 0,
                        "processing_time": 0,
                        "result": ""
                    })
            
            except Exception as e:
                print(f"   ❌ Exceção: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "has_zep_content": False,
                    "result_length": 0,
                    "processing_time": 0,
                    "result": ""
                })
        
        return results
    
    def test_multiagent_zep_research(self):
        """Testa pesquisa multi-agente sobre Zep"""
        print("\\n🤖 TESTE MULTI-AGENTE - PESQUISA SOBRE ZEP")
        print("-" * 60)
        
        complex_zep_queries = [
            {
                "query": "Explain Zep memory layer architecture and implementation details",
                "objective": "Provide comprehensive technical analysis of Zep for developers"
            },
            {
                "query": "What are the main features and benefits of using Zep?",
                "objective": "Understand Zep capabilities for product evaluation"
            },
            {
                "query": "How does Zep compare to other memory solutions?",
                "objective": "Comparative analysis for technology selection"
            }
        ]
        
        results = []
        
        for i, query_obj in enumerate(complex_zep_queries, 1):
            query = query_obj["query"]
            objective = query_obj["objective"]
            
            print(f"\\n📍 Multi-Agent Query {i}:")
            print(f"   🔍 Query: {query}")
            print(f"   🎯 Objective: {objective}")
            
            try:
                response = self.client.post(
                    f"{API_BASE_URL}/api/v1/research",
                    json={"query": query, "objective": objective}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    result = data.get("result", "")
                    agent_id = data.get("agent_id", "")
                    status = data.get("status", "")
                    processing_time = data.get("processing_time", 0)
                    confidence_score = data.get("confidence_score")
                    sources = data.get("sources", [])
                    reasoning_trace = data.get("reasoning_trace")
                    
                    print(f"   ✅ Success: {success}")
                    print(f"   🤖 Agent: {agent_id}")
                    print(f"   📊 Status: {status}")
                    print(f"   ⏱️ Tempo: {processing_time:.3f}s")
                    print(f"   🎯 Confiança: {confidence_score}")
                    print(f"   📚 Fontes: {sources}")
                    
                    if reasoning_trace:
                        print(f"   🧠 Reasoning: Disponível")
                    
                    has_zep_content = "zep" in result.lower() if result else False
                    if has_zep_content:
                        print("   🎯 Contém informações sobre Zep!")
                        print(f"   📄 Resultado ({len(result)} chars): {result[:300]}...")
                    elif result:
                        print(f"   📄 Resultado: {result[:200]}...")
                    else:
                        print("   ⚠️ Nenhum resultado específico")
                    
                    results.append({
                        "query": query,
                        "objective": objective,
                        "success": success,
                        "status": status,
                        "has_zep_content": has_zep_content,
                        "result_length": len(result),
                        "processing_time": processing_time,
                        "confidence_score": confidence_score,
                        "sources": sources,
                        "agent_id": agent_id,
                        "result": result
                    })
                else:
                    print(f"   ❌ Erro: {response.status_code}")
                    results.append({
                        "query": query,
                        "objective": objective,
                        "success": False,
                        "status": "ERROR",
                        "has_zep_content": False,
                        "result_length": 0,
                        "processing_time": 0,
                        "confidence_score": 0,
                        "sources": [],
                        "agent_id": "",
                        "result": ""
                    })
            
            except Exception as e:
                print(f"   ❌ Exceção: {e}")
                results.append({
                    "query": query,
                    "objective": objective,
                    "success": False,
                    "status": "EXCEPTION",
                    "has_zep_content": False,
                    "result_length": 0,
                    "processing_time": 0,
                    "confidence_score": 0,
                    "sources": [],
                    "agent_id": "",
                    "result": ""
                })
        
        return results
    
    def test_direct_rag_zep_search(self):
        """Testa busca direta via Lead Researcher sobre Zep"""
        print("\\n🎯 TESTE RAG DIRETO - BUSCA SOBRE ZEP")
        print("-" * 60)
        
        direct_queries = [
            "Zep memory layer",
            "Zep features",
            "Zep architecture design",
            "Zep implementation"
        ]
        
        results = []
        
        for i, query in enumerate(direct_queries, 1):
            print(f"\\n📍 Direct Query {i}: {query}")
            try:
                response = self.client.post(
                    f"{API_BASE_URL}/api/v1/research/direct",
                    json={"query": query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    result = data.get("result", "")
                    status = data.get("status", "")
                    processing_time = data.get("processing_time", 0)
                    confidence_score = data.get("confidence_score", 0)
                    sources = data.get("sources", [])
                    
                    print(f"   ✅ Success: {success}")
                    print(f"   📊 Status: {status}")
                    print(f"   ⏱️ Tempo: {processing_time:.3f}s")
                    print(f"   🎯 Confiança: {confidence_score}")
                    print(f"   📚 Fontes: {sources}")
                    
                    has_zep_content = "zep" in result.lower() if result else False
                    if has_zep_content:
                        print("   🎯 Contém informações sobre Zep!")
                        print(f"   📄 Resultado: {result[:250]}...")
                    elif result:
                        print(f"   📄 Resultado: {result[:150]}...")
                    else:
                        print("   ⚠️ Nenhum resultado")
                    
                    results.append({
                        "query": query,
                        "success": success,
                        "status": status,
                        "has_zep_content": has_zep_content,
                        "result_length": len(result),
                        "processing_time": processing_time,
                        "confidence_score": confidence_score,
                        "sources": sources,
                        "result": result
                    })
                else:
                    print(f"   ❌ Erro: {response.status_code}")
                    results.append({
                        "query": query,
                        "success": False,
                        "status": "ERROR",
                        "has_zep_content": False,
                        "result_length": 0,
                        "processing_time": 0,
                        "confidence_score": 0,
                        "sources": [],
                        "result": ""
                    })
            
            except Exception as e:
                print(f"   ❌ Exceção: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "status": "EXCEPTION",
                    "has_zep_content": False,
                    "result_length": 0,
                    "processing_time": 0,
                    "confidence_score": 0,
                    "sources": [],
                    "result": ""
                })
        
        return results
    
    def test_reasoning_about_zep(self):
        """Testa o sistema de reasoning sobre Zep"""
        print("\\n🧠 TESTE REASONING - ANÁLISE SOBRE ZEP")
        print("-" * 60)
        
        reasoning_query = {
            "query": "Analyze Zep memory layer and explain its key components and benefits",
            "objective": "Provide detailed technical analysis with reasoning steps"
        }
        
        print(f"📍 Reasoning Query: {reasoning_query['query']}")
        print(f"🎯 Objective: {reasoning_query['objective']}")
        
        try:
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research/test-reasoning",
                json=reasoning_query
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                plan_created = data.get("plan_created", False)
                plan_tasks = data.get("plan_tasks", 0)
                plan_details = data.get("plan_details", [])
                reasoning_available = data.get("reasoning_available", False)
                reasoning_type = data.get("reasoning_type", "")
                rag_info = data.get("rag_info", {})
                
                print(f"\\n   ✅ Success: {success}")
                print(f"   🗂️ Plano criado: {plan_created}")
                print(f"   📋 Tarefas no plano: {plan_tasks}")
                print(f"   🧠 Reasoning disponível: {reasoning_available}")
                print(f"   🔧 Tipo reasoning: {reasoning_type}")
                print(f"   🔗 RAG info: {rag_info}")
                
                if plan_details:
                    print("\\n   📋 Detalhes do Plano:")
                    for i, task in enumerate(plan_details, 1):
                        print(f"      {i}. {task}")
                
                return {
                    "success": success,
                    "plan_created": plan_created,
                    "plan_tasks": plan_tasks,
                    "reasoning_available": reasoning_available,
                    "reasoning_type": reasoning_type,
                    "plan_details": plan_details,
                    "rag_info": rag_info
                }
            else:
                print(f"   ❌ Erro: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            print(f"   ❌ Exceção: {e}")
            return {"success": False, "error": str(e)}
    
    def run_zep_tests(self):
        """Executa todos os testes sobre Zep"""
        print("🧠 TESTES ESPECÍFICOS SOBRE ZEP (CAMADA DE MEMÓRIA)")
        print("=" * 80)
        
        # Iniciar servidor
        if not self.start_server_dev_mode():
            return False
        
        try:
            # Aguardar inicialização
            print("⏳ Aguardando inicialização completa...")
            time.sleep(5)
            
            # Executar todos os testes
            print("\\n🔍 Iniciando testes sobre Zep...")
            
            simple_results = self.test_simple_rag_zep_search()
            multiagent_results = self.test_multiagent_zep_research()
            direct_results = self.test_direct_rag_zep_search()
            reasoning_results = self.test_reasoning_about_zep()
            
            # Análise dos resultados
            print("\\n" + "=" * 80)
            print("📊 ANÁLISE DOS RESULTADOS SOBRE ZEP:")
            
            # SimpleRAG
            simple_zep_found = sum(1 for r in simple_results if r["has_zep_content"])
            simple_total = len(simple_results)
            print(f"\\n🔍 SIMPLERAG: {simple_zep_found}/{simple_total} consultas encontraram conteúdo sobre Zep")
            
            for result in simple_results:
                status = "🎯" if result["has_zep_content"] else "❌"
                print(f"   {status} {result['query']} ({result['result_length']} chars)")
            
            # Multi-Agent
            multiagent_zep_found = sum(1 for r in multiagent_results if r["has_zep_content"])
            multiagent_total = len(multiagent_results)
            print(f"\\n🤖 MULTI-AGENTE: {multiagent_zep_found}/{multiagent_total} consultas encontraram conteúdo sobre Zep")
            
            for result in multiagent_results:
                status = "🎯" if result["has_zep_content"] else "❌"
                print(f"   {status} {result['query'][:50]}... ({result['result_length']} chars, {result['processing_time']:.2f}s)")
            
            # RAG Direto
            direct_zep_found = sum(1 for r in direct_results if r["has_zep_content"])
            direct_total = len(direct_results)
            print(f"\\n🎯 RAG DIRETO: {direct_zep_found}/{direct_total} consultas encontraram conteúdo sobre Zep")
            
            for result in direct_results:
                status = "🎯" if result["has_zep_content"] else "❌"
                print(f"   {status} {result['query']} ({result['result_length']} chars)")
            
            # Reasoning
            print(f"\\n🧠 REASONING: {'✅' if reasoning_results['success'] else '❌'} Sistema de reasoning")
            if reasoning_results.get("plan_created"):
                print(f"   📋 Plano criado com {reasoning_results.get('plan_tasks', 0)} tarefas")
            
            # Resultado geral
            total_zep_found = simple_zep_found + multiagent_zep_found + direct_zep_found
            total_queries = simple_total + multiagent_total + direct_total
            
            print(f"\\n🎯 RESULTADO GERAL:")
            print(f"   📊 {total_zep_found}/{total_queries} consultas encontraram informações sobre Zep")
            print(f"   📈 Taxa de sucesso: {(total_zep_found/total_queries)*100:.1f}%")
            
            if total_zep_found > 0:
                print("\\n🎉 SUCESSO! O sistema encontrou informações sobre Zep no PDF indexado!")
                
                # Mostrar melhor resultado
                all_results = simple_results + multiagent_results + direct_results
                best_result = max([r for r in all_results if r["has_zep_content"]], 
                                key=lambda x: x["result_length"], default=None)
                
                if best_result:
                    print("\\n📄 MELHOR RESULTADO ENCONTRADO:")
                    print(f"   🔍 Query: {best_result['query']}")
                    print(f"   📊 Tamanho: {best_result['result_length']} caracteres")
                    print(f"   📄 Conteúdo: {best_result['result'][:500]}...")
                
                return True
            else:
                print("\\n⚠️ ATENÇÃO! Nenhuma informação sobre Zep foi encontrada.")
                print("   Isso pode indicar:")
                print("   - PDF não foi indexado corretamente")
                print("   - PDF não contém informações sobre Zep")
                print("   - Sistema de busca precisa de ajustes")
                return False
                
        finally:
            self.stop_server()
            self.client.close()


def main():
    """Função principal"""
    try:
        tester = ZepMemoryTester()
        success = tester.run_zep_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()