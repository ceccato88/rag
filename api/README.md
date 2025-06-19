# 🚀 Sistema RAG Multi-Agente v2.0.0

API REST moderna e modular para sistema RAG (Retrieval-Augmented Generation) multi-agente, construída com FastAPI e arquitetura limpa.

## ✨ Características Principais

### 🏗️ **Arquitetura Modular**
- **Separação clara de responsabilidades**
- **Código bem organizado e manutenível**
- **Pydantic V2** com field_validators modernos
- **Injeção de dependências** bem estruturada

### 🤖 **Sistema Multi-Agente**
- **Lead Researcher**: Agente principal para pesquisas complexas
- **Memória de Pesquisa**: Sistema de contexto persistente
- **RAG Simples**: Sistema de busca vetorial rápido

### 📄 **Indexação Inteligente**
- **Processamento de PDF**: Extração de texto e imagens
- **Chunking Semântico**: Divisão inteligente de conteúdo
- **Embeddings Vetoriais**: Busca por similaridade

### 🛡️ **Recursos de Produção**
- **Autenticação Bearer Token**: Segurança robusta
- **Rate Limiting**: Proteção contra abuso (100 req/min)
- **Middlewares Customizados**: Logging, métricas, segurança
- **Health Checks**: Verificação detalhada de saúde
- **Error Handling**: Tratamento estruturado de erros

## 📁 Estrutura do Projeto

```
api/
├── 📁 core/                 # Módulos centrais
│   ├── config.py           # Configuração centralizada (Pydantic V2)
│   └── state.py            # Gerenciamento de estado thread-safe
├── 📁 utils/                # Utilitários
│   ├── errors.py           # Sistema de tratamento de erros
│   └── middleware.py       # Middlewares customizados
├── 📁 models/               # Schemas de dados
│   └── schemas.py          # Modelos Pydantic V2
├── 📁 routers/              # Endpoints organizados
│   ├── research.py         # Endpoints de pesquisa
│   ├── indexing.py         # Endpoints de indexação
│   └── management.py       # Health checks e administração
├── dependencies.py         # Injeção de dependências
├── main.py                 # Aplicação principal
├── requirements.txt        # Dependências
└── .env.example           # Exemplo de configuração
```

## 🚀 Instalação e Configuração

### 1. **Instalar Dependências**
```bash
cd /workspaces/rag/api
pip install -r requirements.txt
```

### 2. **Configurar Ambiente**
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

### 3. **Configurações Obrigatórias**
```bash
# Database (AstraDB)
ASTRA_DB_API_ENDPOINT=https://your-database-id-region.apps.astra.datastax.com
ASTRA_DB_APPLICATION_TOKEN=AstraCS:your-token-here

# AI Models
OPENAI_API_KEY=sk-your-openai-key-here
VOYAGE_API_KEY=pa-your-voyage-key-here

# Security (Produção)
API_BEARER_TOKEN=your-secure-token-here
```

## 🎯 Executando a API

### **Desenvolvimento**
```bash
python main.py
```

### **Produção com Uvicorn**
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 📖 Uso da API

### **Documentação Interativa**
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### **Autenticação**
Todos os endpoints (exceto `/health`) requerem Bearer Token:
```bash
Authorization: Bearer YOUR_API_TOKEN
```

### **Exemplos de Uso**

#### 🔍 **Pesquisa**
```bash
curl -X POST "http://localhost:8001/api/v1/research" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Como funciona machine learning?",
       "objective": "Explicação para iniciantes"
     }'
```

#### 📄 **Indexação**
```bash
curl -X POST "http://localhost:8001/api/v1/index" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://arxiv.org/pdf/2301.00001.pdf",
       "doc_source": "paper-transformers-2023"
     }'
```

#### ❤️ **Health Check**
```bash
curl "http://localhost:8001/api/v1/health"
```

## 🔧 Endpoints Disponíveis

### **Pesquisa** (`/api/v1/research`)
- `POST /` - Realizar pesquisa
- `GET /status` - Status do sistema de pesquisa

### **Indexação** (`/api/v1/index`)
- `POST /` - Indexar documento PDF
- `POST /validate-url` - Validar URL
- `GET /status` - Status do indexer

### **Gerenciamento** (`/api/v1`)
- `GET /health` - Health check básico
- `GET /health/detailed` - Health check detalhado
- `GET /stats` - Estatísticas do sistema
- `GET /version` - Versão da API
- `GET /config` - Configuração atual
- `DELETE /documents/{collection}` - Deletar documentos

## 🛡️ Recursos de Segurança

### **Rate Limiting**
- **Limite**: 100 requisições por minuto por cliente
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`
- **Endpoints protegidos**: Todos exceto `/health`, `/docs`, `/redoc`

### **Headers de Segurança**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy` (em produção)

### **CORS**
- Configurável via `ENABLE_CORS=true`
- Origins específicas via `CORS_ORIGINS`

## 📊 Monitoramento

### **Métricas Disponíveis**
- Total de requisições
- Taxa de sucesso/falha
- Tempo médio de resposta
- Uptime do sistema

### **Logging Estruturado**
- Request ID único para rastreamento
- Logs detalhados com contexto
- Diferentes níveis (DEBUG, INFO, WARNING, ERROR)

### **Health Checks**
- **Básico**: Status geral e componentes
- **Detalhado**: Configurações e diagnósticos

## ⚙️ Configurações Avançadas

### **Modo de Produção**
```bash
PRODUCTION_MODE=true
ENABLE_METRICS=true
ENABLE_RATE_LIMITING=true
API_LOG_LEVEL=INFO
```

### **Performance**
```bash
API_WORKERS=4               # Número de workers
MAX_REQUEST_SIZE=16777216   # 16MB max request
REQUEST_TIMEOUT=300         # 5 minutos timeout
```

### **Desenvolvimento**
```bash
API_RELOAD=true
API_LOG_LEVEL=DEBUG
# API_BEARER_TOKEN=  # Desabilitado para dev
```

## 🔄 Melhorias da v2.0.0

### **Arquitetura**
- ✅ **Estrutura modular** com separação clara
- ✅ **Pydantic V2** com field_validators modernos
- ✅ **Injeção de dependências** bem estruturada
- ✅ **Error handling** centralizado e robusto

### **Funcionalidades**
- ✅ **Middlewares customizados** para logging e segurança
- ✅ **Rate limiting** inteligente por cliente
- ✅ **Health checks** detalhados
- ✅ **Métricas** de performance em tempo real

### **Qualidade**
- ✅ **Typing** completo com Python 3.12+
- ✅ **Documentação** interativa melhorada
- ✅ **Logs estruturados** com request tracing
- ✅ **Configuração** centralizada e validada

## 🐛 Troubleshooting

### **Problema: API não inicia**
```bash
# Verificar configuração
python -c "from api.core.config import config; print(config.validate_all())"

# Verificar dependências
pip install -r requirements.txt
```

### **Problema: Autenticação falha**
```bash
# Verificar token
echo $API_BEARER_TOKEN

# Para desenvolvimento, desabilitar:
# API_BEARER_TOKEN=
```

### **Problema: Rate limiting**
```bash
# Headers de resposta mostram limites
curl -I "http://localhost:8001/api/v1/health"
```

## 📝 TODO

- [ ] **Docker** containerização
- [ ] **Tests** unitários e integração
- [ ] **CI/CD** pipeline
- [ ] **Prometheus** metrics
- [ ] **Grafana** dashboards
- [ ] **OpenTelemetry** tracing

## 🤝 Contribuição

1. Seguir a estrutura modular existente
2. Usar Pydantic V2 field_validators
3. Adicionar testes para novas funcionalidades
4. Manter documentação atualizada
5. Seguir padrões de logging existentes

---

**Versão**: 2.0.0 | **Data**: 2025-06-19 | **Python**: 3.12+ | **Framework**: FastAPI
