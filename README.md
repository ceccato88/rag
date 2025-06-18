# 🤖 Sistema RAG Multi-Agente

Sistema de IA avançado com busca semântica e raciocínio multi-agente para consultas complexas.

## 🚀 Início Rápido

### 1. Configurar Variáveis
```bash
# Edite .env com suas chaves reais
OPENAI_API_KEY=sk-proj-sua-chave-aqui
VOYAGE_API_KEY=pa-sua-chave-aqui
ASTRA_DB_API_ENDPOINT=https://sua-db-aqui
ASTRA_DB_APPLICATION_TOKEN=AstraCS:seu-token-aqui
API_BEARER_TOKEN=$(openssl rand -hex 32)
```

### 2. Iniciar Sistema
```bash
./production-start.sh
```

### 3. Verificar Segurança
```bash
./security-check.sh
```

## 📊 APIs Disponíveis

### API Simples (Porta 8000)
- **Busca Rápida**: Consultas diretas com RAG otimizado
- **Performance**: Baixa latência, ideal para buscas simples
- **Endpoint**: `POST /search`

### API Multi-Agente (Porta 8001)
- **Raciocínio Avançado**: Consultas complexas com múltiplos agentes
- **Especialização**: Agentes especializados por tipo de consulta  
- **Modos**: Síncrono, assíncrono e streaming
- **Endpoint**: `POST /research`

### Indexação de Documentos (Ambas APIs)
- **Indexação por URL**: Processa PDFs de URLs
- **Extração Multimodal**: Texto e imagens
- **Chunking Inteligente**: Divisão otimizada
- **Endpoint**: `POST /index`

## 🔧 Uso

### Busca Simples
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer $API_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning"}'
```

### Pesquisa Multi-Agente
```bash
curl -X POST "http://localhost:8001/research" \
  -H "Authorization: Bearer $API_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain neural networks in detail",
    "processing_mode": "sync"
  }'
```

### Indexação de Documento
```bash
curl -X POST "http://localhost:8000/index" \
  -H "Authorization: Bearer $API_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://arxiv.org/pdf/2501.13956",
    "doc_source": "arxiv_2024_paper"
  }'
```

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐
│   API Simples   │    │ API Multi-Agent │
│    (Porta 8000) │    │   (Porta 8001)  │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
            ┌─────────────────┐
            │   Vector DB     │
            │   (AstraDB)     │
            └─────────────────┘
```

### Componentes Principais
- **SimpleRAG**: Busca vetorial otimizada
- **EnhancedRAG**: Sistema multi-agente com especialização
- **DistributedMemory**: Cache hierárquico com sharding
- **Specialist Agents**: Agentes especializados por domínio

## 🛠️ Comandos Úteis

```bash
# Iniciar sistema
./production-start.sh

# Ver logs
docker-compose logs -f

# Parar sistema  
./production-stop.sh

# Deploy completo
./deploy.sh

# Verificar segurança
./security-check.sh
```

## ⚙️ Configuração Avançada

### Performance
```env
API_WORKERS=4              # Workers por API
MAX_SUBAGENTS=5           # Agentes simultâneos
CONCURRENCY_LIMIT=10      # Limite de concorrência
```

### Cache
```env
REDIS_URL=redis://redis:6379
ENABLE_DISTRIBUTED_CACHE=true
CACHE_TTL=7200
```

### Segurança
```env
ENABLE_CORS=false         # CORS desabilitado
API_RATE_LIMIT=100        # Requests por minuto
DEBUG=false               # Debug desabilitado
```

## 🔒 Segurança

- **Token Bearer fixo** para autenticação
- **CORS desabilitado** por padrão
- **Rate limiting** configurado
- **Containers não-root**
- **Resource limits** aplicados
- **Headers de segurança** no Nginx

## 🛠️ Endpoints de Manutenção (Protegidos)

### Limpeza de Dados
```bash
# Deletar TODOS os documentos
curl -X DELETE "http://localhost:8000/maintenance/collection?all_docs=true" \
  -H "Authorization: Bearer $API_BEARER_TOKEN"

# Deletar documentos por prefixo
curl -X DELETE "http://localhost:8000/maintenance/documents?doc_prefix=arxiv_2024" \
  -H "Authorization: Bearer $API_BEARER_TOKEN"

# Deletar TODAS as imagens
curl -X DELETE "http://localhost:8001/maintenance/images?all_images=true" \
  -H "Authorization: Bearer $API_BEARER_TOKEN"
```

## 📈 Monitoramento

- **Health checks**: `/health` em ambas APIs
- **Métricas**: Prometheus (opcional, perfil `monitoring`)
- **Logs estruturados**: JSON com rotação automática
- **Alertas**: Via status codes e logs

## 🔧 Troubleshooting

### APIs não respondem
```bash
docker-compose ps
docker-compose logs api-simple api-multiagent
```

### Problemas de memória
```bash
docker stats
# Ajustar limits no docker-compose.yml
```

### Verificar configuração
```bash
./security-check.sh
curl http://localhost:8000/health
curl http://localhost:8001/health
```

---

**URLs**: 
- API Simples: http://localhost:8000
- API Multi-Agente: http://localhost:8001  
- Nginx: http://localhost (produção)