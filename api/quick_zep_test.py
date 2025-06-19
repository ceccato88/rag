#!/usr/bin/env python3
"""
Teste rápido sobre Zep usando a API
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
    print("🚀 Iniciando servidor...")
    
    env = os.environ.copy()
    env["PRODUCTION_MODE"] = "false"
    env["API_BEARER_TOKEN"] = ""
    
    cmd = [sys.executable, "-m", "uvicorn", "api.main:app", 
           "--host", API_HOST, "--port", str(API_PORT)]
    
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(15)  # Aguarda inicialização
    
    if process.poll() is None:
        print("✅ Servidor rodando")
        return process
    else:
        print("❌ Falha ao iniciar servidor")
        return None


def test_zep_search():
    """Testa busca sobre Zep"""
    client = httpx.Client(timeout=30.0)
    
    queries = [
        "What is Zep?",
        "Zep memory layer",
        "Zep features"
    ]
    
    print("\\n🔍 TESTANDO BUSCA SOBRE ZEP:")
    print("-" * 40)
    
    for i, query in enumerate(queries, 1):
        print(f"\\n{i}. Query: {query}")
        
        try:
            # Teste SimpleRAG
            response = client.post(f"{API_BASE_URL}/api/v1/research/simple", 
                                 json={"query": query})
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", "")
                success = data.get("success", False)
                
                print(f"   SimpleRAG: {'✅' if success else '❌'}")
                if result and "zep" in result.lower():
                    print(f"   🎯 Encontrou Zep! ({len(result)} chars)")
                    print(f"   📄 Preview: {result[:150]}...")
                elif result:
                    print(f"   📄 Resultado: {result[:100]}...")
                else:
                    print("   ⚠️ Sem resultado")
            else:
                print(f"   ❌ SimpleRAG erro: {response.status_code}")
            
            # Teste Multi-Agent (mais rápido)
            response = client.post(f"{API_BASE_URL}/api/v1/research/direct", 
                                 json={"query": query})
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", "")
                success = data.get("success", False)
                
                print(f"   Direct RAG: {'✅' if success else '❌'}")
                if result and "zep" in result.lower():
                    print(f"   🎯 Encontrou Zep! ({len(result)} chars)")
                elif result:
                    print(f"   📄 Resultado: {len(result)} chars")
        
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    client.close()


def main():
    server = start_server()
    if not server:
        return 1
    
    try:
        print("⏳ Aguardando sistema inicializar...")
        time.sleep(5)
        
        test_zep_search()
        
        print("\\n✅ Teste concluído!")
        return 0
    
    finally:
        if server:
            print("🛑 Parando servidor...")
            server.terminate()
            server.wait()


if __name__ == "__main__":
    sys.exit(main())