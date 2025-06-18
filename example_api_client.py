#!/usr/bin/env python3
"""
🔧 EXEMPLO DE CLIENTE PARA AS APIs
Demonstra como usar as APIs RAG Simples e Multi-Agente
"""

import requests
import json
import time
import websocket
import threading
from datetime import datetime
from typing import Dict, Any, Optional

class RAGAPIClient:
    """Cliente para interagir com as APIs RAG"""
    
    def __init__(self, simple_api_url: str = "http://localhost:8000", 
                 multiagent_api_url: str = "http://localhost:8001"):
        self.simple_api_url = simple_api_url
        self.multiagent_api_url = multiagent_api_url
        
    def test_connection(self) -> Dict[str, bool]:
        """Testa conexão com ambas as APIs"""
        results = {}
        
        # Testar API Simples
        try:
            response = requests.get(f"{self.simple_api_url}/health", timeout=5)
            results["simple_api"] = response.status_code == 200
        except:
            results["simple_api"] = False
            
        # Testar API Multi-Agente
        try:
            response = requests.get(f"{self.multiagent_api_url}/health", timeout=5)
            results["multiagent_api"] = response.status_code == 200
        except:
            results["multiagent_api"] = False
            
        return results
    
    def simple_search(self, query: str, max_results: int = 5, 
                     similarity_threshold: float = 0.7) -> Optional[Dict[str, Any]]:
        """Realiza busca usando a API RAG Simples"""
        
        url = f"{self.simple_api_url}/search"
        payload = {
            "query": query,
            "max_results": max_results,
            "similarity_threshold": similarity_threshold,
            "include_metadata": True
        }
        
        try:
            print(f"🔍 Consultando API RAG Simples...")
            start_time = time.time()
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                processing_time = time.time() - start_time
                
                print(f"✅ Resposta recebida em {processing_time:.2f}s")
                return result
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def multiagent_research_sync(self, query: str, objective: Optional[str] = None,
                                max_agents: int = 3, include_reasoning: bool = True) -> Optional[Dict[str, Any]]:
        """Realiza pesquisa síncrona usando a API Multi-Agente"""
        
        url = f"{self.multiagent_api_url}/research"
        payload = {
            "query": query,
            "objective": objective or f"Pesquisar sobre: {query}",
            "processing_mode": "sync",
            "max_agents": max_agents,
            "include_reasoning": include_reasoning,
            "timeout_seconds": 300
        }
        
        try:
            print(f"🤖 Consultando API Multi-Agente (síncrono)...")
            start_time = time.time()
            
            response = requests.post(url, json=payload, timeout=330)  # Timeout um pouco maior
            
            if response.status_code == 200:
                result = response.json()
                processing_time = time.time() - start_time
                
                print(f"✅ Resposta recebida em {processing_time:.2f}s")
                return result
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def multiagent_research_async(self, query: str, objective: Optional[str] = None) -> Optional[str]:
        """Inicia pesquisa assíncrona usando a API Multi-Agente"""
        
        url = f"{self.multiagent_api_url}/research"
        payload = {
            "query": query,
            "objective": objective or f"Pesquisar sobre: {query}",
            "processing_mode": "async",
            "timeout_seconds": 300
        }
        
        try:
            print(f"🚀 Iniciando pesquisa assíncrona...")
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("job_id")
                print(f"✅ Job iniciado: {job_id}")
                return job_id
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def check_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Verifica status de job assíncrono"""
        
        url = f"{self.multiagent_api_url}/research/{job_id}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def wait_for_job_completion(self, job_id: str, max_wait_time: int = 300) -> Optional[Dict[str, Any]]:
        """Aguarda conclusão de job assíncrono"""
        
        print(f"⏳ Aguardando conclusão do job {job_id}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.check_job_status(job_id)
            
            if not status:
                print("❌ Erro ao verificar status do job")
                return None
            
            job_status = status.get("status", "unknown")
            progress = status.get("progress", 0.0)
            
            print(f"📊 Status: {job_status} - {progress:.1%}")
            
            if job_status == "completed":
                print("✅ Job concluído!")
                return status.get("result")
            elif job_status == "failed":
                error = status.get("error", "Unknown error")
                print(f"❌ Job falhou: {error}")
                return None
            
            time.sleep(5)  # Aguardar 5 segundos
        
        print(f"⏰ Timeout após {max_wait_time}s")
        return None
    
    def analyze_complexity(self, query: str) -> Optional[Dict[str, Any]]:
        """Analisa complexidade de uma query"""
        
        url = f"{self.multiagent_api_url}/analyze-complexity"
        payload = {"query": query}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None

def print_simple_result(result: Dict[str, Any]):
    """Exibe resultado da API RAG Simples"""
    print("\n" + "="*60)
    print("📊 RESULTADO - API RAG SIMPLES")
    print("="*60)
    
    print(f"🔍 Query: {result['query']}")
    print(f"⏱️  Tempo: {result['processing_time']:.2f}s")
    print(f"📄 Resultados: {result['results_count']}")
    print(f"🎯 Sucesso: {'✅' if result['success'] else '❌'}")
    
    print(f"\n💬 RESPOSTA:")
    print("-" * 40)
    print(result['response'])
    
    if result.get('sources'):
        print(f"\n📚 FONTES ({len(result['sources'])}):")
        print("-" * 40)
        for i, source in enumerate(result['sources'][:3], 1):
            print(f"{i}. Página {source['page_num']} - Similaridade: {source['similarity_score']:.2f}")
            print(f"   {source['excerpt'][:150]}...")

def print_multiagent_result(result: Dict[str, Any]):
    """Exibe resultado da API Multi-Agente"""
    print("\n" + "="*60)
    print("🤖 RESULTADO - API MULTI-AGENTE")
    print("="*60)
    
    print(f"🔍 Query: {result['query']}")
    print(f"🎯 Objetivo: {result['objective']}")
    print(f"⏱️  Tempo: {result['processing_time']:.2f}s")
    print(f"🎲 Confiança: {result['confidence_score']:.2f}")
    print(f"🧠 Complexidade: {result['complexity_detected']}")
    print(f"🤖 Agentes: {len(result['agents_used'])}")
    
    print(f"\n💬 RESPOSTA FINAL:")
    print("-" * 40)
    print(result['final_answer'])
    
    if result.get('agents_used'):
        print(f"\n🤖 AGENTES UTILIZADOS:")
        print("-" * 40)
        for agent in result['agents_used']:
            status_icon = "✅" if agent['status'] == 'completed' else "❌"
            print(f"{status_icon} {agent['agent_type']} - {agent.get('execution_time', 0):.1f}s")
    
    if result.get('reasoning_trace'):
        print(f"\n🧠 PROCESSO DE REASONING:")
        print("-" * 40)
        for i, step in enumerate(result['reasoning_trace'][:5], 1):
            print(f"{i}. {step}")

def main():
    """Função principal com exemplos de uso"""
    
    print("🚀 EXEMPLO DE USO DAS APIs RAG")
    print("="*60)
    
    # Inicializar cliente
    client = RAGAPIClient()
    
    # Testar conexão
    print("\n🔌 TESTANDO CONEXÃO COM AS APIs...")
    connections = client.test_connection()
    
    for api, status in connections.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {api.replace('_', ' ').title()}: {'Conectado' if status else 'Desconectado'}")
    
    if not any(connections.values()):
        print("\n❌ NENHUMA API ESTÁ DISPONÍVEL")
        print("💡 Inicie as APIs antes de executar este exemplo:")
        print("   • python api_simple.py")
        print("   • python api_multiagent.py")
        return
    
    # Exemplos de consultas
    queries = [
        {
            "query": "O que é machine learning?",
            "type": "simple",
            "description": "Consulta simples sobre conceitos básicos"
        },
        {
            "query": "Compare as vantagens e desvantagens do TensorFlow versus PyTorch para deep learning",
            "type": "complex",
            "description": "Análise comparativa que requer reasoning multi-agente"
        },
        {
            "query": "Explique redes neurais convolucionais e suas aplicações práticas",
            "type": "both",
            "description": "Consulta que pode ser testada em ambas as APIs"
        }
    ]
    
    for i, example in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"📝 EXEMPLO {i}: {example['description']}")
        print(f"🔍 Query: {example['query']}")
        print("="*60)
        
        if example["type"] in ["simple", "both"] and connections["simple_api"]:
            # Testar API RAG Simples
            print(f"\n🔍 TESTANDO API RAG SIMPLES...")
            result = client.simple_search(example["query"])
            if result:
                print_simple_result(result)
            
            time.sleep(2)  # Pausa entre requests
        
        if example["type"] in ["complex", "both"] and connections["multiagent_api"]:
            # Analisar complexidade primeiro
            print(f"\n🧠 ANALISANDO COMPLEXIDADE...")
            complexity = client.analyze_complexity(example["query"])
            if complexity:
                print(f"📊 Complexidade detectada: {complexity['detected_complexity']}")
                print(f"💭 Reasoning: {complexity['reasoning']}")
                print(f"⏱️  Tempo estimado: {complexity['estimated_time']}s")
            
            # Testar API Multi-Agente (síncrono)
            print(f"\n🤖 TESTANDO API MULTI-AGENTE (SÍNCRONO)...")
            result = client.multiagent_research_sync(
                example["query"],
                f"Fornecer análise detalhada sobre: {example['query']}"
            )
            if result:
                print_multiagent_result(result)
        
        if i < len(queries):
            print(f"\n⏳ Aguardando próximo exemplo...")
            time.sleep(3)
    
    print(f"\n🎉 EXEMPLOS CONCLUÍDOS!")
    print("="*60)
    print("💡 PRÓXIMOS PASSOS:")
    print("   • Experimente suas próprias consultas")
    print("   • Acesse a documentação: /docs")
    print("   • Monitore métricas: /metrics")

if __name__ == "__main__":
    main()