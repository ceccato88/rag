# 🤖 RAG Multi-Agent Research System

Sistema avançado de pesquisa baseado em RAG (Retrieval-Augmented Generation) com│  🎯 CONCEPTUAL    ⚖️ COMPARATIVE    🔧 TECHNICAL   │  
│  (gpt-4.1-mini)  (gpt-4.1-mini)   (gpt-4.1-mini)  │
│       │               │                │           │ordenação multi-agente e reasoning inteligente.

## ⚡ Características Principais

- **🧠 Sistema Multi-Agente Enhanced**: Sistema hierárquico com 5 tipos de especialistas (CONCEPTUAL, TECHNICAL, COMPARATIVE, EXAMPLES, GENERAL)
- **🎯 7 Focus Areas**: Especialização automática em conceptual, technical, comparative, examples, overview, applications, general
- **⚡ Execução Paralela**: Subagentes executam simultaneamente para máxima performance
- **🔍 Query Complexity Detection**: Análise automática de complexidade (SIMPLE, MODERATE, COMPLEX, VERY_COMPLEX)
- **📊 RAG Multimodal**: Suporte a texto + imagens com embeddings Voyage
- **🗄️ AstraDB**: Banco vetorial distribuído para escalabilidade
- **🔒 Segurança**: Rate limiting, autenticação Bearer, validação SSRF/XSS

## 🚀 Quick Start

### 1. Configuração do Ambiente

```bash
# Clone o repositório
git clone https://github.com/ceccato88/rag.git
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
OPENAI_MODEL=gpt-4.1-mini              # Subagentes
COORDINATOR_MODEL=gpt-4.1              # Coordenador
EMBEDDING_MODEL=voyage-multimodal-3

# Sistema Multi-Agente
MAX_CANDIDATES=3                       # Padrão (varia por complexidade)
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

# Via código Python
from src.core.indexer import DocumentIndexer
indexer = DocumentIndexer()
indexer.index_pdf("https://arxiv.org/pdf/2501.13956")
```

## 📖 Uso da API

### Research Multi-Agente

```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como Zep implementa temporal knowledge graphs para memória de agentes AI?"
  }'
```

### Busca com Focus Areas Específicas

```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "O que é Zep?",
    "focus_areas": ["conceptual", "examples", "overview"]
  }'
```

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                  🎯 User Query                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│     🧠 Enhanced Lead Researcher (gpt-4.1)          │
│  • Query Analysis • Complexity Detection           │
│  • Specialist Selection • Enhanced Synthesis       │
└─────────────────┬───────────────────────────────────┘
                  │ (decompose by complexity)
                  ▼
┌─────────────────────────────────────────────────────┐
│              ⚡ Specialist Agents                   │
│                                                     │
│  🎯 CONCEPTUAL    ⚖️ COMPARATIVE    � TECHNICAL   │  
│  (gpt-4o-mini)   (gpt-4o-mini)    (gpt-4o-mini)   │
│       │               │                │           │
│       ▼               ▼                ▼           │
│  📚 RAG Search   📚 RAG Search   📚 RAG Search     │
│  (focus: conceptual) (focus: comparative) (focus: technical) │
└─────┬───────────────┬──────────────┬───────────────┘
      │               │              │
      ▼               ▼              ▼
┌─────────────────────────────────────────────────────┐
│      🧠 Enhanced Synthesis (gpt-4.1)               │
│  • Cross-reference Analysis • Quality Assessment    │
│  • Conflict Resolution • Structured Report          │
└─────────────────────────────────────────────────────┘
```

## 🎯 Specialist Types vs Focus Areas

### 📋 Diferença Conceitual

**Specialist Types** e **Focus Areas** são conceitos complementares mas distintos:

- **🤖 Specialist Types**: Define **QUAL agente** será instanciado (classe do agente)
- **🎯 Focus Areas**: Define **COMO** o agente vai processar a informação

### 🔄 Fluxo de Processamento

```
Query → Specialist Selection → Focus Area Mapping → Agent Processing
```

1. **Análise da Query**: Sistema analisa a query para detectar padrões
2. **Seleção do Specialist**: Escolhe qual tipo de agente usar (CONCEPTUAL, TECHNICAL, etc.)
3. **Mapeamento de Focus**: Define como o agente deve processar (conceptual, technical, etc.)
4. **Processamento**: Agente usa o focus area para ajustar busca e formatação

### 🤖 Specialist Types (5 tipos - Define QUAL agente)
| Specialist | Função | Quando Usar |
|------------|--------|-------------|
| **CONCEPTUAL** | Extração de conceitos, definições, teoria | "O que é...", "Defina...", necessidade de base conceitual |
| **TECHNICAL** | Detalhes técnicos, implementação, arquitetura | "Como implementar...", especificações técnicas |
| **COMPARATIVE** | Análise comparativa, diferenças, alternativas | "X vs Y", "diferenças entre...", avaliações |
| **EXAMPLES** | Casos de uso, exemplos práticos, demonstrações | "Exemplos de...", casos práticos, proof-of-concept |
| **GENERAL** | Pesquisa geral, coordenação, contexto amplo | Queries gerais ou como complemento |

### 🔍 Correspondência 1:1 (Specialist ↔ Focus Area)

Na maioria dos casos, há correspondência direta:

```python
CONCEPTUAL → focus_area: "conceptual" + ["definitions", "theoretical_background"]
TECHNICAL → focus_area: "technical" + ["architecture", "implementation"]  
COMPARATIVE → focus_area: "comparative" + ["alternatives", "differences"]
EXAMPLES → focus_area: "examples" + ["case_studies", "applications"]
GENERAL → focus_area: "general" + ["overview", "broad_context"]
```

## 📊 Query Complexity Detection

O sistema Enhanced detecta automaticamente a complexidade das queries:

### 🟢 SIMPLE
- **Características**: Perguntas diretas sobre definições/conceitos
- **Candidatos**: 2 documentos
- **Estratégia**: Busca direta e focada
- **Exemplo**: "O que é machine learning?"

### 🟡 MODERATE  
- **Características**: Perguntas sobre funcionamento/processo
- **Candidatos**: 3 documentos
- **Estratégia**: Expansão semântica moderada
- **Exemplo**: "Como funciona o deep learning?"

### 🟠 COMPLEX
- **Características**: Comparação/análise de múltiplos aspectos
- **Candidatos**: 4 documentos
- **Estratégia**: Múltiplas perspectivas
- **Exemplo**: "Compare machine learning e deep learning"

### 🔴 VERY_COMPLEX
- **Características**: Análises avançadas, síntese de múltiplas fontes
- **Candidatos**: 5 documentos  
- **Estratégia**: Análise profunda e síntese avançada
- **Exemplo**: "Analyze the evolution and future of AI reasoning systems"

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
│       ├── enhanced/             # Enhanced system components
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
OPENAI_MODEL=gpt-4.1-mini              # Subagentes (eficiência)
COORDINATOR_MODEL=gpt-4.1              # Coordenador (qualidade)
EMBEDDING_MODEL=voyage-multimodal-3    # Embeddings multimodais
```

### Performance

```env
# Configurações de performance por complexidade
MAX_CANDIDATES_SIMPLE=2                # Queries simples
MAX_CANDIDATES_MODERATE=3              # Queries moderadas
MAX_CANDIDATES_COMPLEX=4               # Queries complexas
MAX_CANDIDATES_VERY_COMPLEX=5          # Queries muito complexas
MAX_CANDIDATES=3                       # Fallback geral
PARALLEL_EXECUTION=true                # Execução paralela
SUBAGENT_TIMEOUT=300.0                # Timeout por subagente (5min)
```

### Configuração Unificada

O sistema usa configuração unificada que otimiza automaticamente parâmetros baseado na complexidade da query e tipo de especialista:

```env
# Configuração automática por complexidade + especialista
# Exemplo: COMPLEX + TECHNICAL = max_candidates=4, similarity_threshold=0.65
# Exemplo: SIMPLE + CONCEPTUAL = max_candidates=2, similarity_threshold=0.70
UNIFIED_CONFIG_ENABLED=true
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
# 🔧 Teste do Sistema Enhanced
python scripts/test_enhanced_system.py

# 🚀 Teste de Integração Enhanced
python scripts/test_enhanced_integration.py

# �️ Verificar Consistência de Configuração
python scripts/verify_config_consistency.py
```

### Estrutura de Testes
- **`scripts/test_enhanced_system.py`** - Teste completo do sistema enhanced
- **`scripts/test_enhanced_integration.py`** - Teste de integração dos componentes
- **`scripts/verify_config_consistency.py`** - Verificação de consistência de config

Logs salvos em `/logs/`.

## 📚 Documentação

- [📖 Guia Completo](docs/README.md)
- [🏗️ Arquitetura](docs/architecture.md)
- [🔥 Sistema Enhanced](docs/enhanced-system.md)
- [🤖 Sistema Multi-Agente](docs/multi-agent.md)
- [⚡ Quick Start](docs/quick-start.md)
- [🔍 ReAct Reasoning](docs/reasoning.md)
- [📝 Guia da API](docs/api-guide.md)
- [🧪 Testing](docs/testing.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para a branch (`git push origin feature/amazing-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

## 🆘 Suporte

- 🐛 Issues: [GitHub Issues](https://github.com/ceccato88/rag/issues)

---

**🚀 Built with ❤️ using FastAPI, OpenAI, Voyage AI, and AstraDB**
