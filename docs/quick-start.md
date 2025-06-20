# ⚡ Quick Start Guide

Tenha o sistema RAG Multi-Agente funcionando em **5 minutos**!

## 🎯 Pré-requisitos

- Python 3.11+
- Git
- Conta OpenAI (para GPT-4.1 e GPT-4.1-mini)
- Conta Voyage AI (para embeddings)
- Conta AstraDB (para vector storage)

## 🚀 Instalação Rápida

### 1. Clone e Setup
```bash
# Clone o repositório
git clone <repository-url>
cd rag

# Instale dependências
pip install -r requirements.txt
```

### 2. Configure Variáveis de Ambiente
```bash
# Copie o template
cp .env.example .env

# Edite com suas credenciais
nano .env
```

**Variáveis obrigatórias**:
```env
# APIs (OBRIGATÓRIO)
OPENAI_API_KEY=sk-proj-your_openai_key_here
VOYAGE_API_KEY=pa-your_voyage_key_here
ASTRA_DB_API_ENDPOINT=https://your-db-id.apps.astra.datastax.com
ASTRA_DB_APPLICATION_TOKEN=AstraCS:your_token_here

# Modelos (Configuração hierárquica)
OPENAI_MODEL=gpt-4.1-mini          # Subagentes (eficiência)
COORDINATOR_MODEL=gpt-4.1          # Coordenador (qualidade crítica)
EMBEDDING_MODEL=voyage-multimodal-3

# Segurança
API_BEARER_TOKEN=your_secure_token_here
```

### 3. Inicie a API
```bash
# Desenvolvimento (com reload)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Produção
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Verifique Health
```bash
curl http://localhost:8000/api/v1/health
```

**Resposta esperada**:
```json
{
  "status": "healthy",
  "components": {
    "memory": true,
    "simple_rag": true,
    "lead_researcher": true
  }
}
```

## 📚 Indexe Seu Primeiro Documento

### Via API
```bash
curl -X POST "http://localhost:8000/api/v1/index" \
  -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://arxiv.org/pdf/2501.13956",
    "collection_name": "pdf_documents"
  }'
```

### Via Script (Alternativo)
```bash
# Indexar PDF do Zep (exemplo)
python scripts/indexer.py --url "https://arxiv.org/pdf/2501.13956"
```

**Aguarde**: ~2-3 minutos para indexação completa com imagens.

## 🤖 Sua Primeira Pesquisa Multi-Agente

### Research Multi-Agente (Recomendado)
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "O que é Zep e como funciona sua arquitetura de temporal knowledge graphs?",
    "use_multiagent": true
  }'
```

### Busca Simples (Fallback)
```bash
curl -X POST "http://localhost:8000/api/v1/simple" \
  -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "O que é Zep?"}'
```

## 🎯 Entendendo a Resposta

### Estrutura da Resposta Multi-Agente
```json
{
  "success": true,
  "query": "O que é Zep e como funciona...",
  "result": "# 🤖 AI-Coordinated Research Synthesis\n\n**Coordinator Model**: gpt-4.1\n**Synthesis Method**: Advanced AI Critical Analysis\n**Subagents Processed**: 3/3\n...",
  "agent_id": "abc-123-def",
  "status": "COMPLETED",
  "processing_time": 12.5,
  "confidence_score": null
}
```

### Headers da Síntese
- **Coordinator Model**: `gpt-4.1` (confirma uso do modelo avançado)
- **Synthesis Method**: `Advanced AI Critical Analysis`
- **Subagents Processed**: `3/3` (todos subagentes executaram)

## 🔧 Bearer Token

### Encontrar Seu Token
```bash
# No arquivo .env
grep API_BEARER_TOKEN .env
```

### Gerar Novo Token
```bash
# Gerar token seguro
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Adicionar ao .env
echo "API_BEARER_TOKEN=your_new_token_here" >> .env
```

## 🎓 Exemplos de Queries

### 1. Query Conceitual
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "O que são temporal knowledge graphs?", "use_multiagent": true}'
```
**Focus areas selecionadas**: `conceptual`, `overview`, `examples`

### 2. Query Técnica
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Como implementar Zep em uma aplicação Python?", "use_multiagent": true}'
```
**Focus areas selecionadas**: `technical`, `examples`, `applications`

### 3. Query Comparativa
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Zep vs MemGPT: qual é melhor para chatbots?", "use_multiagent": true}'
```
**Focus areas selecionadas**: `comparative`, `applications`, `technical`

## 📊 Monitoramento Básico

### Status da API
```bash
curl http://localhost:8000/api/v1/health | jq
```

### Métricas (com autenticação)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/stats | jq
```

### Logs em Tempo Real
```bash
# Durante desenvolvimento
tail -f logs/rag_production_debug.log

# Ou diretamente da API
python -m uvicorn api.main:app --log-level debug
```

## 🚨 Troubleshooting Rápido

### Problema: "Credenciais inválidas"
```bash
# Verificar token
echo $API_BEARER_TOKEN

# ou no .env
grep API_BEARER_TOKEN .env
```

### Problema: "No results found"
```bash
# Verificar se documentos foram indexados
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/documents/pdf_documents" | jq
```

### Problema: API não responde
```bash
# Verificar se está rodando
ps aux | grep uvicorn

# Verificar porta
netstat -tlnp | grep :8000

# Reiniciar se necessário
pkill -f uvicorn
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Problema: Erros de model/API
```bash
# Verificar variáveis de ambiente
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('OPENAI_API_KEY:', 'OK' if os.getenv('OPENAI_API_KEY') else 'MISSING')
print('COORDINATOR_MODEL:', os.getenv('COORDINATOR_MODEL', 'NOT SET'))
"
```

## 🎯 Próximos Passos

### 1. **Explore Focus Areas**
- Teste diferentes tipos de queries para ver como o sistema seleciona focus areas automaticamente
- Leia: [🎯 Focus Areas Guide](tutorials/focus-areas.md)

### 2. **Configure para Produção**
- Setup de workers, rate limiting, monitoramento
- Leia: [🚀 Deployment Guide](deployment.md)

### 3. **Customize Agentes**  
- Crie agentes especializados para seu domínio
- Leia: [🤖 Custom Agents](tutorials/custom-agents.md)

### 4. **Integre com Sua Aplicação**
- Use a API REST ou integre diretamente o código
- Leia: [📝 API Guide](api-guide.md)

## 📚 Documentação Completa

- [📖 Documentação Completa](README.md)
- [🏗️ Arquitetura](architecture.md) 
- [🤖 Sistema Multi-Agente](multi-agent.md)
- [🔍 ReAct Reasoning](reasoning.md)
- [⚙️ Configuração Avançada](configuration.md)

---

🎉 **Parabéns!** Você tem um sistema RAG Multi-Agente funcionando com coordenação inteligente e reasoning avançado.

**Próximo passo**: Teste com suas próprias queries e documentos!