#!/bin/bash

# Script de Verificação de Segurança para Produção
# Sistema RAG Multi-Agente

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔒 Verificação de Segurança - Sistema RAG Multi-Agente${NC}"
echo "=================================================="

# Contadores
PASSED=0
FAILED=0
WARNINGS=0

# Função para check
check() {
    local test_name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "🔍 $test_name... "
    
    if eval "$command" > /dev/null 2>&1; then
        if [[ "$expected" == "fail" ]]; then
            echo -e "${RED}FALHOU${NC}"
            ((FAILED++))
        else
            echo -e "${GREEN}OK${NC}"
            ((PASSED++))
        fi
    else
        if [[ "$expected" == "fail" ]]; then
            echo -e "${GREEN}OK${NC}"
            ((PASSED++))
        else
            echo -e "${RED}FALHOU${NC}"
            ((FAILED++))
        fi
    fi
}

# Função para warning
warning() {
    local message="$1"
    echo -e "${YELLOW}⚠️ AVISO: $message${NC}"
    ((WARNINGS++))
}

echo -e "${BLUE}1. Verificações de Configuração${NC}"
echo "--------------------------------"

# Verificar se estamos em produção
if [[ "${ENVIRONMENT:-}" == "production" ]]; then
    echo -e "✅ Ambiente: ${GREEN}PRODUCTION${NC}"
else
    warning "Ambiente não está configurado como 'production'"
fi

# Verificar variáveis críticas
echo -n "🔍 API Bearer Token configurado... "
if [[ -n "$API_BEARER_TOKEN" && ${#API_BEARER_TOKEN} -ge 32 ]]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}FALHOU${NC} (token muito curto ou ausente)"
    ((FAILED++))
fi

# Verificar debug desabilitado
echo -n "🔍 Debug mode desabilitado... "
if [[ "${DEBUG:-}" == "false" ]]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}FALHOU${NC} (DEBUG deve ser false)"
    ((FAILED++))
fi

# Verificar CORS
echo -n "🔍 CORS restritivo... "
if [[ "${ENABLE_CORS:-}" == "false" ]]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    warning "CORS está habilitado - verifique se é necessário"
fi

echo ""
echo -e "${BLUE}2. Verificações de Rede${NC}"
echo "------------------------"

# Testar autenticação inválida
echo -n "🔍 Autenticação rejeitando tokens inválidos... "
if curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid-token" http://localhost:8000/health | grep -q "401"; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}FALHOU${NC} (não rejeitou token inválido)"
    ((FAILED++))
fi

# Testar sem autenticação
echo -n "🔍 Endpoints protegidos requerem auth... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/search | grep -q "401\|403"; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}FALHOU${NC} (endpoint não protegido)"
    ((FAILED++))
fi

# Verificar headers de segurança
echo -n "🔍 Headers de segurança presentes... "
if curl -s -I http://localhost/health | grep -q "X-Frame-Options\|X-Content-Type-Options"; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    warning "Headers de segurança não encontrados (configure no Nginx)"
fi

echo ""
echo -e "${BLUE}3. Verificações de Container${NC}"
echo "-------------------------------"

# Verificar se containers estão rodando como não-root
echo -n "🔍 Containers rodando como não-root... "
if docker-compose exec -T api-simple whoami | grep -q "appuser"; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}FALHOU${NC} (container rodando como root)"
    ((FAILED++))
fi

# Verificar resource limits
echo -n "🔍 Resource limits configurados... "
if docker-compose config | grep -q "limits"; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    warning "Resource limits não configurados"
fi

echo ""
echo -e "${BLUE}4. Verificações de Logs${NC}"
echo "-------------------------"

# Verificar se logs não contêm secrets
echo -n "🔍 Logs não contêm secrets... "
if ! grep -r "sk-" logs/ 2>/dev/null | grep -v "MASKED"; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}FALHOU${NC} (possível vazamento de API key nos logs)"
    ((FAILED++))
fi

# Verificar permissões de diretórios
echo -n "🔍 Permissões de diretórios seguras... "
if [[ $(stat -c %a logs/) == "755" || $(stat -c %a logs/) == "750" ]]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    warning "Permissões do diretório de logs podem estar muito abertas"
fi

echo ""
echo "=================================================="
echo -e "${BLUE}📊 Resumo da Verificação de Segurança${NC}"
echo "=================================================="
echo -e "✅ Testes Passou: ${GREEN}$PASSED${NC}"
echo -e "❌ Testes Falhou: ${RED}$FAILED${NC}"
echo -e "⚠️ Avisos: ${YELLOW}$WARNINGS${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 Sistema passou em todas as verificações críticas de segurança!${NC}"
    exit 0
else
    echo -e "${RED}🚨 Sistema falhou em $FAILED verificações críticas!${NC}"
    echo -e "${YELLOW}Por favor, corrija os problemas antes de ir para produção.${NC}"
    exit 1
fi