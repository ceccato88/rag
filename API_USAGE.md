# 🚀 API Reference & Usage Guide

**Sistema RAG Multi-Agente - Documentação das APIs**

> ⚠️ **Pré-requisito**: Sistema já instalado e configurado. Se ainda não configurou, veja [QUICKSTART.md](QUICKSTART.md) ou [SETUP_FINAL.md](SETUP_FINAL.md).

## 📋 APIs Disponíveis

| API | Porta | Uso | Performance |
|-----|-------|-----|-------------|
| **Simple RAG** | 8000 | Busca direta, respostas rápidas | < 500ms |
| **Multi-Agent** | 8001 | Pesquisa complexa, reasoning avançado | < 2s |

## 🔗 URLs Base

```bash
# Desenvolvimento
API_SIMPLE="http://localhost:8000"
API_MULTIAGENT="http://localhost:8001"

# Produção (com nginx)
API_SIMPLE="http://localhost/api/simple"
API_MULTIAGENT="http://localhost/api/multiagent"
```

## ⚡ Quick Test

```bash
# Verificar se APIs estão funcionando
curl http://localhost:8000/health
curl http://localhost:8001/health

# Teste básico
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Como configurar Docker?"}'
```

---

## 🎯 API Simple RAG (Porta 8000)

**Quando usar**: Consultas diretas, busca rápida, casos simples

### 🔍 **POST /search** - Busca Semântica

**Request:**

# Produção (com nginx)
API_SIMPLE="http://localhost/api/simple"
API_MULTIAGENT="http://localhost/api/multiagent"
```

## ⚡ Quick Test

```bash
# Verificar se APIs estão funcionando
curl http://localhost:8000/health
curl http://localhost:8001/health

# Teste básico
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Como configurar Docker?"}'
```