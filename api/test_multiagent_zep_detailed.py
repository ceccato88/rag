#!/usr/bin/env python3
"""
Teste detalhado do sistema multi-agente com consulta complexa sobre Zep
"""

import os
import subprocess
import sys
import time

import httpx

# Configuração
API_HOST = "127.0.0.1"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"


def start_server():
    """Inicia servidor em modo dev"""
    print("🚀 Iniciando servidor para teste multi-agente detalhado...")
    
    env = os.environ.copy()
    env["PRODUCTION_MODE"] = "false"
    env["API_BEARER_TOKEN"] = ""
    
    cmd = [sys.executable, "-m", "uvicorn", "api.main:app", 
           "--host", API_HOST, "--port", str(API_PORT)]
    
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(20)  # Mais tempo para multi-agente
    
    if process.poll() is None:
        print("✅ Servidor multi-agente rodando")
        return process
    else:
        print("❌ Falha ao iniciar servidor")
        return None


def test_multiagent_zep_analysis():
    """Testa análise completa do Zep com sistema multi-agente"""
    client = httpx.Client(timeout=60.0)
    
    print("\\n🤖 TESTE MULTI-AGENTE - ANÁLISE COMPLETA DO ZEP")
    print("=" * 70)
    
    # Consulta complexa que deve ativar múltiplos subagentes
    complex_query = {
        "query": "Provide a comprehensive analysis of Zep memory layer: architecture, features, benefits, and how it compares to MemGPT",
        "objective": "Detailed technical evaluation of Zep for AI system architects and developers"
    }
    
    print(f"🔍 Query: {complex_query['query']}")
    print(f"🎯 Objective: {complex_query['objective']}")
    print("\\n⏳ Executando análise multi-agente...")
    
    start_time = time.time()
    
    try:
        # Teste principal multi-agente
        response = client.post(f"{API_BASE_URL}/api/v1/research", json=complex_query)
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Extrair informações detalhadas
            success = data.get("success", False)
            result = data.get("result", "")
            agent_id = data.get("agent_id", "")
            status = data.get("status", "")
            api_processing_time = data.get("processing_time", 0)
            confidence_score = data.get("confidence_score")
            sources = data.get("sources", [])
            reasoning_trace = data.get("reasoning_trace")
            error = data.get("error")
            
            print("\\n📊 RESULTADOS DO SISTEMA MULTI-AGENTE:")
            print("-" * 50)
            print(f"✅ Success: {success}")
            print(f"🤖 Agent ID: {agent_id}")
            print(f"📊 Status: {status}")
            print(f"⏱️ Tempo total: {processing_time:.2f}s")
            print(f"⏱️ Tempo API: {api_processing_time:.2f}s")
            print(f"🎯 Confidence: {confidence_score}")
            print(f"📚 Sources: {sources}")
            print(f"🧠 Reasoning trace: {'Disponível' if reasoning_trace else 'N/A'}")
            
            if error:
                print(f"❌ Error: {error}")
            
            # Analisar o resultado
            if result:
                result_length = len(result)
                has_zep = "zep" in result.lower()
                has_memgpt = "memgpt" in result.lower()
                has_architecture = any(word in result.lower() for word in ["architecture", "arquitetura"])
                has_features = any(word in result.lower() for word in ["features", "funcionalidades", "características"])
                has_comparison = any(word in result.lower() for word in ["compare", "comparison", "vs", "versus", "comparação"])
                
                print(f"\\n📄 ANÁLISE DO RESULTADO:")
                print("-" * 30)
                print(f"📏 Tamanho: {result_length} caracteres")
                print(f"🎯 Menciona Zep: {'✅' if has_zep else '❌'}")
                print(f"🔍 Menciona MemGPT: {'✅' if has_memgpt else '❌'}")
                print(f"🏗️ Discute arquitetura: {'✅' if has_architecture else '❌'}")
                print(f"⭐ Discute features: {'✅' if has_features else '❌'}")
                print(f"⚖️ Faz comparação: {'✅' if has_comparison else '❌'}")
                
                # Mostrar preview do resultado
                print(f"\\n📖 PREVIEW DO RESULTADO:")
                print("-" * 30)
                
                # Dividir em parágrafos para melhor visualização
                paragraphs = result.split('\\n')
                preview_chars = 0
                for para in paragraphs:
                    if preview_chars + len(para) > 800:  # Limitar preview
                        print("...")
                        break
                    print(para)
                    preview_chars += len(para)
                
                # Avaliar qualidade da resposta
                quality_score = 0
                if has_zep: quality_score += 2
                if has_memgpt: quality_score += 2  
                if has_architecture: quality_score += 1
                if has_features: quality_score += 1
                if has_comparison: quality_score += 2
                if result_length > 500: quality_score += 1
                if result_length > 1000: quality_score += 1
                
                print(f"\\n🏆 PONTUAÇÃO DE QUALIDADE: {quality_score}/10")
                
                if quality_score >= 8:
                    print("🎉 EXCELENTE! Resposta muito completa e detalhada!")
                elif quality_score >= 6:
                    print("👍 BOA! Resposta adequada com informações relevantes.")
                elif quality_score >= 4:
                    print("👌 SATISFATÓRIA! Resposta básica mas útil.")
                else:
                    print("⚠️ LIMITADA! Resposta precisa de mais detalhes.")
                
                return {
                    "success": success,
                    "quality_score": quality_score,
                    "has_zep_content": has_zep,
                    "result_length": result_length,
                    "processing_time": processing_time,
                    "agent_worked": status == "COMPLETED"
                }
            else:
                print("\\n❌ NENHUM RESULTADO RETORNADO")
                return {
                    "success": False,
                    "quality_score": 0,
                    "has_zep_content": False,
                    "result_length": 0,
                    "processing_time": processing_time,
                    "agent_worked": False
                }
        else:
            print(f"\\n❌ ERRO HTTP: {response.status_code}")
            if response.text:
                print(f"Detalhes: {response.text[:200]}")
            return {
                "success": False,
                "quality_score": 0,
                "has_zep_content": False,
                "result_length": 0,
                "processing_time": processing_time,
                "agent_worked": False
            }
    
    except Exception as e:
        print(f"\\n❌ EXCEÇÃO: {e}")
        return {
            "success": False,
            "quality_score": 0,
            "has_zep_content": False,
            "result_length": 0,
            "processing_time": time.time() - start_time,
            "agent_worked": False
        }
    
    finally:
        client.close()


def test_reasoning_system():
    """Testa o sistema de reasoning"""
    client = httpx.Client(timeout=30.0)
    
    print("\\n🧠 TESTE DO SISTEMA DE REASONING")
    print("=" * 50)
    
    reasoning_query = {
        "query": "Analyze Zep memory layer and create a structured plan to understand its capabilities",
        "objective": "Test reasoning and planning capabilities"
    }
    
    print(f"🔍 Query: {reasoning_query['query']}")
    
    try:
        response = client.post(f"{API_BASE_URL}/api/v1/research/test-reasoning", 
                             json=reasoning_query)
        
        if response.status_code == 200:
            data = response.json()
            
            success = data.get("success", False)
            plan_created = data.get("plan_created", False)
            plan_tasks = data.get("plan_tasks", 0)
            plan_details = data.get("plan_details", [])
            reasoning_available = data.get("reasoning_available", False)
            reasoning_type = data.get("reasoning_type", "")
            
            print(f"\\n📊 RESULTADOS DO REASONING:")
            print("-" * 30)
            print(f"✅ Success: {success}")
            print(f"📋 Plan created: {plan_created}")
            print(f"📝 Plan tasks: {plan_tasks}")
            print(f"🧠 Reasoning available: {reasoning_available}")
            print(f"🔧 Reasoning type: {reasoning_type}")
            
            if plan_details:
                print(f"\\n📋 DETALHES DO PLANO:")
                for i, task in enumerate(plan_details, 1):
                    print(f"   {i}. {task}")
            
            return {
                "reasoning_works": success and reasoning_available,
                "planning_works": plan_created and plan_tasks > 0,
                "reasoning_type": reasoning_type
            }
        else:
            print(f"❌ Erro: {response.status_code}")
            return {"reasoning_works": False, "planning_works": False, "reasoning_type": ""}
    
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return {"reasoning_works": False, "planning_works": False, "reasoning_type": ""}
    
    finally:
        client.close()


def main():
    server = start_server()
    if not server:
        return 1
    
    try:
        print("⏳ Aguardando sistema multi-agente inicializar...")
        time.sleep(5)
        
        # Testar reasoning primeiro
        reasoning_results = test_reasoning_system()
        
        # Testar análise multi-agente
        analysis_results = test_multiagent_zep_analysis()
        
        # Resultado final
        print("\\n" + "=" * 70)
        print("🎯 RESUMO FINAL DOS TESTES MULTI-AGENTE:")
        print("-" * 70)
        
        print(f"🧠 Sistema de Reasoning: {'✅' if reasoning_results['reasoning_works'] else '❌'}")
        print(f"📋 Sistema de Planning: {'✅' if reasoning_results['planning_works'] else '❌'}")
        print(f"🔧 Tipo de Reasoning: {reasoning_results['reasoning_type']}")
        
        print(f"\\n🤖 Multi-Agent Analysis: {'✅' if analysis_results['success'] else '❌'}")
        print(f"🎯 Encontrou conteúdo Zep: {'✅' if analysis_results['has_zep_content'] else '❌'}")
        print(f"🏆 Qualidade da resposta: {analysis_results['quality_score']}/10")
        print(f"⏱️ Tempo de processamento: {analysis_results['processing_time']:.2f}s")
        print(f"📏 Tamanho da resposta: {analysis_results['result_length']} caracteres")
        
        # Avaliação geral
        overall_success = (
            reasoning_results['reasoning_works'] and
            reasoning_results['planning_works'] and
            analysis_results['success'] and
            analysis_results['has_zep_content'] and
            analysis_results['quality_score'] >= 5
        )
        
        print(f"\\n🎉 RESULTADO GERAL: {'✅ SISTEMA MULTI-AGENTE FUNCIONANDO PERFEITAMENTE!' if overall_success else '⚠️ SISTEMA PARCIALMENTE FUNCIONAL'}")
        
        return 0 if overall_success else 1
    
    finally:
        if server:
            print("\\n🛑 Parando servidor...")
            server.terminate()
            server.wait()


if __name__ == "__main__":
    sys.exit(main())