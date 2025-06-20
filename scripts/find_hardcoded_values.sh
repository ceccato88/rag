#!/bin/bash
# Script para encontrar valores hardcoded no código
# Uso: ./scripts/find_hardcoded_values.sh

echo "🔍 Buscando valores hardcoded no sistema RAG..."
echo "=============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para buscar padrões
search_pattern() {
    local pattern="$1"
    local description="$2"
    local exclude_pattern="$3"
    local results
    
    echo -e "\n${YELLOW}🔍 Buscando: $description${NC}"
    echo "Padrão: $pattern"
    echo "----------------------------------------"
    
    # Buscar em arquivos Python, excluindo cache e venv
    if [ -n "$exclude_pattern" ]; then
        results=$(find . -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.venv/*" -exec grep -l "$pattern" {} \; | xargs grep -n "$pattern" 2>/dev/null | grep -v "$exclude_pattern")
    else
        results=$(find . -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.venv/*" -exec grep -l "$pattern" {} \; | xargs grep -n "$pattern" 2>/dev/null)
    fi
    
    if [ -n "$results" ]; then
        echo -e "${RED}❌ Encontrados:${NC}"
        # Numerar as linhas para melhor organização
        echo "$results" | nl -w2 -s'. '
        echo -e "${RED}📊 Total: $(echo "$results" | wc -l) ocorrências${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Nenhum encontrado${NC}"
        return 0
    fi
}

# Contador de problemas
issues=0

# 1. Temperatura hardcoded (incluindo 0.0) - excluir config files
if ! search_pattern "temperature.*=.*[0-9]" "Temperatura hardcoded" "Field\(default=\|PROCESSING_CONFIG\|verify_config_consistency"; then
    ((issues++))
fi

# 2. Max tokens hardcoded - excluir config files
if ! search_pattern "max_tokens.*=.*[0-9]" "Max tokens hardcoded" "Field\(default=\|TOKEN_LIMITS\|exemplo/"; then
    ((issues++))
fi

# 3. Modelos hardcoded - apenas valores literais
if ! search_pattern "model.*=.*[\"']gpt-" "Modelos GPT hardcoded" "config\.rag\.|system_config\.rag\."; then
    ((issues++))
fi

# 4. Modelos de embedding hardcoded - apenas valores literais
if ! search_pattern "model.*=.*[\"']voyage-" "Modelos Voyage hardcoded" "config\.rag\.|system_config\.rag\."; then
    ((issues++))
fi

# 5. Uso direto de os.getenv - excluir arquivos de configuração e funções de validação
if ! search_pattern "os\.getenv" "Uso direto de os.getenv()" "src/core/config\.py\|api/core/config\.py\|constants\.py\|check_env_var\|exemplo/\|verify_config_consistency\|env_validation\.py"; then
    ((issues++))
fi

# 6. URLs hardcoded
if ! search_pattern "https://[a-zA-Z0-9.-]+\.(com|org|net)" "URLs hardcoded"; then
    ((issues++))
fi

# 7. Timeouts hardcoded
if ! search_pattern "timeout\s*=\s*\d+" "Timeouts hardcoded"; then
    ((issues++))
fi

# 8. Portas hardcoded
if ! search_pattern "port\s*=\s*\d+" "Portas hardcoded"; then
    ((issues++))
fi

# 9. Chaves API hardcoded (perigoso!)
if ! search_pattern "[\"']sk-[a-zA-Z0-9-]+[\"']|[\"']pa-[a-zA-Z0-9-]+[\"']" "Possíveis chaves API hardcoded"; then
    ((issues++))
fi

# 10. Magic numbers comuns
if ! search_pattern "\b(1000|2000|3000|4000|5000)\b(?!.*#.*magic|.*constant)" "Magic numbers suspeitos"; then
    ((issues++))
fi

# Resultado final
echo ""
echo "=============================================="
if [ $issues -eq 0 ]; then
    echo -e "${GREEN}✅ SUCESSO: Nenhum valor hardcoded encontrado!${NC}"
    echo "   O código está seguindo as boas práticas."
else
    echo -e "${RED}❌ PROBLEMAS ENCONTRADOS: $issues categorias${NC}"
    echo "   Consulte BOAS_PRATICAS_CONFIGURACAO.md para correções."
fi
echo "=============================================="

# Comandos úteis extras
echo ""
echo "💡 Comandos úteis para investigação:"
echo "   • Buscar variável específica: rg -n 'NOME_VARIAVEL' --type py"
echo "   • Ver configuração atual: python -c 'from src.core.config import SystemConfig; SystemConfig().print_config()'"
echo "   • Verificar consistência: python scripts/verify_config_consistency.py"

exit $issues