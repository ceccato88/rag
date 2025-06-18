#!/bin/bash

# Script para testar todos os endpoints das APIs com autenticação
TOKEN="rag-prod-2024-secure-api-token-b8f9c3d7e2a1"
BASE_URL="http://localhost:8000"

echo "🧪 TESTE COMPLETO DAS APIs - SISTEMA RAG"
echo "=================================================="

echo ""
echo "📋 1. ENDPOINTS PÚBLICOS (sem autenticação):"
echo "----------------------------------------------"

echo "GET / (raiz)"
curl -s $BASE_URL/ | jq .

echo -e "\nGET /health (health check)"
curl -s $BASE_URL/health | jq .

echo ""
echo "🔒 2. ENDPOINTS PROTEGIDOS (com autenticação):"
echo "----------------------------------------------"

echo "GET /config (sem token - deve falhar)"
curl -s $BASE_URL/config

echo -e "\n\nGET /config (com token - deve funcionar)"
curl -s -H "Authorization: Bearer $TOKEN" $BASE_URL/config | jq .

echo -e "\nGET /metrics (com token)"
curl -s -H "Authorization: Bearer $TOKEN" $BASE_URL/metrics | jq .

echo ""
echo "🚨 3. TESTE DE ENDPOINT INVÁLIDO:"
echo "----------------------------------------------"

echo "GET /invalid (deve retornar 404)"
curl -s $BASE_URL/invalid

echo ""
echo ""
echo "✅ TESTE CONCLUÍDO!"
echo "=================================================="