# 📋 Resumo das Configurações - Sistema RAG Refatorado v2.0.0

## 🎯 Visão Geral

Sistema completamente refatorado com configurações otimizadas para uso de modelos nativos e arquitetura simplificada.

## ⚙️ Arquivos de Configuração

### 1. `.env` - Variáveis de Ambiente
```bash
# Configurações principais
API_PORT=8000                    # API Multi-Agente
API_SIMPLE_PORT=8001            # API RAG Simples  
PRODUCTION_MODE=true            # Modo de produção
NATIVE_MODELS_ONLY=true         # Apenas modelos nativos
FACTORY_PATTERN_ENABLED=true    # Factory patterns ativos
```

### 2. `constants.py` - Constantes do Sistema
```python
# Novas configurações para APIs refatoradas
API_REFACTORED_CONFIG = {
    'MULTIAGENT_API_PORT': 8001,
    'SIMPLE_API_PORT': 8000,
    'FACTORY_PATTERN_ENABLED': True,
    'NATIVE_MODELS_ONLY': True
}

NATIVE_MODELS_CONFIG = {
    'AGENT_RESULT': 'researcher.agents.base.AgentResult',
    'SIMPLE_RAG': 'search.SimpleRAG',
    'RESPONSE_FACTORY': 'ResponseFactory'
}
```

### 3. `config.py` - Classes de Configuração
```python
class APIRefactoredConfig:
    """Configurações específicas das APIs refatoradas"""
    
class SystemConfig:
    """Configuração central com suporte às APIs refatoradas"""
```

## 🔧 Principais Mudanças

### ✅ APIs Refatoradas
- **API Multi-Agente** (Port 8000): 4 workers, 3GB RAM
- **API RAG Simples** (Port 8001): 2 workers, 1.5GB RAM
- **Modelos Nativos**: AgentResult, AgentContext, SimpleRAG
- **Factory Patterns**: ResponseFactory, SimpleResponseFactory

### ✅ Configurações de Produção
- **Rate Limiting**: 100 req/min, 20 concurrent
- **Monitoring**: Prometheus + Grafana + health checks
- **Security**: Headers de segurança, CORS restritivo
- **Logging**: Estruturado, rotação automática

### ✅ Docker Otimizado
- **Health Checks**: 30s interval, 15s timeout
- **Resource Limits**: CPU e memória por serviço
- **Profiles**: cache, loadbalancer, monitoring
- **Networks**: rag-network isolado

## 📊 Configurações por Ambiente

### Desenvolvimento
```bash
PRODUCTION_MODE=false
DEBUG_MODE=true
VERBOSE_LOGGING=true
API_RELOAD=true
```

### Produção
```bash
PRODUCTION_MODE=true
DEBUG_MODE=false
VERBOSE_LOGGING=false
ENABLE_RATE_LIMITING=true
MONITORING_ENABLED=true
```

## 🌐 Endpoints Configurados

### API Multi-Agente (Port 8000)
- `GET /health` - Health check
- `POST /research` - Pesquisa multi-agente
- `POST /index` - Indexação de documentos
- `DELETE /documents/{collection}` - Remoção
- `GET /stats` - Estatísticas

### API RAG Simples (Port 8001)
- `GET /health` - Health check
- `POST /search` - Busca simples
- `DELETE /documents/{collection}` - Remoção
- `GET /config` - Configuração atual
- `GET /stats` - Estatísticas

## ⚡ Performance e Limites

### Timeouts Otimizados
```bash
DATABASE_TIMEOUT=10s
REDIS_TIMEOUT=5s
EXTERNAL_API_TIMEOUT=15s
SUBAGENT_TIMEOUT=180s
```

### Cache Hierárquico
```bash
EMBEDDING_CACHE_SIZE=1000
RESPONSE_CACHE_SIZE=200
L1_CACHE_MAX_SIZE=1000
L2_CACHE_MAX_SIZE=5000
```

### Processamento
```bash
BATCH_SIZE=100
PROCESSING_CONCURRENCY=5
MAX_SUBAGENTS=3
PARALLEL_EXECUTION=true
```

## 🔒 Segurança

### Autenticação
```bash
API_BEARER_TOKEN=EkRxL063pHbrAd6wMjoOQJyX_WN75Kmoc624hago3VA
```

### Headers de Segurança
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

### CORS
```bash
ENABLE_CORS=false           # Produção
CORS_ORIGINS=https://yourdomain.com
```

## 📈 Monitoramento

### Logs
```bash
LOG_LEVEL=INFO
MAX_LOG_FILE_SIZE=50MB
LOG_ROTATION_COUNT=10
ASYNC_LOGGING=true
```

### Métricas
```bash
ENABLE_PERFORMANCE_METRICS=true
MONITORING_ENABLED=true
HEALTH_CHECK_INTERVAL=60s
```

## 🐳 Docker Profiles

### Básico (APIs apenas)
```bash
docker-compose up
```

### Com Cache
```bash
docker-compose --profile cache up
```

### Com Load Balancer
```bash
docker-compose --profile loadbalancer up
```

### Monitoramento Completo
```bash
docker-compose --profile monitoring up
```

## 🔍 Validação das Configurações

### Comando de Teste
```bash
python config.py
```

### Saída Esperada
```
🔧 STATUS DAS CONFIGURAÇÕES REFATORADAS v2.0.0
✅ Todas as configurações válidas!
📊 Status dos componentes:
  • RAG: ✅
  • Multi-Agente: ✅
  • Produção: ✅
  • APIs Refatoradas: ✅
```

## 🆘 Troubleshooting

### Problemas Comuns
1. **Ports ocupados**: Alterar `API_PORT` e `API_SIMPLE_PORT`
2. **Timeout baixo**: Aumentar `SUBAGENT_TIMEOUT`
3. **Cache pequeno**: Aumentar `*_CACHE_SIZE`
4. **Rate limit**: Ajustar `MAX_REQUESTS_PER_MINUTE`

### Logs de Debug
```bash
# Ativar logs detalhados
VERBOSE_LOGGING=true
LOG_LEVEL=DEBUG

# Verificar configuração
python -c "from config import SystemConfig; SystemConfig().print_status()"
```

## 📁 Estrutura de Arquivos

```
/workspaces/rag/
├── .env                    # Variáveis de ambiente
├── config.py              # Classes de configuração
├── constants.py           # Constantes do sistema
├── api_multiagent.py      # API refatorada multi-agente
├── api_simple.py          # API refatorada RAG simples
├── docker-compose.yml     # Orquestração Docker
├── Dockerfile.api-*       # Images Docker
└── nginx_rag.conf         # Load balancer config
```

---

**Sistema RAG Multi-Agente Refatorado v2.0.0**  
*Configurações otimizadas para produção com modelos nativos*