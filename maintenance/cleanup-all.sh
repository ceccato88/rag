#!/bin/bash

# Script para limpeza completa do sistema
# ⚠️ CUIDADO: Remove TODOS os dados!

set -e

echo "🛠️ Script de Limpeza Completa do Sistema RAG"
echo "============================================="
echo ""
echo "⚠️  AVISO: Este script vai remover:"
echo "   • Todos os documentos do AstraDB"
echo "   • Todas as imagens extraídas"
echo "   • Logs do sistema"
echo "   • Cache temporário"
echo ""

# Verificar se estamos no diretório correto
if [[ ! -f "../config.py" ]]; then
    echo "❌ Execute este script da pasta maintenance/"
    exit 1
fi

# Solicitar confirmação
read -p "Tem certeza que deseja continuar? Digite 'CONFIRMO' para prosseguir: " confirm

if [[ "$confirm" != "CONFIRMO" ]]; then
    echo "❌ Operação cancelada."
    exit 1
fi

echo ""
echo "🧹 Iniciando limpeza completa..."

# 1. Limpar collection AstraDB
echo "📊 1. Limpando collection AstraDB..."
python delete_collection.py --collection pdf_documents --confirm || echo "⚠️ Erro ao limpar collection"

# 2. Limpar imagens
echo "🖼️ 2. Limpando imagens extraídas..."
python delete_images.py --directory ../pdf_images --confirm || echo "⚠️ Erro ao limpar imagens"

# 3. Limpar logs
echo "📝 3. Limpando logs..."
rm -rf ../logs/*.log || echo "⚠️ Nenhum log para limpar"

# 4. Limpar cache temporário
echo "💾 4. Limpando cache temporário..."
rm -rf ../temp/* || echo "⚠️ Nenhum cache para limpar"

# 5. Limpar containers Docker (opcional)
echo "🐳 5. Limpando dados do Docker..."
if command -v docker >/dev/null 2>&1; then
    docker-compose down 2>/dev/null || true
    docker system prune -f 2>/dev/null || echo "⚠️ Erro ao limpar Docker"
fi

echo ""
echo "✅ Limpeza completa finalizada!"
echo "📋 Próximos passos:"
echo "   1. Reinicie o sistema: ../production-start.sh"
echo "   2. Reindexe documentos se necessário"
echo "   3. Verifique logs para confirmar funcionamento"