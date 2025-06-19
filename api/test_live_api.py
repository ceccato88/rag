#!/usr/bin/env python3
"""
Teste ao vivo da API RAG Multi-Agente com servidor real
"""

import asyncio
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

# Configuração
API_HOST = "127.0.0.1"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"


class APITester:
    def __init__(self):
        self.server_process = None
        self.client = httpx.Client(timeout=30.0)
    
    def start_server(self):
        """Inicia o servidor da API"""
        print("🚀 Iniciando servidor da API...")
        
        # Comando para iniciar o servidor
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
            
            # Aguardar servidor inicializar
            print("⏳ Aguardando servidor inicializar...")
            time.sleep(15)  # Aguarda 15 segundos para inicialização completa
            
            # Verificar se o processo ainda está rodando
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
    
    def test_health_endpoint(self):
        """Testa o endpoint de health"""
        try:
            response = self.client.get(f"{API_BASE_URL}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check - Status: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ Health check falhou - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro no health check: {e}")
            return False
    
    def test_root_endpoint(self):
        """Testa o endpoint raiz"""
        try:
            response = self.client.get(f"{API_BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint raiz - Mensagem: {data.get('message', 'unknown')[:50]}...")
                return True
            else:
                print(f"❌ Endpoint raiz falhou - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro no endpoint raiz: {e}")
            return False
    
    def test_docs_endpoint(self):
        """Testa o endpoint de documentação"""
        try:
            response = self.client.get(f"{API_BASE_URL}/docs")
            if response.status_code == 200:
                print("✅ Endpoint de documentação acessível")
                return True
            else:
                print(f"❌ Endpoint de documentação falhou - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro no endpoint de documentação: {e}")
            return False
    
    def test_protected_endpoint(self):
        """Testa endpoint protegido sem autenticação"""
        try:
            response = self.client.post(
                f"{API_BASE_URL}/api/v1/research",
                json={"query": "test query"}
            )
            if response.status_code in [401, 503]:
                print(f"✅ Endpoint protegido funcionando - Status: {response.status_code}")
                return True
            else:
                print(f"❌ Endpoint protegido comportamento inesperado - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro no endpoint protegido: {e}")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🧪 Iniciando testes da API ao vivo")
        print("=" * 60)
        
        # Iniciar servidor
        if not self.start_server():
            return False
        
        try:
            tests = [
                ("Health Check", self.test_health_endpoint),
                ("Endpoint Raiz", self.test_root_endpoint),
                ("Documentação", self.test_docs_endpoint),
                ("Endpoint Protegido", self.test_protected_endpoint)
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in tests:
                print(f"\n🔍 Testando: {test_name}")
                try:
                    if test_func():
                        passed += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"❌ {test_name} - Exceção: {e}")
                    failed += 1
            
            print("\n" + "=" * 60)
            print(f"📊 Resultados finais: {passed} sucessos, {failed} falhas")
            
            if failed == 0:
                print("🎉 Todos os testes passaram!")
                return True
            else:
                print("⚠️  Alguns testes falharam!")
                return False
                
        finally:
            self.stop_server()
            self.client.close()


def main():
    """Função principal"""
    try:
        tester = APITester()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()