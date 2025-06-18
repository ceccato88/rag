#!/bin/bash

# Script para Parar Sistema em Produção
# Sistema RAG Multi-Agente

set -e

echo "🛑 Parando Sistema RAG Multi-Agente - Produção"

# Backup do Redis antes de parar
if docker-compose ps redis | grep -q "Up"; then
    echo "💾 Criando backup do Redis..."
    docker-compose exec -T redis redis-cli BGSAVE || echo "⚠️ Backup do Redis falhou"
fi

# Parar todos os serviços
echo "🔽 Parando serviços..."
docker-compose down

# Verificar se todos pararam
echo "🔍 Verificando se serviços pararam..."
if docker-compose ps | grep -q "Up"; then
    echo "⚠️ Alguns serviços ainda estão rodando"
    docker-compose ps
else
    echo "✅ Todos os serviços foram parados"
fi

echo "✅ Sistema parado com sucesso!"