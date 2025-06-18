#!/usr/bin/env python3
"""
Teste completo das APIs via Docker
"""
import time
import requests
import subprocess
import json
import os
from typing import Dict, List, Optional

class DockerAPITester:
    def __init__(self):
        self.simple_api_url = "http://localhost:8000"
        self.multiagent_api_url = "http://localhost:8001"
        self.test_results = []
        
        # Token de autenticação do .env
        self.bearer_token = "rag-prod-2024-secure-api-token-b8f9c3d7e2a1"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
    def run_command(self, command: str, cwd: str = None) -> Dict[str, any]:
        """Executa comando shell e retorna resultado"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=cwd,
                timeout=300
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def wait_for_api(self, url: str, timeout: int = 120) -> bool:
        """Aguarda API ficar disponível"""
        print(f"  ⏳ Aguardando API em {url}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Usar headers de autenticação para health check
                response = requests.get(f"{url}/health", headers=self.headers, timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ API disponível em {url}")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        print(f"  ❌ Timeout aguardando API em {url}")
        return False
    
    def test_api_endpoint(self, url: str, endpoint: str, data: Dict = None) -> Dict:
        """Testa endpoint específico da API"""
        try:
            if data:
                response = requests.post(f"{url}{endpoint}", json=data, headers=self.headers, timeout=30)
            else:
                response = requests.get(f"{url}{endpoint}", headers=self.headers, timeout=30)
            
            return {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "response_time": 0,
                "error": str(e)
            }
    
    def test_dockerfile_build(self, dockerfile: str, tag: str) -> bool:
        """Testa build individual do Dockerfile"""
        print(f"\n🔨 Testando build do {dockerfile}...")
        
        # Build da imagem
        build_cmd = f"docker build -f {dockerfile} -t {tag} ."
        result = self.run_command(build_cmd)
        
        if not result["success"]:
            print(f"  ❌ Falha no build: {result['stderr']}")
            return False
        
        print(f"  ✅ Build {tag} concluído com sucesso")
        return True
    
    def test_dockerfile_run(self, tag: str, port: str, api_url: str) -> bool:
        """Testa execução individual do container"""
        print(f"\n🚀 Testando execução do container {tag}...")
        
        # Parar container se estiver rodando
        self.run_command(f"docker stop {tag}-test 2>/dev/null")
        self.run_command(f"docker rm {tag}-test 2>/dev/null")
        
        # Executar container
        run_cmd = f"docker run -d --name {tag}-test -p {port}:8000 --env-file .env {tag}"
        result = self.run_command(run_cmd)
        
        if not result["success"]:
            print(f"  ❌ Falha na execução: {result['stderr']}")
            return False
        
        # Aguardar API ficar disponível
        if not self.wait_for_api(api_url):
            return False
        
        # Testar endpoints
        success = self.test_api_endpoints(api_url, f"{tag} (individual)")
        
        # Parar container
        self.run_command(f"docker stop {tag}-test")
        self.run_command(f"docker rm {tag}-test")
        
        return success
    
    def test_api_endpoints(self, base_url: str, context: str) -> bool:
        """Testa endpoints da API"""
        print(f"  🧪 Testando endpoints da API ({context})...")
        
        all_success = True
        
        # Teste 1: Health check
        result = self.test_api_endpoint(base_url, "/health")
        if result["success"]:
            print(f"    ✅ Health check OK ({result['response_time']:.2f}s)")
        else:
            print(f"    ❌ Health check falhou: {result.get('error', result.get('status_code'))}")
            all_success = False
        
        # Teste 2: Endpoint específico por API
        if "simple" in context.lower() or "8000" in base_url:
            # API Simple - endpoint /search
            search_data = {
                "query": "Como configurar Docker?",
                "max_results": 3
            }
            result = self.test_api_endpoint(base_url, "/search", search_data)
            if result["success"]:
                print(f"    ✅ Search endpoint OK ({result['response_time']:.2f}s)")
                # Verificar estrutura da resposta
                if "results" in result["data"]:
                    print(f"      📊 Retornou {len(result['data']['results'])} resultados")
                else:
                    print(f"      ⚠️ Resposta inesperada: {result['data']}")
            else:
                print(f"    ❌ Search endpoint falhou: {result.get('error', result.get('status_code'))}")
                all_success = False
        
        elif "multiagent" in context.lower() or "8001" in base_url:
            # API MultiAgent - endpoint /research
            research_data = {
                "query": "Explique arquitetura de microserviços",
                "research_depth": "standard",
                "enable_specialist": True
            }
            result = self.test_api_endpoint(base_url, "/research", research_data)
            if result["success"]:
                print(f"    ✅ Research endpoint OK ({result['response_time']:.2f}s)")
                # Verificar estrutura da resposta
                if "summary" in result["data"] or "research_result" in result["data"]:
                    print(f"      📊 Pesquisa multiagente executada com sucesso")
                else:
                    print(f"      ⚠️ Resposta inesperada: {result['data']}")
            else:
                print(f"    ❌ Research endpoint falhou: {result.get('error', result.get('status_code'))}")
                all_success = False
            
            # Teste adicional: analyze-complexity
            complexity_data = {
                "query": "Como implementar cache distribuído?"
            }
            result = self.test_api_endpoint(base_url, "/analyze-complexity", complexity_data)
            if result["success"]:
                print(f"    ✅ Complexity analysis OK ({result['response_time']:.2f}s)")
            else:
                print(f"    ❌ Complexity analysis falhou: {result.get('error', result.get('status_code'))}")
        
        return all_success
    
    def test_docker_compose(self) -> bool:
        """Testa docker-compose completo"""
        print(f"\n🐳 Testando Docker Compose...")
        
        # Parar serviços se estiverem rodando
        self.run_command("docker-compose down")
        
        # Build e start
        build_result = self.run_command("docker-compose build")
        if not build_result["success"]:
            print(f"  ❌ Falha no build compose: {build_result['stderr']}")
            return False
        
        print("  ✅ Build compose concluído")
        
        # Start serviços
        up_result = self.run_command("docker-compose up -d")
        if not up_result["success"]:
            print(f"  ❌ Falha no start compose: {up_result['stderr']}")
            return False
        
        print("  ✅ Serviços iniciados")
        
        # Aguardar APIs ficarem disponíveis
        simple_ready = self.wait_for_api(self.simple_api_url)
        multiagent_ready = self.wait_for_api(self.multiagent_api_url)
        
        success = True
        
        if simple_ready:
            success &= self.test_api_endpoints(self.simple_api_url, "Simple API - Compose")
        else:
            print("  ❌ API Simple não ficou disponível")
            success = False
        
        if multiagent_ready:
            success &= self.test_api_endpoints(self.multiagent_api_url, "MultiAgent API - Compose")
        else:
            print("  ❌ API MultiAgent não ficou disponível")
            success = False
        
        # Teste de integração entre APIs
        if simple_ready and multiagent_ready:
            print("  🔗 Testando integração entre APIs...")
            success &= self.test_api_integration()
        
        # Parar serviços
        self.run_command("docker-compose down")
        
        return success
    
    def test_api_integration(self) -> bool:
        """Testa integração entre as duas APIs"""
        try:
            # Comparar respostas da mesma query em ambas APIs
            query = "Explique arquitetura de microserviços"
            
            # Simple API usa /search
            simple_result = self.test_api_endpoint(
                self.simple_api_url, 
                "/search", 
                {"query": query, "max_results": 3}
            )
            
            # MultiAgent API usa /research
            multiagent_result = self.test_api_endpoint(
                self.multiagent_api_url, 
                "/research", 
                {
                    "query": query, 
                    "research_depth": "standard",
                    "enable_specialist": True
                }
            )
            
            if simple_result["success"] and multiagent_result["success"]:
                print("    ✅ Ambas APIs responderam corretamente")
                
                # Comparar tempos de resposta
                simple_time = simple_result["response_time"]
                multiagent_time = multiagent_result["response_time"]
                
                print(f"    📊 Simple API (/search): {simple_time:.2f}s")
                print(f"    📊 MultiAgent API (/research): {multiagent_time:.2f}s")
                
                if multiagent_time > simple_time:
                    print("    ✅ MultiAgent mais lenta como esperado (mais processamento)")
                
                return True
            else:
                print("    ❌ Uma ou ambas APIs falharam na integração")
                if not simple_result["success"]:
                    print(f"      Simple API: {simple_result.get('error', simple_result.get('status_code'))}")
                if not multiagent_result["success"]:
                    print(f"      MultiAgent API: {multiagent_result.get('error', multiagent_result.get('status_code'))}")
                return False
                
        except Exception as e:
            print(f"    ❌ Erro na integração: {e}")
            return False
    
    def run_full_test(self) -> Dict[str, bool]:
        """Executa bateria completa de testes"""
        print("🧪 TESTE COMPLETO DAS APIS VIA DOCKER")
        print("=" * 50)
        
        results = {}
        
        # Verificar pré-requisitos
        print("\n🔍 Verificando pré-requisitos...")
        
        # Docker disponível
        docker_check = self.run_command("docker --version")
        if docker_check["success"]:
            print("  ✅ Docker disponível")
        else:
            print("  ❌ Docker não encontrado")
            return {"error": "Docker não disponível"}
        
        # Docker Compose disponível
        compose_check = self.run_command("docker-compose --version")
        if compose_check["success"]:
            print("  ✅ Docker Compose disponível")
        else:
            print("  ❌ Docker Compose não encontrado")
            return {"error": "Docker Compose não disponível"}
        
        # Arquivo .env
        if os.path.exists(".env"):
            print("  ✅ Arquivo .env encontrado")
        else:
            print("  ❌ Arquivo .env não encontrado")
            return {"error": "Arquivo .env necessário"}
        
        # Teste 1: Build individual dos Dockerfiles
        print("\n" + "="*50)
        print("📦 TESTE 1: BUILD INDIVIDUAL DOS DOCKERFILES")
        print("="*50)
        
        results["simple_build"] = self.test_dockerfile_build("Dockerfile.api-simple", "rag-simple-api")
        results["multiagent_build"] = self.test_dockerfile_build("Dockerfile.api-multiagent", "rag-multiagent-api")
        
        # Teste 2: Execução individual dos containers
        if results["simple_build"]:
            print("\n" + "="*50)
            print("🚀 TESTE 2: EXECUÇÃO INDIVIDUAL - SIMPLE API")
            print("="*50)
            results["simple_run"] = self.test_dockerfile_run("rag-simple-api", "8000", self.simple_api_url)
        
        if results["multiagent_build"]:
            print("\n" + "="*50)
            print("🚀 TESTE 3: EXECUÇÃO INDIVIDUAL - MULTIAGENT API")
            print("="*50)
            results["multiagent_run"] = self.test_dockerfile_run("rag-multiagent-api", "8001", self.multiagent_api_url)
        
        # Teste 3: Docker Compose
        print("\n" + "="*50)
        print("🐳 TESTE 4: DOCKER COMPOSE COMPLETO")
        print("="*50)
        results["compose"] = self.test_docker_compose()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Imprime resumo dos resultados"""
        print("\n" + "="*50)
        print("📊 RESUMO DOS TESTES")
        print("="*50)
        
        total_tests = len([k for k in results.keys() if k != "error"])
        passed_tests = sum(1 for v in results.values() if v == True)
        
        print(f"\n📈 Resultados Gerais:")
        print(f"  ✅ Testes passaram: {passed_tests}/{total_tests}")
        print(f"  📊 Taxa de sucesso: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n📋 Detalhes por teste:")
        
        test_names = {
            "simple_build": "🔨 Build Simple API",
            "multiagent_build": "🔨 Build MultiAgent API", 
            "simple_run": "🚀 Execução Simple API",
            "multiagent_run": "🚀 Execução MultiAgent API",
            "compose": "🐳 Docker Compose"
        }
        
        for key, name in test_names.items():
            if key in results:
                status = "✅ PASSOU" if results[key] else "❌ FALHOU"
                print(f"  {name}: {status}")
        
        if "error" in results:
            print(f"\n❌ Erro geral: {results['error']}")
        
        # Recomendações
        print(f"\n💡 Recomendações:")
        if all(results.get(k, False) for k in ["simple_build", "multiagent_build", "compose"]):
            print("  🎉 Todos os testes passaram! APIs prontas para produção.")
        else:
            print("  🔧 Verificar falhas nos testes e corrigir antes do deploy.")
            if not results.get("simple_build", True):
                print("    - Verificar Dockerfile.api-simple")
            if not results.get("multiagent_build", True):
                print("    - Verificar Dockerfile.api-multiagent")
            if not results.get("compose", True):
                print("    - Verificar docker-compose.yml")

def main():
    tester = DockerAPITester()
    results = tester.run_full_test()
    tester.print_summary(results)
    
    # Retornar código de saída apropriado
    if "error" in results:
        exit(1)
    
    success_rate = sum(1 for v in results.values() if v == True) / len(results)
    exit(0 if success_rate >= 0.8 else 1)

if __name__ == "__main__":
    main()
