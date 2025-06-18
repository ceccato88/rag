# 🔧 Troubleshooting e Resolução de Problemas

## 🚨 Problemas Comuns e Soluções

### 1. **Problemas de Instalação**

#### ❌ Erro: "ModuleNotFoundError: No module named 'chromadb'"

**Causa**: Dependências não instaladas corretamente

**Solução**:
```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Reinstalar dependências
pip install -r requirements.txt

# Verificar instalação
python -c "import chromadb; print('ChromaDB OK')"
```

#### ❌ Erro: "Failed to connect to OpenAI API"

**Causa**: API key não configurada ou inválida

**Solução**:
```bash
# Verificar variável de ambiente
echo $OPENAI_API_KEY

# Configurar se necessário
export OPENAI_API_KEY="sk-your-key-here"

# Ou criar arquivo .env
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

**Teste**:
```python
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
print("API Key configurada:", openai.api_key is not None)
```

#### ❌ Erro: "Permission denied" ao executar scripts

**Causa**: Permissões de arquivo

**Solução**:
```bash
# Dar permissão de execução
chmod +x test_all_endpoints.sh
chmod +x install.py

# Verificar permissões
ls -la *.sh *.py
```

### 2. **Problemas com ChromaDB**

#### ❌ Erro: "Collection already exists"

**Causa**: Tentativa de criar collection existente

**Solução**:
```python
# Verificar collections existentes
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
print("Collections:", client.list_collections())

# Deletar collection se necessário
try:
    client.delete_collection("documents")
    print("Collection deletada")
except:
    print("Collection não existia")
```

#### ❌ Erro: "Database locked"

**Causa**: Múltiplas instâncias acessando o banco

**Solução**:
```bash
# Parar todos os processos
pkill -f "uvicorn"
pkill -f "python"

# Verificar locks
lsof ./chroma_db/

# Remover locks se necessário
rm -f ./chroma_db/*.lock

# Reiniciar API
uvicorn api_simple:app --reload
```

#### ❌ Erro: "No documents found in collection"

**Causa**: Base de conhecimento vazia

**Solução**:
```bash
# Verificar documentos
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('documents')
print('Documentos:', collection.count())
"

# Reindexar se necessário
python indexer.py --directory ./docs --collection documents
```

### 3. **Problemas de Performance**

#### 🐌 API muito lenta

**Diagnóstico**:
```python
import time
import requests

def test_latency():
    start = time.time()
    response = requests.post("http://localhost:8000/search", json={
        "query": "teste de performance",
        "max_results": 5
    })
    latency = time.time() - start
    print(f"Latência: {latency:.2f}s")
    return latency

# Testar múltiplas vezes
latencies = [test_latency() for _ in range(5)]
print(f"Latência média: {sum(latencies)/len(latencies):.2f}s")
```

**Soluções**:

1. **Otimizar cache**:
```python
# Em config.py
CACHE_SIZE = 1000
CACHE_TTL = 3600  # 1 hora
ENABLE_QUERY_CACHE = True
```

2. **Reduzir tamanho dos chunks**:
```python
# Em constants.py
CHUNK_SIZE = 500  # Menor = mais rápido
CHUNK_OVERLAP = 50
```

3. **Limitar resultados**:
```python
# Em requests
{
    "query": "sua pergunta",
    "max_results": 3  # Menos resultados = mais rápido
}
```

#### 🔥 Alto uso de memória

**Diagnóstico**:
```bash
# Monitorar uso de memória
top -p $(pgrep -f "uvicorn")

# Ou usar htop
htop -p $(pgrep -f "uvicorn")
```

**Soluções**:

1. **Configurar limites**:
```python
# Em config.py
MAX_MEMORY_USAGE = 2048  # MB
MAX_CONCURRENT_REQUESTS = 10
GARBAGE_COLLECTION_INTERVAL = 60
```

2. **Otimizar embeddings**:
```python
# Usar modelo menor
EMBEDDING_MODEL = "text-embedding-ada-002"  # Mais eficiente
```

### 4. **Problemas de API**

#### ❌ Erro 422: Validation Error

**Causa**: Parâmetros inválidos na requisição

**Exemplo de erro**:
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solução**:
```bash
# Formato correto
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sua pergunta aqui",
    "max_results": 5
  }'
```

#### ❌ Erro 500: Internal Server Error

**Diagnóstico**:
```bash
# Verificar logs
tail -f api_simple.log

# Ou logs do Docker
docker-compose logs -f api
```

**Soluções comuns**:

1. **Verificar OpenAI API**:
```python
# Testar conexão
python test_api_config.py
```

2. **Verificar ChromaDB**:
```python
# Testar banco
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
print('ChromaDB OK')
"
```

#### ❌ Erro 429: Rate Limit Exceeded

**Causa**: Muitas requisições para OpenAI

**Solução**:
```python
# Em config.py - adicionar rate limiting
OPENAI_RATE_LIMIT = 60  # requests per minute
RATE_LIMIT_DELAY = 1    # seconds between requests

# Implementar backoff exponencial
import time
import random

def exponential_backoff(attempt):
    delay = (2 ** attempt) + random.uniform(0, 1)
    time.sleep(delay)
```

### 5. **Problemas Multi-Agente**

#### ❌ Agentes não respondem

**Diagnóstico**:
```python
# Testar agentes individualmente
import sys
sys.path.append('./multi-agent-researcher/src')

from researcher.agents.basic_lead_researcher import BasicLeadResearcher

# Teste simples
agent = BasicLeadResearcher()
result = agent.research("teste simples")
print(result)
```

**Soluções**:

1. **Verificar configuração**:
```python
# Verificar se todos os componentes estão inicializados
def check_agent_config():
    try:
        from researcher.memory.enhanced_memory import EnhancedMemory
        from researcher.reasoning.enhanced_react_reasoning import EnhancedReActReasoning
        print("✅ Componentes OK")
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")

check_agent_config()
```

2. **Reinicializar sistema**:
```bash
# Parar tudo
pkill -f "python"

# Limpar cache Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Reiniciar
python api_multiagent.py
```

#### ❌ Timeout em pesquisas longas

**Causa**: Pesquisa muito complexa ou muitos agentes

**Solução**:
```python
# Em config.py
AGENT_TIMEOUT = 300        # 5 minutos
MAX_AGENT_ITERATIONS = 5   # Limitar iterações
RESEARCH_DEPTH_LIMIT = 3   # Profundidade máxima
```

## 📊 Ferramentas de Diagnóstico

### 1. **Script de Diagnóstico Completo**

```python
#!/usr/bin/env python3
"""
Script de diagnóstico completo do sistema RAG
"""
import os
import sys
import importlib
import requests
import chromadb
from pathlib import Path

def check_environment():
    """Verifica ambiente Python"""
    print("🐍 Verificando ambiente Python...")
    print(f"  Python version: {sys.version}")
    print(f"  Working directory: {os.getcwd()}")
    print(f"  Virtual env: {os.getenv('VIRTUAL_ENV', 'Não ativado')}")

def check_dependencies():
    """Verifica dependências"""
    print("\n📦 Verificando dependências...")
    
    required_packages = [
        'chromadb', 'fastapi', 'uvicorn', 'openai', 
        'langchain', 'python-multipart', 'pydantic'
    ]
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - FALTANDO")

def check_config():
    """Verifica configuração"""
    print("\n⚙️ Verificando configuração...")
    
    # API Key
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"  ✅ OPENAI_API_KEY configurada (***{api_key[-4:]})")
    else:
        print("  ❌ OPENAI_API_KEY não encontrada")
    
    # Arquivos de configuração
    config_files = ['config.py', 'constants.py']
    for file in config_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - FALTANDO")

def check_chromadb():
    """Verifica ChromaDB"""
    print("\n💾 Verificando ChromaDB...")
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        print(f"  ✅ ChromaDB conectado")
        print(f"  📊 Collections: {len(collections)}")
        
        for collection in collections:
            count = collection.count()
            print(f"    - {collection.name}: {count} documentos")
            
    except Exception as e:
        print(f"  ❌ Erro ChromaDB: {e}")

def check_api():
    """Verifica API"""
    print("\n🌐 Verificando API...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ API respondendo")
            data = response.json()
            print(f"  📊 Status: {data.get('status', 'unknown')}")
        else:
            print(f"  ❌ API erro {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("  ❌ API não está rodando")
    except Exception as e:
        print(f"  ❌ Erro API: {e}")

def check_files():
    """Verifica arquivos essenciais"""
    print("\n📁 Verificando arquivos...")
    
    essential_files = [
        'api_simple.py', 'api_multiagent.py', 'indexer.py',
        'requirements.txt', 'README.md'
    ]
    
    for file in essential_files:
        if Path(file).exists():
            size = Path(file).stat().st_size
            print(f"  ✅ {file} ({size} bytes)")
        else:
            print(f"  ❌ {file} - FALTANDO")

def main():
    print("🔍 DIAGNÓSTICO COMPLETO DO SISTEMA RAG")
    print("=" * 50)
    
    check_environment()
    check_dependencies()
    check_config()
    check_chromadb()
    check_api()
    check_files()
    
    print("\n" + "=" * 50)
    print("✅ Diagnóstico concluído")

if __name__ == "__main__":
    main()
```

### 2. **Monitor de Performance**

```python
#!/usr/bin/env python3
"""
Monitor de performance em tempo real
"""
import time
import psutil
import requests
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_metrics(self):
        """Coleta métricas do sistema"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('./').percent,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_api_performance(self):
        """Testa performance da API"""
        queries = [
            "teste rápido",
            "consulta média de performance",
            "pergunta complexa sobre arquitetura de sistemas distribuídos"
        ]
        
        results = []
        for query in queries:
            start = time.time()
            try:
                response = requests.post("http://localhost:8000/search", 
                                       json={"query": query, "max_results": 3},
                                       timeout=30)
                latency = time.time() - start
                success = response.status_code == 200
            except:
                latency = 30  # timeout
                success = False
                
            results.append({
                "query": query[:30] + "...",
                "latency": latency,
                "success": success
            })
        
        return results
    
    def monitor(self, duration=60):
        """Monitora por um período"""
        print("🔄 Iniciando monitoramento...")
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Métricas do sistema
            system = self.get_system_metrics()
            print(f"\n⏰ {system['timestamp']}")
            print(f"🖥️  CPU: {system['cpu_percent']:.1f}%")
            print(f"💾 RAM: {system['memory_percent']:.1f}%")
            print(f"💿 Disk: {system['disk_usage']:.1f}%")
            
            # Teste de API
            api_results = self.test_api_performance()
            for result in api_results:
                status = "✅" if result['success'] else "❌"
                print(f"{status} {result['query']}: {result['latency']:.2f}s")
            
            time.sleep(10)

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.monitor(300)  # 5 minutos
```

### 3. **Validador de Configuração**

```python
#!/usr/bin/env python3
"""
Validador completo de configuração
"""
def validate_config():
    """Valida toda a configuração do sistema"""
    issues = []
    
    # Verificar API Key
    import os
    if not os.getenv('OPENAI_API_KEY'):
        issues.append("❌ OPENAI_API_KEY não configurada")
    
    # Verificar ChromaDB
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        if not client.list_collections():
            issues.append("⚠️  ChromaDB sem collections")
    except Exception as e:
        issues.append(f"❌ ChromaDB erro: {e}")
    
    # Verificar dependências
    required = ['fastapi', 'uvicorn', 'openai', 'langchain']
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            issues.append(f"❌ Pacote faltando: {pkg}")
    
    # Verificar arquivos
    from pathlib import Path
    required_files = ['config.py', 'constants.py', 'api_simple.py']
    for file in required_files:
        if not Path(file).exists():
            issues.append(f"❌ Arquivo faltando: {file}")
    
    if not issues:
        print("✅ Configuração válida!")
    else:
        print("🚨 Problemas encontrados:")
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

if __name__ == "__main__":
    validate_config()
```

## 🆘 Suporte e Ajuda

### 📞 Canais de Suporte

1. **Logs do Sistema**: Sempre verificar `api_simple.log` primeiro
2. **Documentação**: Consultar `README.md` e `docs/`
3. **GitHub Issues**: Para bugs e feature requests
4. **Community Forum**: Para dúvidas gerais

### 🔧 Comandos Úteis de Diagnóstico

```bash
# Verificar processos ativos
ps aux | grep python

# Verificar portas em uso
netstat -tulpn | grep :8000

# Verificar logs em tempo real
tail -f api_simple.log

# Testar conectividade
curl -X GET http://localhost:8000/health

# Verificar espaço em disco
df -h

# Verificar memória
free -h
```

### 🏥 Reset Completo do Sistema

```bash
#!/bin/bash
# reset_system.sh - Reset completo em caso de problemas graves

echo "🔄 Iniciando reset completo..."

# Parar todos os processos
pkill -f "uvicorn"
pkill -f "python.*api"

# Limpar cache Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Backup e limpar ChromaDB
mv chroma_db chroma_db.backup.$(date +%Y%m%d_%H%M%S)

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall

# Recriar base de dados
python indexer.py

# Testar configuração
python test_api_config.py

# Iniciar API
uvicorn api_simple:app --reload &

echo "✅ Reset concluído!"
```
