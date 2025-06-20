# 🤖 RAG Multi-Agent Research System

Sistema avançado de pesquisa baseado em RAG (Retrieval-Augmented Generation) com coordenação multi-agente e reasoning inteligente.

## ⚡ Características Principais

- **🧠 Coordenação Multi-Agente**: Sistema hierárquico com coordenador (gpt-4.1) e subagentes especializados (gpt-4.1-mini)
- **🔍 7 Focus Areas**: Especialização automática em conceptual, technical, comparative, examples, overview, applications, general
- **⚡ Execução Paralela**: Subagentes executam simultaneamente para máxima performance
- **🎯 ReAct Reasoning**: Raciocínio estruturado do planejamento à síntese final
- **📊 RAG Multimodal**: Suporte a texto + imagens com embeddings Voyage
- **🗄️ AstraDB**: Banco vetorial distribuído para escalabilidade
- **🔒 Segurança**: Rate limiting, autenticação Bearer, validação SSRF/XSS

## 🚀 Quick Start

### 1. Configuração do Ambiente

```bash
# Clone o repositório
git clone <repository-url>
cd rag

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas API keys
```

### 2. Variáveis de Ambiente Obrigatórias

```env
# APIs
OPENAI_API_KEY=your_openai_key
VOYAGE_API_KEY=your_voyage_key
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
ASTRA_DB_APPLICATION_TOKEN=your_astra_token

# Modelos
OPENAI_MODEL=gpt-4.1-mini          # Subagentes
COORDINATOR_MODEL=gpt-4.1          # Coordenador
EMBEDDING_MODEL=voyage-multimodal-3

# Sistema Multi-Agente
MAX_CANDIDATES=5
MAX_SUBAGENTS=3
PARALLEL_EXECUTION=true
```

### 3. Executar API

```bash
# Desenvolvimento
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Produção
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Indexar Documentos

```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/index" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pdf_url": "https://arxiv.org/pdf/2501.13956"}'

# Via script
python scripts/indexer.py --url "https://arxiv.org/pdf/2501.13956"
```

## 📖 Uso da API

### Research Multi-Agente

```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como Zep implementa temporal knowledge graphs para memória de agentes AI?",
    "use_multiagent": true
  }'
```

### Busca Simples

```bash
curl -X POST "http://localhost:8000/api/v1/simple" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "O que é Zep?"}'
```

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                  🎯 User Query                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│           🧠 Lead Researcher (gpt-4.1)             │
│  • ReAct Reasoning • Query Decomposition           │
│  • Focus Area Selection • Advanced Synthesis       │
└─────────────────┬───────────────────────────────────┘
                  │ (decompose into specialized tasks)
                  ▼
┌─────────────────────────────────────────────────────┐
│              ⚡ Parallel Execution                  │
│                                                     │
│  🔍 Subagent 1    🔍 Subagent 2    🔍 Subagent 3   │
│  (conceptual)     (technical)      (examples)      │
│  gpt-4.1-mini     gpt-4.1-mini     gpt-4.1-mini    │
│       │               │                │           │
│       ▼               ▼                ▼           │
│  📚 RAG Search   📚 RAG Search   📚 RAG Search     │
│  (specialized)   (specialized)   (specialized)     │
└─────┬───────────────┬──────────────┬───────────────┘
      │               │              │
      ▼               ▼              ▼
┌─────────────────────────────────────────────────────┐
│         🧠 Advanced AI Synthesis (gpt-4.1)         │
│  • Cross-reference Analysis • Critical Thinking    │
│  • Insight Generation • Structured Report          │
└─────────────────────────────────────────────────────┘
```

## 🎯 Focus Areas

| Focus Area | Descrição | Quando Usar |
|------------|-----------|-------------|
| **conceptual** | Definições, conceitos, fundamentos | "O que é...", necessidade de entendimento básico |
| **technical** | Implementação, arquitetura, algoritmos | "Como implementar...", especificações técnicas |
| **comparative** | Comparações, diferenças, avaliações | "X vs Y", "qual é melhor..." |
| **examples** | Casos de uso, exemplos práticos | "Exemplos de...", demonstrações |
| **overview** | Visão geral, introdução ampla | Contexto geral, getting started |
| **applications** | Aplicações práticas, uso no mundo real | Uso empresarial, deployment |
| **general** | Pesquisa abrangente sem foco específico | Queries muito gerais |

## 📁 Estrutura do Projeto

```
rag/
├── api/                          # FastAPI application
│   ├── routers/                  # API endpoints
│   ├── core/                     # Core configuration
│   └── utils/                    # Utilities
├── src/core/                     # Core RAG system
│   ├── search.py                 # RAG implementation
│   ├── indexer.py                # Document indexing
│   ├── config.py                 # Configuration
│   └── constants.py              # Constants
├── multi-agent-researcher/       # Multi-agent system
│   └── src/researcher/
│       ├── agents/               # Agent implementations
│       ├── reasoning/            # ReAct reasoning
│       └── tools/                # Agent tools
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
└── data/                         # Data storage
```

## 🔧 Configuração Avançada

### Modelos de IA

```env
# Hierarquia de modelos para otimização de custo/qualidade
OPENAI_MODEL=gpt-4.1-mini          # Subagentes (eficiência)
COORDINATOR_MODEL=gpt-4.1          # Coordenador (qualidade)
EMBEDDING_MODEL=voyage-multimodal-3 # Embeddings multimodais
```

### Performance

```env
# Configurações de performance
MAX_SUBAGENTS=3                    # Máximo 3 subagentes paralelos
PARALLEL_EXECUTION=true            # Execução paralela
SUBAGENT_TIMEOUT=300.0            # Timeout por subagente (5min)
MAX_CANDIDATES=5                   # Documentos por busca
```

### Segurança

```env
# Configurações de segurança
PRODUCTION_MODE=true
ENABLE_RATE_LIMITING=true
API_BEARER_TOKEN=your_secure_token
CORS_ORIGINS=https://yourdomain.com
```

## 📊 Monitoramento

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Métricas

```bash
curl http://localhost:8000/api/v1/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Testes

```bash
# Testes unitários
pytest tests/

# Teste da API
python scripts/test_api.py

# Teste completo do pipeline
python scripts/test_full_pipeline.py
```

## 📚 Documentação

- [📖 Guia Completo](docs/README.md)
- [🏗️ Arquitetura](docs/architecture.md)
- [🤖 Sistema Multi-Agente](docs/multi-agent.md)
- [🔍 ReAct Reasoning](docs/reasoning.md)
- [⚙️ Configuração](docs/configuration.md)
- [🚀 Deployment](docs/deployment.md)
- [🔧 Troubleshooting](docs/troubleshooting.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para a branch (`git push origin feature/amazing-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja `LICENSE` para mais detalhes.

## 🆘 Suporte

- 📧 Email: support@yourcompany.com
- 💬 Discord: [Link do servidor]
- 🐛 Issues: [GitHub Issues](https://github.com/yourorg/rag/issues)

---

**🚀 Built with ❤️ using FastAPI, OpenAI, Voyage AI, and AstraDB**