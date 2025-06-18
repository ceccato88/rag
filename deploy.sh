#!/bin/bash

# Script de Deploy para Produção
# Sistema RAG Multi-Agente

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}🚀 Iniciando deploy para produção...${NC}"

# Função para log
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Verificar se estamos em produção
if [[ "${ENVIRONMENT:-}" != "production" ]]; then
    error "Este script deve ser executado apenas em ambiente de produção!"
fi

# Verificar dependências
command -v docker >/dev/null 2>&1 || error "Docker não está instalado"
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose não está instalado"

# Verificar arquivos essenciais
[[ -f "$DOCKER_COMPOSE_FILE" ]] || error "Arquivo $DOCKER_COMPOSE_FILE não encontrado"
[[ -f "$ENV_FILE" ]] || error "Arquivo $ENV_FILE não encontrado"

# Verificar variáveis de ambiente críticas
log "Verificando configuração..."
if ! grep -q "API_BEARER_TOKEN=" "$ENV_FILE"; then
    error "API_BEARER_TOKEN não configurado no $ENV_FILE"
fi

if ! grep -q "OPENAI_API_KEY=" "$ENV_FILE"; then
    error "OPENAI_API_KEY não configurado no $ENV_FILE"
fi

if ! grep -q "VOYAGE_API_KEY=" "$ENV_FILE"; then
    error "VOYAGE_API_KEY não configurado no $ENV_FILE"
fi

# Criar backup
log "Criando backup..."
mkdir -p "$BACKUP_DIR"
if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli BGSAVE || warning "Backup do Redis falhou"
fi

# Parar serviços existentes
log "Parando serviços existentes..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down || warning "Alguns serviços já estavam parados"

# Limpar imagens antigas
log "Limpando imagens antigas..."
docker system prune -f

# Build das novas imagens
log "Construindo imagens..."
docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache

# Iniciar serviços
log "Iniciando serviços..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

# Aguardar health checks
log "Aguardando health checks..."
sleep 30

# Verificar status dos serviços
log "Verificando status dos serviços..."

# Verificar API Simple
if curl -f -s "http://localhost:8000/health" > /dev/null; then
    log "✅ API Simple está funcionando"
else
    error "❌ API Simple não está respondendo"
fi

# Verificar API Multi-Agent
if curl -f -s "http://localhost:8001/health" > /dev/null; then
    log "✅ API Multi-Agent está funcionando"
else
    error "❌ API Multi-Agent não está respondendo"
fi

# Verificar Redis
if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
    log "✅ Redis está funcionando"
else
    warning "⚠️ Redis não está respondendo"
fi

# Mostrar status final
log "Status final dos serviços:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Logs recentes
log "Logs recentes:"
docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=10

echo -e "${GREEN}🎉 Deploy concluído com sucesso!${NC}"
echo -e "${BLUE}📊 URLs dos serviços:${NC}"
echo -e "  API Simple: http://localhost:8000"
echo -e "  API Multi-Agent: http://localhost:8001"
echo -e "  Health Checks: http://localhost:8000/health | http://localhost:8001/health"
echo -e "${BLUE}📝 Para ver logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f${NC}"