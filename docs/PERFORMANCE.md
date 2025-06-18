# ⚡ Performance e Otimização

## 🎯 Configurações de Performance

### 1. **Configurações Básicas**

#### Configuração Rápida (Desenvolvimento)
```python
# config.py - Configuração para desenvolvimento
class DevConfig:
    # ChromaDB
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    COLLECTION_NAME = "documents_dev"
    
    # Cache
    ENABLE_CACHE = True
    CACHE_SIZE = 100
    CACHE_TTL = 1800  # 30 minutos
    
    # API
    MAX_CONCURRENT_REQUESTS = 5
    REQUEST_TIMEOUT = 30
    
    # LLM
    MODEL_NAME = "gpt-3.5-turbo"  # Mais rápido que GPT-4
    MAX_TOKENS = 1500
    TEMPERATURE = 0.1
```

#### Configuração Balanceada (Produção)
```python
# config.py - Configuração para produção
class ProdConfig:
    # ChromaDB
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    COLLECTION_NAME = "documents_prod"
    
    # Cache
    ENABLE_CACHE = True
    CACHE_SIZE = 1000
    CACHE_TTL = 3600  # 1 hora
    
    # API
    MAX_CONCURRENT_REQUESTS = 20
    REQUEST_TIMEOUT = 60
    
    # LLM
    MODEL_NAME = "gpt-4-turbo-preview"  # Melhor qualidade
    MAX_TOKENS = 3000
    TEMPERATURE = 0.1
```

#### Configuração de Alta Performance
```python
# config.py - Configuração otimizada para velocidade
class HighPerfConfig:
    # ChromaDB com otimizações
    CHUNK_SIZE = 300
    CHUNK_OVERLAP = 30
    COLLECTION_NAME = "documents_fast"
    
    # Cache agressivo
    ENABLE_CACHE = True
    CACHE_SIZE = 2000
    CACHE_TTL = 7200  # 2 horas
    ENABLE_QUERY_CACHE = True
    ENABLE_EMBEDDING_CACHE = True
    
    # API otimizada
    MAX_CONCURRENT_REQUESTS = 50
    REQUEST_TIMEOUT = 15
    ENABLE_COMPRESSION = True
    
    # LLM otimizado
    MODEL_NAME = "gpt-3.5-turbo"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.0  # Determinístico = mais rápido
```

### 2. **Otimização de ChromaDB**

#### Configuração de Embeddings
```python
# constants.py - Otimizações de embedding
EMBEDDING_CONFIGS = {
    "fast": {
        "model": "text-embedding-ada-002",
        "dimensions": 1536,
        "batch_size": 100
    },
    "balanced": {
        "model": "text-embedding-ada-002", 
        "dimensions": 1536,
        "batch_size": 50
    },
    "quality": {
        "model": "text-embedding-ada-002",
        "dimensions": 1536,
        "batch_size": 20
    }
}

# Configuração de indexação
INDEXING_CONFIG = {
    "chunk_size": 800,
    "chunk_overlap": 150,
    "separators": ["\n\n", "\n", ". ", "! ", "? "],
    "metadata_extraction": True
}
```

#### Otimização de Queries
```python
# search.py - Busca otimizada
class OptimizedSearch:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_collection("documents")
        
    def search_with_filters(self, query: str, filters: dict = None, limit: int = 10):
        """Busca com filtros para melhor performance"""
        where_clause = {}
        
        if filters:
            # Filtrar por tipo de documento
            if 'doc_type' in filters:
                where_clause['doc_type'] = filters['doc_type']
            
            # Filtrar por data
            if 'date_range' in filters:
                where_clause['date'] = {"$gte": filters['date_range']['start']}
        
        results = self.collection.query(
            query_texts=[query],
            where=where_clause,
            n_results=limit,
            include=['documents', 'metadatas', 'distances']
        )
        
        return results
    
    def search_with_cache(self, query: str, cache_key: str = None):
        """Busca com cache inteligente"""
        if not cache_key:
            cache_key = hashlib.md5(query.encode()).hexdigest()
        
        # Verificar cache
        cached_result = self.get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Executar busca
        results = self.collection.query(
            query_texts=[query],
            n_results=10
        )
        
        # Salvar no cache
        self.save_to_cache(cache_key, results)
        return results
```

### 3. **Cache Strategy**

#### Implementação de Cache Multi-Layer
```python
# utils/cache.py - Sistema de cache avançado
import redis
import pickle
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta

class MultiLayerCache:
    def __init__(self):
        # Cache em memória (mais rápido)
        self.memory_cache = {}
        self.memory_ttl = {}
        
        # Cache Redis (persistente)
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_available = True
        except:
            self.redis_available = False
            
        # Cache em disco (fallback)
        self.disk_cache_dir = "./cache"
        os.makedirs(self.disk_cache_dir, exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Busca em cache com fallback em cascata"""
        # 1. Tentar cache em memória
        if key in self.memory_cache:
            if self._is_valid(key, self.memory_ttl):
                return self.memory_cache[key]
            else:
                del self.memory_cache[key]
                del self.memory_ttl[key]
        
        # 2. Tentar Redis
        if self.redis_available:
            try:
                data = self.redis_client.get(key)
                if data:
                    result = pickle.loads(data)
                    # Promover para memory cache
                    self.memory_cache[key] = result
                    self.memory_ttl[key] = datetime.now() + timedelta(minutes=30)
                    return result
            except:
                pass
        
        # 3. Tentar disco
        cache_file = os.path.join(self.disk_cache_dir, f"{key}.cache")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    result = pickle.load(f)
                # Promover para caches superiores
                self.set(key, result, ttl=1800)
                return result
            except:
                pass
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Salva em todos os layers de cache"""
        # Memory cache
        self.memory_cache[key] = value
        self.memory_ttl[key] = datetime.now() + timedelta(seconds=ttl)
        
        # Redis cache
        if self.redis_available:
            try:
                self.redis_client.setex(key, ttl, pickle.dumps(value))
            except:
                pass
        
        # Disk cache
        cache_file = os.path.join(self.disk_cache_dir, f"{key}.cache")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except:
            pass
    
    def _is_valid(self, key: str, ttl_dict: dict) -> bool:
        """Verifica se entrada no cache ainda é válida"""
        return key in ttl_dict and datetime.now() < ttl_dict[key]

# Uso do cache
cache = MultiLayerCache()

def cached_search(query: str):
    cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
    
    # Tentar cache primeiro
    result = cache.get(cache_key)
    if result:
        return result
    
    # Executar busca se não estiver em cache
    result = execute_search(query)
    
    # Salvar no cache
    cache.set(cache_key, result, ttl=1800)  # 30 minutos
    return result
```

#### Cache Específico para Embeddings
```python
# utils/embedding_cache.py
class EmbeddingCache:
    def __init__(self):
        self.embeddings_cache = {}
        self.cache_file = "./cache/embeddings.json"
        self.load_cache()
    
    def get_embedding(self, text: str):
        """Busca embedding no cache ou calcula se necessário"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]
        
        # Calcular embedding
        import openai
        embedding = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )['data'][0]['embedding']
        
        # Salvar no cache
        self.embeddings_cache[text_hash] = embedding
        self.save_cache()
        
        return embedding
    
    def load_cache(self):
        """Carrega cache do disco"""
        try:
            with open(self.cache_file, 'r') as f:
                self.embeddings_cache = json.load(f)
        except:
            self.embeddings_cache = {}
    
    def save_cache(self):
        """Salva cache no disco"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.embeddings_cache, f)
        except:
            pass
```

### 4. **Otimização de API**

#### FastAPI com Async
```python
# api_optimized.py - API otimizada
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvloop  # Performance boost para async

# Usar uvloop para melhor performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

app = FastAPI(
    title="RAG Multi-Agent API Optimized",
    description="Versão otimizada da API",
    version="2.0.0"
)

# Middleware de compressão
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS otimizado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Pool de conexões reutilizáveis
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=10)

@app.post("/search-async")
async def search_async(request: SearchRequest):
    """Busca assíncrona otimizada"""
    loop = asyncio.get_event_loop()
    
    # Executar busca em thread separada
    result = await loop.run_in_executor(
        executor, 
        execute_search, 
        request.query
    )
    
    return result

@app.post("/batch-search")
async def batch_search(requests: List[SearchRequest]):
    """Busca em lote para múltiplas queries"""
    tasks = []
    
    for req in requests:
        task = asyncio.create_task(search_async(req))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return {"results": results}
```

#### Rate Limiting Inteligente
```python
# utils/rate_limiter.py
from collections import defaultdict, deque
import time

class SmartRateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        self.limits = {
            "search": 60,      # 60 por minuto
            "chat": 30,        # 30 por minuto  
            "research": 10     # 10 por minuto
        }
    
    def is_allowed(self, client_id: str, endpoint: str) -> bool:
        """Verifica se request é permitida"""
        now = time.time()
        minute_ago = now - 60
        
        # Limpar requests antigas
        while (self.requests[client_id] and 
               self.requests[client_id][0] < minute_ago):
            self.requests[client_id].popleft()
        
        # Verificar limite
        limit = self.limits.get(endpoint, 100)
        if len(self.requests[client_id]) >= limit:
            return False
        
        # Adicionar request atual
        self.requests[client_id].append(now)
        return True

rate_limiter = SmartRateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    endpoint = request.url.path.split('/')[-1]
    
    if not rate_limiter.is_allowed(client_ip, endpoint):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"}
        )
    
    response = await call_next(request)
    return response
```

### 5. **Monitoramento de Performance**

#### Métricas Avançadas
```python
# utils/performance_monitor.py
import time
import psutil
from collections import deque
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "request_times": deque(maxlen=1000),
            "memory_usage": deque(maxlen=100),
            "cpu_usage": deque(maxlen=100),
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0
        }
        
        # Iniciar coleta de métricas do sistema
        self.start_system_monitoring()
    
    def record_request(self, duration: float):
        """Registra tempo de uma requisição"""
        self.metrics["request_times"].append(duration)
        self.metrics["total_requests"] += 1
    
    def record_cache_hit(self):
        """Registra cache hit"""
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        """Registra cache miss"""
        self.metrics["cache_misses"] += 1
    
    def get_stats(self) -> dict:
        """Retorna estatísticas atuais"""
        request_times = list(self.metrics["request_times"])
        
        stats = {
            "avg_response_time": sum(request_times) / len(request_times) if request_times else 0,
            "p95_response_time": sorted(request_times)[int(0.95 * len(request_times))] if request_times else 0,
            "cache_hit_rate": self.metrics["cache_hits"] / (self.metrics["cache_hits"] + self.metrics["cache_misses"]) if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0 else 0,
            "total_requests": self.metrics["total_requests"],
            "current_memory": psutil.virtual_memory().percent,
            "current_cpu": psutil.cpu_percent()
        }
        
        return stats
    
    def start_system_monitoring(self):
        """Inicia monitoramento do sistema em background"""
        import threading
        
        def monitor():
            while True:
                self.metrics["memory_usage"].append(psutil.virtual_memory().percent)
                self.metrics["cpu_usage"].append(psutil.cpu_percent())
                time.sleep(10)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

# Singleton global
monitor = PerformanceMonitor()

# Decorator para medir performance
def measure_performance(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        monitor.record_request(duration)
        return result
    return wrapper

# Endpoint de métricas
@app.get("/metrics")
def get_metrics():
    return monitor.get_stats()
```

### 6. **Benchmarking e Testes de Carga**

#### Script de Benchmark
```python
#!/usr/bin/env python3
"""
Benchmark completo do sistema RAG
"""
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

class RAGBenchmark:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def single_request(self, session, query):
        """Executa uma única requisição"""
        start = time.time()
        
        try:
            async with session.post(f"{self.base_url}/search", 
                                  json={"query": query, "max_results": 5}) as response:
                await response.json()
                success = response.status == 200
        except:
            success = False
        
        duration = time.time() - start
        return {"duration": duration, "success": success, "query": query}
    
    async def load_test(self, queries, concurrent_users=10, iterations=5):
        """Teste de carga com múltiplos usuários simultâneos"""
        print(f"🔥 Iniciando teste de carga: {concurrent_users} usuários, {iterations} iterações")
        
        all_tasks = []
        
        async with aiohttp.ClientSession() as session:
            for iteration in range(iterations):
                tasks = []
                for query in queries[:concurrent_users]:
                    task = self.single_request(session, query)
                    tasks.append(task)
                
                # Executar todas as requisições simultaneamente
                batch_results = await asyncio.gather(*tasks)
                all_tasks.extend(batch_results)
                
                print(f"  Iteração {iteration + 1}/{iterations} concluída")
        
        return all_tasks
    
    def analyze_results(self, results):
        """Analisa resultados do benchmark"""
        durations = [r["duration"] for r in results if r["success"]]
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        if not durations:
            return {"error": "Nenhuma requisição bem-sucedida"}
        
        analysis = {
            "total_requests": len(results),
            "success_rate": success_rate,
            "avg_duration": statistics.mean(durations),
            "median_duration": statistics.median(durations),
            "p95_duration": sorted(durations)[int(0.95 * len(durations))],
            "p99_duration": sorted(durations)[int(0.99 * len(durations))],
            "min_duration": min(durations),
            "max_duration": max(durations),
            "requests_per_second": len(durations) / sum(durations) if sum(durations) > 0 else 0
        }
        
        return analysis
    
    def print_report(self, analysis):
        """Imprime relatório formatado"""
        print("\n" + "="*50)
        print("📊 RELATÓRIO DE PERFORMANCE")
        print("="*50)
        print(f"Total de requisições: {analysis['total_requests']}")
        print(f"Taxa de sucesso: {analysis['success_rate']:.1%}")
        print(f"Duração média: {analysis['avg_duration']:.3f}s")
        print(f"Mediana: {analysis['median_duration']:.3f}s")
        print(f"P95: {analysis['p95_duration']:.3f}s")
        print(f"P99: {analysis['p99_duration']:.3f}s")
        print(f"Min/Max: {analysis['min_duration']:.3f}s / {analysis['max_duration']:.3f}s")
        print(f"Requests/segundo: {analysis['requests_per_second']:.1f}")
        print("="*50)

async def main():
    benchmark = RAGBenchmark()
    
    # Queries de teste
    test_queries = [
        "Como configurar Docker?",
        "Explicar microserviços",
        "Tutorial FastAPI",
        "Implementar cache Redis",
        "Arquitetura de sistemas distribuídos",
        "Padrões de design",
        "Segurança em APIs",
        "Monitoramento de aplicações",
        "CI/CD com GitHub Actions",
        "Testes automatizados"
    ]
    
    # Teste com diferentes cargas
    scenarios = [
        {"users": 5, "iterations": 3},
        {"users": 10, "iterations": 3},
        {"users": 20, "iterations": 2}
    ]
    
    for scenario in scenarios:
        print(f"\n🎯 Cenário: {scenario['users']} usuários")
        results = await benchmark.load_test(
            test_queries, 
            concurrent_users=scenario['users'],
            iterations=scenario['iterations']
        )
        
        analysis = benchmark.analyze_results(results)
        benchmark.print_report(analysis)

if __name__ == "__main__":
    asyncio.run(main())
```

### 7. **Otimizações de Deploy**

#### Docker Otimizado
```dockerfile
# Dockerfile.optimized
FROM python:3.11-slim

# Instalar dependências de sistema otimizadas
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .

# Instalar dependências Python com otimizações
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Mudar proprietário
RUN chown -R appuser:appuser /app

USER appuser

# Configurar Python para performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONOPTIMIZE=1

# Usar Gunicorn com workers otimizados
CMD ["gunicorn", "api_simple:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
```

#### Docker Compose para Produção
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.optimized
    ports:
      - "8000-8003:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./logs:/app/logs
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  redis_data:
```

#### Configuração Nginx para Produção
```nginx
# nginx.prod.conf
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    upstream api_backend {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
        server api:8001 max_fails=3 fail_timeout=30s;
        server api:8002 max_fails=3 fail_timeout=30s;
        server api:8003 max_fails=3 fail_timeout=30s;
    }

    # Cache de conteúdo estático
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m use_temp_path=off;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com;

        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        # Compressão
        gzip on;
        gzip_comp_level 6;
        gzip_types text/plain text/css application/json application/javascript text/javascript;

        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;

            # Cache para endpoints específicos
            location /health {
                proxy_pass http://api_backend;
                proxy_cache api_cache;
                proxy_cache_valid 200 5m;
                add_header X-Cache-Status $upstream_cache_status;
            }
        }
    }
}
```

### 🎯 Resumo de Otimizações

#### Quick Wins (Implementação Rápida)
1. **Cache de queries** - 50-80% melhoria
2. **Chunking otimizado** - 20-30% melhoria  
3. **Rate limiting** - Estabilidade
4. **Compressão gzip** - 30-50% redução de bandwidth

#### Melhorias Médias (Algumas horas)
1. **Cache multi-layer** - 60-90% melhoria
2. **API assíncrona** - 2-3x mais throughput
3. **Connection pooling** - 20-40% melhoria
4. **Monitoramento** - Visibilidade total

#### Otimizações Avançadas (Projeto maior)
1. **Deploy distribuído** - Escalabilidade horizontal
2. **CDN para cache** - Latência global
3. **Database clustering** - Alta disponibilidade
4. **ML para cache inteligente** - Cache preditivo
