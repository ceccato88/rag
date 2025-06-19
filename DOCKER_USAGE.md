# 🐳 Docker Setup - APIs RAG Refatoradas

## 📋 Visão Geral

Sistema containerizado com duas APIs refatoradas:
- **API Multi-Agente** (port 8000): Sistema avançado com reasoning multi-agente
- **API RAG Simples** (port 8001): Sistema de busca RAG direta

## 🚀 Comandos Rápidos

### Executar apenas as APIs
```bash
docker-compose up --build
```

### Executar com cache Redis
```bash
docker-compose --profile cache up --build
```

### Executar com load balancer
```bash
docker-compose --profile loadbalancer up --build
```

### Executar com monitoramento completo
```bash
docker-compose --profile monitoring up --build
```

### Executar tudo (APIs + Cache + Load Balancer + Monitoramento)
```bash
docker-compose --profile cache --profile loadbalancer --profile monitoring up --build
```

## 🔧 Configuração Individual

### Apenas API Multi-Agente
```bash
docker-compose up api-multiagent --build
```

### Apenas API RAG Simples
```bash
docker-compose up api-simple --build
```

## 🌐 Endpoints

### Acesso Direto
- **API Multi-Agente**: http://localhost:8000
  - Health: http://localhost:8000/health
  - Research: POST http://localhost:8000/research
  - Docs: http://localhost:8000/docs

- **API RAG Simples**: http://localhost:8001
  - Health: http://localhost:8001/health
  - Search: POST http://localhost:8001/search
  - Docs: http://localhost:8001/docs

### Acesso via Load Balancer (com profile loadbalancer)
- **Multi-Agent**: http://multiagent.localhost
- **Simple**: http://simple.localhost
- **Health**: http://localhost/health

### Monitoramento (com profile monitoring)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

## 📊 Recursos e Limites

### API Multi-Agente
- **CPU**: 3.0 cores (reservado: 0.5)
- **Memory**: 3GB (reservado: 1GB)
- **Workers**: 4

### API RAG Simples  
- **CPU**: 1.5 cores (reservado: 0.3)
- **Memory**: 1.5GB (reservado: 512MB)
- **Workers**: 2

## 🔍 Logs e Debugging

### Ver logs em tempo real
```bash
# Todos os serviços
docker-compose logs -f

# Apenas API Multi-Agente
docker-compose logs -f api-multiagent

# Apenas API RAG Simples
docker-compose logs -f api-simple
```

### Acessar container
```bash
# API Multi-Agente
docker-compose exec api-multiagent bash

# API RAG Simples
docker-compose exec api-simple bash
```

## 🛑 Comandos de Parada

### Parar serviços
```bash
docker-compose down
```

### Parar e remover volumes
```bash
docker-compose down -v
```

### Limpar tudo (imagens, containers, volumes)
```bash
docker-compose down -v --rmi all
```

## 🔄 Rebuild e Update

### Rebuild apenas uma API
```bash
docker-compose build api-multiagent
docker-compose up api-multiagent
```

### Rebuild tudo
```bash
docker-compose build --no-cache
docker-compose up
```

## 📝 Variáveis de Ambiente

As seguintes variáveis são configuradas automaticamente:

### APIs
- `API_HOST=0.0.0.0`
- `API_PORT=8000/8001`
- `API_LOG_LEVEL=info`
- `API_WORKERS=2/4`
- `ENVIRONMENT=production`

### Sistema
Todas as variáveis do `.env` são carregadas automaticamente.

## 🔐 Segurança

- Containers rodam com usuário não-root
- Rate limiting configurado no nginx
- Headers de segurança aplicados
- Logs estruturados com rotação automática

## 🎯 Profiles Disponíveis

| Profile | Serviços | Uso |
|---------|----------|-----|
| default | api-simple, api-multiagent | Desenvolvimento básico |
| cache | + redis | Desenvolvimento com cache |
| loadbalancer | + nginx | Produção com balanceamento |
| monitoring | + prometheus, grafana | Produção com métricas |

## ⚡ Exemplos de Teste

### Testar API Multi-Agente
```bash
curl -X POST "http://localhost:8000/research" \
  -H "Authorization: Bearer $API_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "explique machine learning", "objective": "educacional"}'
```

### Testar API RAG Simples
```bash
curl -X POST "http://localhost:8001/search" \
  -H "Authorization: Bearer $API_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "conceitos de AI", "max_results": 5}'
```

## 🆘 Troubleshooting

### Problemas Comuns

1. **APIs não iniciam**: Verificar variáveis do `.env`
2. **Erro de memória**: Reduzir workers ou limites de memory
3. **Nginx não conecta**: Verificar se APIs estão rodando primeiro
4. **Permissões de log**: Criar diretório `logs/` com permissões corretas

### Verificação de Health
```bash
# Status de todos os serviços
docker-compose ps

# Health check específico
curl http://localhost:8000/health
curl http://localhost:8001/health
```