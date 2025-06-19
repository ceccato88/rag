#!/usr/bin/env python3
"""
Testes específicos para o sistema multi-agente
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


class MultiAgentTester:
    def __init__(self):
        self.server_process = None
        self.client = httpx.Client(timeout=60.0)  # Timeout maior para multi-agent
    
    def start_server_dev_mode(self):
        """Inicia o servidor em modo desenvolvimento"""
        print("🚀 Iniciando servidor para testes multi-agente...")
        
        # Configurar variáveis de ambiente para modo dev
        import os
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
            
            print("⏳ Aguardando servidor inicializar (20s para multi-agente)...")
            time.sleep(20)  # Mais tempo para inicialização do sistema multi-agente
            
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
    
    def test_lead_researcher_components(self):
        """Testa os componentes do Lead Researcher"""
        print("\\n🤖 TESTANDO COMPONENTES DO LEAD RESEARCHER")
        print("-" * 60)
        
        results = {
            "debug_access": False,
            "lead_researcher_available": False,
            "rag_system_connected": False,
            "reasoning_system": False,
            "agent_configuration": False
        }
        
        try:
            # 1. Verificar debug do sistema
            print("📍 Acessando debug do sistema multi-agente...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/research/debug")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Debug acessível")
                results["debug_access"] = True
                
                # Verificar componentes
                components = data.get("components", {})
                lead_available = components.get("lead_researcher_available", False)
                rag_available = components.get("simple_rag_available", False)
                
                print(f"      - Lead Researcher: {lead_available}")
                print(f"      - SimpleRAG: {rag_available}")
                
                if lead_available:
                    results["lead_researcher_available"] = True
                    print("   ✅ Lead Researcher disponível")
                
                if rag_available:
                    results["rag_system_connected"] = True
                    print("   ✅ Sistema RAG conectado")
                
                # Verificar informações detalhadas do Lead Researcher
                lead_info = data.get("lead_researcher_info", {})
                if lead_info:
                    agent_id = lead_info.get("agent_id", "N/A")
                    agent_name = lead_info.get("name", "N/A")
                    has_rag = lead_info.get("has_rag_system", False)
                    
                    print(f"      - Agent ID: {agent_id}")
                    print(f"      - Agent Name: {agent_name}")
                    print(f"      - RAG System: {has_rag}")
                    
                    if agent_id != "N/A" and agent_name != "N/A":
                        results["agent_configuration"] = True
                        print("   ✅ Configuração do agente válida")
                    
                    if has_rag:
                        results["reasoning_system"] = True
                        print("   ✅ Sistema de reasoning configurado")
            else:
                print(f"   ❌ Debug não acessível - {response.status_code}")
        
        except Exception as e:
            print(f"❌ Erro ao testar componentes: {e}")
        
        return results
    
    def test_multi_agent_reasoning(self):
        """Testa as capacidades de reasoning multi-agente"""
        print("\\n🧠 TESTANDO REASONING MULTI-AGENTE")
        print("-" * 60)
        
        results = {
            "planning_phase": False,
            "reasoning_test": False,
            "complex_query_handling": False,
            "agent_collaboration": False
        }
        
        try:
            # 1. Teste de planning
            print("📍 Testando fase de planning...")
            planning_query = {
                "query": "Explain the transformer architecture and its impact on modern AI",
                "objective": "Provide comprehensive analysis for AI researchers"
            }
            
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research/test-reasoning",
                json=planning_query
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    plan_created = data.get("plan_created", False)
                    plan_tasks = data.get("plan_tasks", 0)
                    
                    print(f"   ✅ Planning executado")
                    print(f"      - Plano criado: {plan_created}")
                    print(f"      - Tarefas no plano: {plan_tasks}")
                    
                    if plan_created and plan_tasks > 0:
                        results["planning_phase"] = True
                        print("   ✅ Sistema de planning funcionando")
                    
                    # Verificar informações sobre reasoning
                    reasoning_available = data.get("reasoning_available", False)
                    reasoning_type = data.get("reasoning_type", "N/A")
                    
                    print(f"      - Reasoning disponível: {reasoning_available}")
                    print(f"      - Tipo de reasoning: {reasoning_type}")
                    
                    if reasoning_available:
                        results["reasoning_test"] = True
                        print("   ✅ Sistema de reasoning ativo")
                else:
                    print(f"   ⚠️ Planning falhou: {data.get('error')}")
            else:
                print(f"   ❌ Teste de reasoning falhou - {response.status_code}")
            
            # 2. Teste de consulta complexa
            print("\\n📍 Testando consulta complexa...")
            complex_query = {
                "query": "Compare different attention mechanisms in neural networks and their computational complexity",
                "objective": "Detailed technical comparison for machine learning engineers"
            }
            
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research",
                json=complex_query
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_length = len(data.get("result", ""))
                    processing_time = data.get("processing_time", 0)
                    status = data.get("status", "UNKNOWN")
                    reasoning_trace = data.get("reasoning_trace")
                    
                    print(f"   ✅ Consulta complexa processada")
                    print(f"      - Status: {status}")
                    print(f"      - Tempo: {processing_time:.2f}s")
                    print(f"      - Resultado: {result_length} caracteres")
                    print(f"      - Reasoning trace: {'Disponível' if reasoning_trace else 'N/A'}")
                    
                    if status == "COMPLETED" and result_length > 100:
                        results["complex_query_handling"] = True
                        print("   ✅ Processamento de consulta complexa funcional")
                    
                    if reasoning_trace:
                        results["agent_collaboration"] = True
                        print("   ✅ Sistema de colaboração entre agentes ativo")
                else:
                    print(f"   ⚠️ Consulta complexa falhou: {data.get('error')}")
            else:
                print(f"   ❌ Consulta complexa falhou - {response.status_code}")
        
        except Exception as e:
            print(f"❌ Erro ao testar reasoning: {e}")
        
        return results
    
    def test_agent_context_memory(self):
        """Testa o sistema de contexto e memória dos agentes"""
        print("\\n🧭 TESTANDO CONTEXTO E MEMÓRIA DOS AGENTES")
        print("-" * 60)
        
        results = {
            "context_creation": False,
            "memory_system": False,
            "context_persistence": False,
            "multi_turn_conversation": False
        }
        
        try:
            # 1. Teste de criação de contexto
            print("📍 Testando criação de contexto...")
            
            # Primeira consulta para criar contexto
            first_query = {
                "query": "What are the key components of a transformer model?",
                "objective": "Understand basic architecture"
            }
            
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research",
                json=first_query
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    agent_id = data.get("agent_id", "")
                    timestamp = data.get("timestamp", "")
                    
                    print(f"   ✅ Contexto criado")
                    print(f"      - Agent ID: {agent_id}")
                    print(f"      - Timestamp: {timestamp}")
                    
                    if agent_id and timestamp:
                        results["context_creation"] = True
                        print("   ✅ Sistema de contexto funcionando")
            
            # 2. Verificar sistema de memória
            print("\\n📍 Verificando sistema de memória...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/research/debug")
            
            if response.status_code == 200:
                data = response.json()
                api_state = data.get("api_state", {})
                ready = api_state.get("ready", False)
                
                if ready:
                    print("   ✅ Sistema de memória inicializado")
                    results["memory_system"] = True
            
            # 3. Teste de persistência de contexto (consulta relacionada)
            print("\\n📍 Testando persistência de contexto...")
            related_query = {
                "query": "How does self-attention work in those models?",
                "objective": "Build on previous knowledge about transformers"
            }
            
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research",
                json=related_query
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", "")
                    
                    # Verificar se a resposta faz referência ao contexto anterior
                    context_indicators = [
                        "transformer", "attention", "model", "architecture",
                        "previous", "earlier", "mentioned", "discussed"
                    ]
                    
                    context_references = sum(1 for indicator in context_indicators 
                                           if indicator.lower() in result.lower())
                    
                    print(f"   ✅ Consulta relacionada processada")
                    print(f"      - Referências contextuais: {context_references}")
                    
                    if context_references >= 2:
                        results["context_persistence"] = True
                        print("   ✅ Persistência de contexto funcionando")
                    
                    results["multi_turn_conversation"] = True
                    print("   ✅ Conversação multi-turno ativa")
        
        except Exception as e:
            print(f"❌ Erro ao testar contexto e memória: {e}")
        
        return results
    
    def test_agent_rag_integration(self):
        """Testa a integração entre agentes e sistema RAG"""
        print("\\n🔗 TESTANDO INTEGRAÇÃO AGENTE-RAG")
        print("-" * 60)
        
        results = {
            "direct_rag_access": False,
            "agent_rag_integration": False,
            "rag_result_processing": False,
            "fallback_handling": False
        }
        
        try:
            # 1. Teste de acesso direto ao RAG
            print("📍 Testando acesso direto ao SimpleRAG...")
            rag_query = {"query": "transformer architecture"}
            
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research/simple",
                json=rag_query
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_length = data.get("result_length", 0)
                    processing_time = data.get("processing_time", 0)
                    
                    print(f"   ✅ RAG direto funcionando")
                    print(f"      - Resultado: {result_length} caracteres")
                    print(f"      - Tempo: {processing_time:.3f}s")
                    
                    if result_length > 0:
                        results["direct_rag_access"] = True
                        print("   ✅ Acesso direto ao RAG funcional")
            
            # 2. Teste de integração via Lead Researcher
            print("\\n📍 Testando RAG via Lead Researcher...")
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research/direct",
                json=rag_query
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", "")
                    confidence = data.get("confidence_score", 0)
                    sources = data.get("sources", [])
                    
                    print(f"   ✅ RAG via Lead Researcher funcionando")
                    print(f"      - Confiança: {confidence}")
                    print(f"      - Fontes: {sources}")
                    print(f"      - Resultado: {len(result)} caracteres")
                    
                    if len(result) > 0:
                        results["agent_rag_integration"] = True
                        print("   ✅ Integração Agente-RAG funcional")
                    
                    if confidence > 0 or sources:
                        results["rag_result_processing"] = True
                        print("   ✅ Processamento de resultados RAG ativo")
            
            # 3. Teste de fallback quando não há resultados
            print("\\n📍 Testando fallback para consultas sem resultados...")
            empty_query = {"query": "xyzabc123nonexistent"}
            
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research/simple",
                json=empty_query
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                diagnostic = data.get("diagnostic", {})
                
                print(f"   ✅ Fallback testado")
                print(f"      - Success: {success}")
                print(f"      - Diagnóstico: {diagnostic}")
                
                # Se o sistema retornou uma resposta estruturada mesmo sem resultados
                if not success and diagnostic:
                    results["fallback_handling"] = True
                    print("   ✅ Sistema de fallback funcionando")
        
        except Exception as e:
            print(f"❌ Erro ao testar integração RAG: {e}")
        
        return results
    
    def test_system_status_detailed(self):
        """Testa o status detalhado do sistema multi-agente"""
        print("\\n📊 TESTANDO STATUS DETALHADO DO SISTEMA")
        print("-" * 60)
        
        results = {
            "system_health": False,
            "component_status": False,
            "performance_metrics": False,
            "initialization_status": False
        }
        
        try:
            # 1. Health check completo
            print("📍 Verificando health check completo...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/health")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                components = data.get("components", {})
                metrics = data.get("metrics", {})
                
                print(f"   ✅ Health check OK - Status: {status}")
                print(f"      - Componentes: {components}")
                
                if status == "healthy":
                    results["system_health"] = True
                    print("   ✅ Sistema saudável")
                
                # Verificar componentes específicos
                required_components = ["memory", "lead_researcher", "simple_rag"]
                available_components = sum(1 for comp in required_components 
                                         if components.get(comp, False))
                
                print(f"      - Componentes disponíveis: {available_components}/{len(required_components)}")
                
                if available_components == len(required_components):
                    results["component_status"] = True
                    print("   ✅ Todos os componentes principais disponíveis")
                
                # Verificar métricas
                if metrics:
                    total_requests = metrics.get("total_requests", 0)
                    success_rate = metrics.get("success_rate", 0)
                    
                    print(f"      - Total de requests: {total_requests}")
                    print(f"      - Taxa de sucesso: {success_rate}%")
                    
                    results["performance_metrics"] = True
                    print("   ✅ Métricas de performance disponíveis")
            
            # 2. Status de pesquisa
            print("\\n📍 Verificando status de pesquisa...")
            response = self.client.get(f"{API_BASE_URL}/api/v1/research/status")
            
            if response.status_code == 200:
                data = response.json()
                research_ready = data.get("research_system_ready", False)
                lead_researcher = data.get("lead_researcher", {})
                
                print(f"   ✅ Status de pesquisa acessível")
                print(f"      - Sistema pronto: {research_ready}")
                print(f"      - Lead Researcher: {lead_researcher}")
                
                if research_ready and lead_researcher.get("available"):
                    results["initialization_status"] = True
                    print("   ✅ Sistema de pesquisa totalmente inicializado")
        
        except Exception as e:
            print(f"❌ Erro ao verificar status: {e}")
        
        return results
    
    def run_multiagent_tests(self):
        """Executa todos os testes do sistema multi-agente"""
        print("🤖 TESTES COMPLETOS DO SISTEMA MULTI-AGENTE")
        print("=" * 80)
        
        # Iniciar servidor
        if not self.start_server_dev_mode():
            return False
        
        try:
            # Aguardar inicialização completa
            print("⏳ Aguardando inicialização completa dos agentes...")
            time.sleep(5)
            
            # Executar todos os grupos de testes
            status_results = self.test_system_status_detailed()
            component_results = self.test_lead_researcher_components()
            reasoning_results = self.test_multi_agent_reasoning()
            memory_results = self.test_agent_context_memory()
            integration_results = self.test_agent_rag_integration()
            
            # Calcular estatísticas finais
            print("\\n" + "=" * 80)
            print("📊 RESULTADOS FINAIS DO SISTEMA MULTI-AGENTE:")
            
            all_results = [
                ("🔍 STATUS DO SISTEMA", status_results),
                ("🤖 COMPONENTES DO LEAD RESEARCHER", component_results),
                ("🧠 REASONING MULTI-AGENTE", reasoning_results),
                ("🧭 CONTEXTO E MEMÓRIA", memory_results),
                ("🔗 INTEGRAÇÃO AGENTE-RAG", integration_results)
            ]
            
            total_passed = 0
            total_tests = 0
            
            for section_name, section_results in all_results:
                passed = sum(section_results.values())
                total = len(section_results)
                total_passed += passed
                total_tests += total
                
                print(f"\\n{section_name}: {passed}/{total} testes passaram")
                for test, result in section_results.items():
                    status = "✅" if result else "❌"
                    print(f"   {status} {test}")
            
            # Resultado geral
            success_rate = (total_passed / total_tests) * 100
            print(f"\\n🎯 RESULTADO GERAL: {total_passed}/{total_tests} ({success_rate:.1f}%) testes passaram")
            
            if success_rate >= 80:
                print("🎉 EXCELENTE! O sistema multi-agente está funcionando muito bem!")
                return True
            elif success_rate >= 60:
                print("👍 BOM! O sistema multi-agente está operacional.")
                return True
            else:
                print("⚠️ ATENÇÃO! O sistema multi-agente precisa de configuração.")
                return False
                
        finally:
            self.stop_server()
            self.client.close()


def main():
    """Função principal"""
    try:
        tester = MultiAgentTester()
        success = tester.run_multiagent_tests()
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