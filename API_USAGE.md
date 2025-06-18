# 🚀 Guia de Uso - APIs de Produção
# Sistema RAG Multi-Agente

## 📋 Visão Geral

Este sistema fornece duas APIs de produção para diferentes tipos de consultas:

1. **API RAG Simples** (`api_simple.py`) - Consultas diretas com busca semântica
2. **API Multi-Agente** (`api_multiagent.py`) - Consultas complexas com reasoning avançado

## 🔧 Instalação e Configuração

### Dependências

```bash
# Instalar dependências principais
pip install -r requirements.txt

# Instalar dependências específicas das APIs
pip install -r requirements_api.txt
```

### Variáveis de Ambiente

Configure o arquivo `.env` com as seguintes variáveis:

```bash
# === MODELOS E APIs ===
OPENAI_API_KEY=your_openai_key
VOYAGE_API_KEY=your_voyage_key
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
ASTRA_DB_APPLICATION_TOKEN=your_astra_token

# === CONFIGURAÇÃO DAS APIs ===
API_HOST=0.0.0.0
API_PORT_SIMPLE=8000
API_PORT_MULTIAGENT=8001
API_LOG_LEVEL=info
API_WORKERS=1
API_RELOAD=false

# === CONFIGURAÇÃO DO SISTEMA ===
RAG_MAX_CANDIDATES=10
RAG_SIMILARITY_THRESHOLD=0.7
MULTIAGENT_MAX_SUBAGENTS=5
MULTIAGENT_TIMEOUT=300
```

## 🚀 Executando as APIs

### Método 1: Execução Direta

```bash
# API RAG Simples (porta 8000)
python api_simple.py

# API Multi-Agente (porta 8001)
python api_multiagent.py
```

### Método 2: Docker Compose (Recomendado)

```bash
# Construir e executar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

### Método 3: Docker Individual

```bash
# API RAG Simples
docker build -f Dockerfile.api-simple -t rag-simple-api .
docker run -p 8000:8000 --env-file .env rag-simple-api

# API Multi-Agente
docker build -f Dockerfile.api-multiagent -t rag-multiagent-api .
docker run -p 8001:8001 --env-file .env rag-multiagent-api
```

## 📊 API RAG Simples

### Características

- **Porta padrão:** 8000
- **Uso:** Consultas diretas e rápidas
- **Processamento:** Busca semântica direta
- **Tempo médio:** 5-30 segundos

### Endpoints Principais

#### `POST /search` - Busca RAG Simples

```bash
curl -X POST "http://localhost:8000/search" \
-H "Content-Type: application/json" \
-d '{
  "query": "O que é inteligência artificial?",
  "max_results": 5,
  "similarity_threshold": 0.7,
  "include_metadata": true
}'
```

**Resposta:**
```json
{
  "success": true,
  "query": "O que é inteligência artificial?",
  "response": "Inteligência artificial (IA) é...",
  "results_count": 5,
  "processing_time": 12.5,
  "timestamp": "2024-01-15T10:30:00Z",
  "sources": [
    {
      "page_num": 1,
      "similarity_score": 0.85,
      "doc_source": "ai_fundamentals",
      "excerpt": "Inteligência artificial refere-se..."
    }
  ],
  "metadata": {
    "request_id": "req_1705312200_1",
    "model_used": "gpt-4o"
  }
}
```

#### `GET /health` - Status da API

```bash
curl http://localhost:8000/health
```

#### `GET /config` - Configuração Atual

```bash
curl http://localhost:8000/config
```

### Exemplos de Uso Python

```python
import requests

# Configuração
API_BASE = "http://localhost:8000"

def simple_rag_search(query, max_results=5):
    url = f"{API_BASE}/search"
    payload = {
        "query": query,
        "max_results": max_results,
        "include_metadata": True
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Resposta: {result['response']}")
        print(f"Tempo: {result['processing_time']:.2f}s")
        print(f"Fontes: {result['results_count']}")
        return result
    else:
        print(f"Erro: {response.status_code}")
        return None

# Exemplo de uso
result = simple_rag_search("Como funciona machine learning?")
```

## 🤖 API Multi-Agente

### Características

- **Porta padrão:** 8001
- **Uso:** Consultas complexas que requerem reasoning
- **Processamento:** Sistema multi-agente com especialização
- **Tempo médio:** 30-300 segundos
- **Recursos:** Processamento síncrono, assíncrono e streaming

### Endpoints Principais

#### `POST /research` - Pesquisa Multi-Agente

**Processamento Síncrono:**
```bash
curl -X POST "http://localhost:8001/research" \
-H "Content-Type: application/json" \
-d '{
  "query": "Compare as vantagens e desvantagens do TensorFlow vs PyTorch para deep learning",
  "objective": "Fornecer análise comparativa detalhada",
  "processing_mode": "sync",
  "include_reasoning": true,
  "max_agents": 3
}'
```

**Processamento Assíncrono:**
```bash
curl -X POST "http://localhost:8001/research" \
-H "Content-Type: application/json" \
-d '{
  "query": "Análise completa das tendências de IA em 2024",
  "processing_mode": "async",
  "timeout_seconds": 300
}'
```

**Resposta (Síncrono):**
```json
{
  "success": true,
  "job_id": "job_a1b2c3d4_1705312200",
  "query": "Compare TensorFlow vs PyTorch...",
  "objective": "Fornecer análise comparativa detalhada",
  "final_answer": "Análise comparativa detalhada...",
  "confidence_score": 0.92,
  "processing_time": 87.3,
  "complexity_detected": "complex",
  "agents_used": [
    {
      "agent_id": "comparative_001",
      "agent_type": "ComparativeAnalysisSubagent",
      "status": "completed",
      "execution_time": 45.2
    }
  ],
  "reasoning_trace": [
    "Identificando necessidade de análise comparativa...",
    "Coletando informações sobre TensorFlow...",
    "Coletando informações sobre PyTorch..."
  ],
  "metadata": {
    "model": "gpt-4o-mini",
    "lead_agent": "OpenAILeadResearcher"
  }
}
```

#### `GET /research/{job_id}` - Status de Job Assíncrono

```bash
curl http://localhost:8001/research/job_a1b2c3d4_1705312200
```

#### `POST /analyze-complexity` - Análise de Complexidade

```bash
curl -X POST "http://localhost:8001/analyze-complexity" \
-H "Content-Type: application/json" \
-d '{
  "query": "Implementar algoritmo de otimização para redes neurais profundas"
}'
```

#### WebSocket `/research/stream` - Processamento em Tempo Real

```javascript
// Exemplo JavaScript para WebSocket
const ws = new WebSocket('ws://localhost:8001/research/stream');

ws.onopen = function() {
    // Enviar query
    ws.send(JSON.stringify({
        query: "Explicar quantum computing e suas aplicações",
        processing_mode: "stream",
        include_reasoning: true
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'status') {
        console.log('Status:', data.message);
    } else if (data.type === 'result') {
        console.log('Resultado:', data.data);
    }
};
```

### Exemplos de Uso Python

```python
import requests
import time

API_BASE = "http://localhost:8001"

def multiagent_research_sync(query, objective=None):
    """Pesquisa síncrona"""
    url = f"{API_BASE}/research"
    payload = {
        "query": query,
        "objective": objective or f"Pesquisar sobre: {query}",
        "processing_mode": "sync",
        "include_reasoning": True
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Resposta: {result['final_answer']}")
        print(f"Confiança: {result['confidence_score']:.2f}")
        print(f"Agentes usados: {len(result['agents_used'])}")
        return result
    else:
        print(f"Erro: {response.status_code}")
        return None

def multiagent_research_async(query):
    """Pesquisa assíncrona"""
    # Iniciar job
    url = f"{API_BASE}/research"
    payload = {
        "query": query,
        "processing_mode": "async"
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        job_id = result["job_id"]
        print(f"Job iniciado: {job_id}")
        
        # Aguardar conclusão
        while True:
            status_response = requests.get(f"{API_BASE}/research/{job_id}")
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"Status: {status['status']} - {status['progress']:.1%}")
                
                if status["status"] == "completed":
                    return status["result"]
                elif status["status"] == "failed":
                    print(f"Erro: {status.get('error', 'Unknown error')}")
                    return None
            
            time.sleep(5)  # Aguardar 5 segundos

# Exemplos de uso
print("=== Pesquisa Síncrona ===")
result = multiagent_research_sync(
    "Compare metodologias ágeis vs waterfall",
    "Análise comparativa para escolha de metodologia"
)

print("\n=== Pesquisa Assíncrona ===")
result = multiagent_research_async(
    "Análise detalhada de blockchain e suas aplicações"
)
```

## 🐳 Deployment com Docker

### Arquivo docker-compose.yml

O arquivo inclui:
- **APIs**: RAG Simples e Multi-Agente
- **Redis**: Cache opcional
- **Nginx**: Load balancer e proxy reverso

### Configuração de Produção

```bash
# Construir imagens
docker-compose build

# Executar em produção
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f rag-simple-api
docker-compose logs -f rag-multiagent-api

# Atualizar configuração
docker-compose restart

# Parar tudo
docker-compose down
```

### Acesso via Nginx

Com o Nginx configurado, as APIs ficam disponíveis em:

- **Dashboard**: http://localhost/
- **API RAG Simples**: http://localhost/api/simple/
- **API Multi-Agente**: http://localhost/api/multiagent/
- **Documentação**: 
  - http://localhost/api/simple/docs
  - http://localhost/api/multiagent/docs

## 📊 Monitoramento e Métricas

### Health Checks

```bash
# Status individual das APIs
curl http://localhost:8000/health
curl http://localhost:8001/health

# Status via Nginx
curl http://localhost/health
```

### Métricas

```bash
# Métricas das APIs
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics

# Jobs ativos (Multi-Agente)
curl http://localhost:8001/jobs
```

### Logs

```bash
# Logs em tempo real
docker-compose logs -f

# Logs específicos
docker-compose logs rag-simple-api
docker-compose logs rag-multiagent-api
docker-compose logs nginx
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente Completas

```bash
# === APIs ===
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=false
API_LOG_LEVEL=info

# === RATE LIMITING ===
API_RATE_LIMIT=100
API_BURST_LIMIT=20

# === CACHE ===
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# === MONITORAMENTO ===
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_PORT=9090

# === SEGURANÇA ===
API_KEY_REQUIRED=false
JWT_SECRET=your_jwt_secret
```

### Customização de Modelos

```bash
# Modelos específicos por API
RAG_SIMPLE_LLM_MODEL=gpt-4o
RAG_SIMPLE_EMBEDDING_MODEL=voyage-3

MULTIAGENT_LLM_MODEL=gpt-4o-mini
MULTIAGENT_EMBEDDING_MODEL=voyage-3
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **API não responde:**
   ```bash
   # Verificar se o serviço está rodando
   docker-compose ps
   
   # Verificar logs
   docker-compose logs api-service-name
   ```

2. **Timeout em consultas:**
   ```bash
   # Aumentar timeout no .env
   MULTIAGENT_TIMEOUT=600
   ```

3. **Erro de conexão com banco:**
   ```bash
   # Verificar variáveis de ambiente
   echo $ASTRA_DB_API_ENDPOINT
   echo $ASTRA_DB_APPLICATION_TOKEN
   ```

4. **Memória insuficiente:**
   ```bash
   # Reduzir concorrência
   MULTIAGENT_MAX_SUBAGENTS=3
   PROCESSING_CONCURRENCY=2
   ```

### Logs de Debug

```bash
# Ativar logs detalhados
API_LOG_LEVEL=debug

# Logs específicos do sistema
PYTHONPATH=/app python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from config import SystemConfig
config = SystemConfig()
print(config.validate_all())
"
```

## 📚 Referências

- **FastAPI**: https://fastapi.tiangolo.com/
- **Uvicorn**: https://www.uvicorn.org/
- **Docker Compose**: https://docs.docker.com/compose/
- **Nginx**: https://nginx.org/en/docs/
- **Sistema RAG**: Ver README.md principal

---

## 🎯 Resumo de Endpoints

### API RAG Simples (`:8000`)
- `GET /` - Informações da API
- `GET /health` - Health check
- `GET /config` - Configuração atual
- `GET /metrics` - Métricas básicas
- `POST /search` - Busca RAG simples

### API Multi-Agente (`:8001`)
- `GET /` - Informações da API
- `GET /health` - Health check
- `GET /specialists` - Lista de especialistas
- `GET /jobs` - Jobs ativos
- `POST /analyze-complexity` - Análise de complexidade
- `POST /research` - Pesquisa multi-agente
- `GET /research/{job_id}` - Status de job
- `WebSocket /research/stream` - Streaming

### Nginx (`:80`)
- `GET /` - Dashboard principal
- `/api/simple/*` - Proxy para API RAG Simples
- `/api/multiagent/*` - Proxy para API Multi-Agente
- `GET /status` - Status geral
- `GET /metrics` - Métricas do Nginx