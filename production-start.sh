#!/bin/bash

# Script de Inicialização para Produção
# Sistema RAG Multi-Agente

set -e

echo "🚀 Iniciando Sistema RAG Multi-Agente - Produção"

# Verificar se estamos em produção
if [[ "${ENVIRONMENT:-}" != "production" ]]; then
    echo "⚠️ AVISO: Configurando ambiente para produção..."
    export ENVIRONMENT=production
fi

# Configurações de produção
export API_WORKERS=4
export API_LOG_LEVEL=info
export API_RELOAD=false
export DEBUG=false

# Verificar dependências críticas
echo "🔍 Verificando configuração..."

# Verificar variáveis de ambiente obrigatórias
required_vars=(
    "OPENAI_API_KEY"
    "VOYAGE_API_KEY"
    "ASTRA_DB_API_ENDPOINT"
    "ASTRA_DB_APPLICATION_TOKEN"
    "API_BEARER_TOKEN"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Variável $var não configurada!"
        exit 1
    fi
done

echo "✅ Todas as variáveis obrigatórias configuradas"

# Criar diretórios necessários
mkdir -p logs temp

# Iniciar usando Docker Compose
echo "🐳 Iniciando com Docker Compose..."
docker-compose up -d

echo "⏳ Aguardando serviços inicializarem..."
sleep 15

# Health checks
echo "🔍 Verificando saúde dos serviços..."

# API Simple
if curl -f -s "http://localhost:8000/health" > /dev/null; then
    echo "✅ API Simple: OK"
else
    echo "❌ API Simple: FALHA"
fi

# API Multi-Agent
if curl -f -s "http://localhost:8001/health" > /dev/null; then
    echo "✅ API Multi-Agent: OK"
else
    echo "❌ API Multi-Agent: FALHA"
fi

echo ""
echo "🎉 Sistema iniciado!"
echo "📊 APIs disponíveis:"
echo "  - API Simple: http://localhost:8000"
echo "  - API Multi-Agent: http://localhost:8001"
echo ""
echo "📝 Para ver logs:"
echo "  docker-compose logs -f"
echo ""
echo "🛑 Para parar:"
echo "  docker-compose down"