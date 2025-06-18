# Sistema de Agentes RAG Multimodal

Um sistema sofisticado de RAG (Retrieval-Augmented Generation) multiagente que usa [Instructor](https://github.com/jxnl/instructor) para saídas estruturadas de LLM e suporta processamento multimodal de documentos com imagens e texto.

## Funcionalidades

- 🤖 **Arquitetura Multiagente**: Agente RAG líder decompõe consultas e coordena agentes especializados
- 🔍 **Busca Multimodal**: Integra embeddings multimodais Voyage AI com busca vetorial Astra DB
- 📊 **Saídas Estruturadas**: Usa Instructor para obter respostas tipadas e validadas de LLMs
- 🖼️ **Processamento Visual**: Lida com documentos PDF com imagens e diagramas
- 🔄 **Re-ranqueamento Inteligente**: Re-ranqueamento inteligente de documentos com análise de contexto
- ⚡ **Execução Paralela**: Múltiplos agentes trabalham simultaneamente para resultados mais rápidos
- 🔧 **Configuração Flexível**: Auto-descoberta de arquivos de ambiente para flexibilidade de implantação

## Início Rápido

### Instalação

```bash
# Navegue para o diretório do projeto
cd multimodal-rag-agents

# Instale as dependências no ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -e .
```

### Configuração do Ambiente

O sistema busca automaticamente por arquivos `.env` em múltiplas localizações:
- Diretório atual
- Raiz do projeto
- Diretório pai
- Diretório home
- Caminhos de configuração do sistema

Crie um arquivo `.env` em qualquer uma dessas localizações:

```bash
# Chaves de API Obrigatórias
OPENAI_API_KEY=sua-chave-openai-aqui
VOYAGE_API_KEY=sua-chave-voyage-aqui

# Configuração Obrigatória do Astra DB
ASTRA_DB_API_ENDPOINT=https://seu-id-database-regiao.apps.astra.datastax.com
ASTRA_DB_APPLICATION_TOKEN=AstraCS:seu-token-aqui

# Configuração de Modelos
LLM_MODEL=gpt-4o                     # Modelo principal para Lead RAG Agent
RERANKER_MODEL=gpt-4o                # Modelo para re-ranking de documentos
CONTEXT_ANALYZER_MODEL=gpt-4o        # Modelo para análise de contexto
ANSWER_GENERATOR_MODEL=gpt-4o        # Modelo para geração de respostas
EMBEDDING_MODEL=voyage-multimodal-3  # Modelo para embeddings multimodais

# Configuração Opcional
COLLECTION_NAME=pdf_documents
IMAGE_DIR=pdf_images
MAX_CANDIDATES=5
```

### Executar Exemplos

```bash
# Demo rápido para testar o sistema
python run_demo.py

# Teste com uma consulta real
python test_real_query.py

# Exemplo abrangente com pipeline completo
python examples/basic_multimodal_rag.py
```

## Arquitetura

O sistema implementa uma arquitetura RAG multiagente hierárquica:

```
Consulta do Usuário → Agente RAG Líder → Decomposição da Consulta (via Instructor)
                        ↓
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    ▼                    ▼                    ▼       ▼
Agente      → Agente      → Analisador → Gerador
Recuperador   Re-ranque     de Contexto   de Resposta
    │            │              │            │
    ▼            ▼              ▼            ▼
Embeddings   OpenAI GPT    Análise de    Resposta
Multimodais     Re-ranque   Qualidade     Multimodal
Voyage AI      Inteligente               
    │
    ▼
Astra DB → Candidatos de Documentos → Resultado RAG Final
Banco de
Dados Vetorial
```

### Componentes Principais

1. **LeadRAGAgent**: Orquestra o pipeline RAG completo usando Instructor para análise estruturada de consultas
2. **MultimodalRetrieverAgent**: Recupera documentos relevantes usando embeddings multimodais Voyage AI
3. **MultimodalRerankerAgent**: Re-ranqueia documentos inteligentemente baseado na relevância da consulta
4. **ContextAnalyzerAgent**: Analisa qualidade e completude do contexto
5. **MultimodalAnswerAgent**: Gera respostas abrangentes com suporte a elementos visuais
6. **Configuração Flexível**: Sistema de auto-descoberta para variáveis de ambiente

## Uso

### Uso Básico

```python
import asyncio
from src.rag_agents.agents.lead_rag import LeadRAGAgent, LeadRAGConfig
from src.rag_agents.agents.retriever import MultimodalRetrieverAgent, RetrieverConfig
from src.rag_agents.agents.reranker import MultimodalRerankerAgent, RerankerConfig
from src.rag_agents.agents.context_analyzer import ContextAnalyzerAgent, ContextAnalyzerConfig
from src.rag_agents.agents.answer_generator import MultimodalAnswerAgent, AnswerGeneratorConfig
from src.rag_agents.agents.base import AgentContext
from config import get_config

async def consulta_rag_multimodal():
    # Carregamento flexível de configuração
    config = get_config()
    if not config.is_ready():
        print("❌ Configuração de ambiente incompleta")
        config.print_status()
        return
    
    # Inicializar configurações dos agentes
    retriever_config = RetrieverConfig(max_candidates=5)
    reranker_config = RerankerConfig(openai_api_key=config.get("OPENAI_API_KEY"))
    analyzer_config = ContextAnalyzerConfig(openai_api_key=config.get("OPENAI_API_KEY"))
    generator_config = AnswerGeneratorConfig(openai_api_key=config.get("OPENAI_API_KEY"))
    lead_config = LeadRAGConfig(openai_api_key=config.get("OPENAI_API_KEY"))
    
    # Inicializar agentes
    retriever = MultimodalRetrieverAgent(config=retriever_config, name="Recuperador")
    reranker = MultimodalRerankerAgent(config=reranker_config, name="Reranqueador")
    context_analyzer = ContextAnalyzerAgent(config=analyzer_config, name="AnalisadorContexto")
    answer_generator = MultimodalAnswerAgent(config=generator_config, name="GeradorResposta")
    
    # Criar agente líder
    lead_agent = LeadRAGAgent(
        retriever_agent=retriever,
        reranker_agent=reranker,
        context_analyzer_agent=context_analyzer,
        answer_generator_agent=answer_generator,
        config=lead_config,
        name="AgenteLider"
    )
    
    # Criar contexto da consulta
    context = AgentContext(
        query="Quais são os principais componentes da arquitetura do sistema?",
        objective="Entender a arquitetura técnica incluindo elementos visuais",
        constraints=["Focar em detalhes técnicos", "Incluir diagramas visuais se disponíveis"]
    )
    
    # Executar RAG multimodal
    result = await lead_agent.run(context)
    
    if result.status.value == "completed":
        rag_result = result.output
        print(f"Resposta: {rag_result.answer.main_response}")
        print(f"Fontes: {len(rag_result.answer.sources_used)}")
        print(f"Confiança: {rag_result.answer.multimodal_confidence:.2f}")
    else:
        print(f"Erro: {result.error}")

# Executar
asyncio.run(consulta_rag_multimodal())
```

### Configuração Avançada

```python
# Configuração de recuperação personalizada
retriever_config = RetrieverConfig(
    max_candidates=10,
    similarity_threshold=0.7,
    collection_name="documentos_personalizados"
)

# Configuração de re-ranqueamento personalizada
reranker_config = RerankerConfig(
    openai_api_key=config.get("OPENAI_API_KEY"),
    model="gpt-4o",
    max_tokens=1024,
    temperature=0.1
)

# Configuração de geração de resposta personalizada
generator_config = AnswerGeneratorConfig(
    openai_api_key=config.get("OPENAI_API_KEY"),
    model="gpt-4o",
    max_tokens=2048,
    include_visual_analysis=True
)
```

## Como Funciona

1. **Decomposição da Consulta**: O agente RAG líder usa Instructor para analisar a consulta e determinar estratégias de busca ótimas
2. **Recuperação Multimodal**: O agente recuperador busca documentos usando embeddings multimodais Voyage AI
3. **Re-ranqueamento Inteligente**: Documentos são re-ranqueados baseados na relevância para a consulta específica
4. **Análise de Contexto**: O analisador de contexto avalia a qualidade e completude das informações recuperadas
5. **Geração de Resposta**: O gerador de resposta cria respostas abrangentes com suporte a elementos visuais

## Configuração de Ambiente

O sistema usa um sistema de configuração flexível que busca automaticamente por arquivos `.env` em múltiplas localizações:

```python
# Verificar status da configuração
python config.py

# O sistema busca estas localizações automaticamente:
# 1. Diretório atual: ./env
# 2. Raiz do projeto: /caminho/para/multimodal-rag-agents/.env
# 3. Diretório pai: /caminho/para/pai/.env
# 4. Diretório home: ~/.env
# 5. Config do sistema: ~/.config/multimodal-rag/.env
# 6. Todo o sistema: /etc/multimodal-rag/.env
# 7. Caminho personalizado via variável de ambiente RAG_CONFIG_PATH
```

## Estrutura do Projeto

```
multimodal-rag-agents/
├── README.md                           # Este arquivo
├── config.py                          # Sistema de configuração flexível
├── pyproject.toml                     # Dependências e config do projeto
├── run_demo.py                        # Demo rápido
├── test_real_query.py                 # Teste de consulta real
├── examples/
│   └── basic_multimodal_rag.py       # Exemplo abrangente
└── src/
    └── rag_agents/
        ├── agents/                    # Todas as implementações de agentes
        │   ├── base.py               # Classe base de agente
        │   ├── lead_rag.py           # Orquestrador RAG líder
        │   ├── retriever.py          # Recuperação multimodal
        │   ├── reranker.py           # Re-ranqueamento inteligente
        │   ├── context_analyzer.py   # Análise de qualidade de contexto
        │   └── answer_generator.py   # Geração de resposta
        └── models/
            └── rag_models.py          # Modelos Pydantic para dados estruturados
```

## Funcionalidades Principais

### Processamento de Documentos Multimodal
- Lida com documentos PDF com imagens e diagramas incorporados
- Extrai e processa elementos visuais junto com texto
- Mantém contexto entre componentes de texto e visuais

### Coordenação Inteligente de Agentes
- Agente líder decompõe consultas em estratégias de busca ótimas
- Agentes especializados lidam com diferentes aspectos do pipeline RAG
- Processamento paralelo para melhor desempenho

### Geração de Saída Estruturada
- Todas as interações LLM usam modelos Pydantic via Instructor
- Respostas type-safe e validadas em cada etapa
- Estruturas de resultado abrangentes com metadados

### Configuração Pronta para Produção
- Gerenciamento flexível de variáveis de ambiente
- Auto-descoberta de arquivos de configuração
- Funciona em vários cenários de implantação

## Referência da API

### Modelos Principais

```python
# Decomposição da consulta
class RAGDecomposition(BaseModel):
    query_type: str
    key_aspects: List[str]
    search_strategies: List[SearchStrategy]
    ranking_criteria: List[RankingCriterion]
    response_format: str

# Resposta estruturada
class StructuredAnswer(BaseModel):
    main_response: str
    sources_used: List[SourceReference]
    multimodal_confidence: float
    evidence_strength: str
    visual_elements_used: List[str]
    limitations: List[str]
    follow_up_suggestions: List[str]
```

### Configurações dos Agentes

```python
# Configuração do recuperador
class RetrieverConfig(BaseModel):
    max_candidates: int = 5
    similarity_threshold: float = 0.7
    collection_name: str = "pdf_documents"

# Configuração do re-ranqueador  
class RerankerConfig(BaseModel):
    openai_api_key: str
    model: str = "gpt-4o"
    max_tokens: int = 512
    temperature: float = 0.1

# Configuração do gerador de resposta
class AnswerGeneratorConfig(BaseModel):
    openai_api_key: str
    model: str = "gpt-4o"
    max_tokens: int = 2048
    include_visual_analysis: bool = True
```

## Testes

```bash
# Testar componentes do sistema
python test_real_query.py

# Executar demo rápido
python run_demo.py

# Testar com configuração de ambiente
python config.py
```

## Considerações de Desempenho

- **Processamento Paralelo**: Agentes trabalham simultaneamente para reduzir latência
- **Eficiência de Token**: Saídas estruturadas minimizam uso de tokens
- **Cache**: Embeddings multimodais são cacheados para consultas repetidas
- **Processamento em Lote**: Múltiplos documentos processados em paralelo

## Otimização de Custos

O sistema permite configurar diferentes modelos para cada agente, permitindo otimização de custos:

### Configurações Recomendadas:

**🏆 Alta Qualidade (Recomendado)**
```bash
LLM_MODEL=gpt-4o
RERANKER_MODEL=gpt-4o
CONTEXT_ANALYZER_MODEL=gpt-4o
ANSWER_GENERATOR_MODEL=gpt-4o
```

**⚖️ Balanceado (Custo/Qualidade)**
```bash
LLM_MODEL=gpt-4o
RERANKER_MODEL=gpt-4o
CONTEXT_ANALYZER_MODEL=gpt-4o-mini
ANSWER_GENERATOR_MODEL=gpt-4o
```

**💰 Otimizado para Custo**
```bash
LLM_MODEL=gpt-4o-mini
RERANKER_MODEL=gpt-4o
CONTEXT_ANALYZER_MODEL=gpt-4o-mini
ANSWER_GENERATOR_MODEL=gpt-4o-mini
```

### Recomendações por Agente:

- **Lead RAG Agent**: `gpt-4o` ou `gpt-4o-mini` para decomposição de queries
- **Reranker Agent**: `gpt-4o` obrigatório para análise multimodal de qualidade
- **Context Analyzer**: `gpt-4o-mini` adequado para análise de qualidade
- **Answer Generator**: `gpt-4o` recomendado para respostas de alta qualidade

## Opções de Implantação

### Desenvolvimento
```bash
# Desenvolvimento local com arquivo .env
python run_demo.py
```

### Produção
```bash
# Variáveis de ambiente definidas no nível do sistema
export OPENAI_API_KEY="sua-chave"
export VOYAGE_API_KEY="sua-chave"
export ASTRA_DB_API_ENDPOINT="seu-endpoint"
export ASTRA_DB_APPLICATION_TOKEN="seu-token"

python examples/basic_multimodal_rag.py
```

### Implantação em Container
```bash
# Definir RAG_CONFIG_PATH para apontar para diretório de config
export RAG_CONFIG_PATH="/app/config"
# Colocar arquivo .env em /app/config/.env
```

## Contribuindo

1. Faça fork do repositório
2. Crie uma branch de funcionalidade
3. Faça suas alterações
4. Adicione testes para nova funcionalidade
5. Envie um pull request

## Licença

Licença MIT - veja [LICENSE](LICENSE) para detalhes.

## Agradecimentos

- Construído com [Instructor](https://github.com/jxnl/instructor) para saídas estruturadas confiáveis
- Powered by [Voyage AI](https://www.voyageai.com/) para embeddings multimodais
- Usa [Astra DB](https://www.datastax.com/products/datastax-astra) para armazenamento vetorial
- Inspirado na arquitetura de pesquisa multiagente da Anthropic

## Projetos Relacionados

- Sistema RAG original: `../search.py`, `../indexer.py`, `../evaluator.py`
- Pesquisador multiagente: `../multi-agent-researcher/`