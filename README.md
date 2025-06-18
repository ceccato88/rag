# 🚀 Sistema RAG Multi-Agente Avançado

Sistema de geração aumentada por recuperação (RAG) com arquitetura multi-agente especializada, reasoning avançado e sistema de memória distribuída.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Guia de Uso](#-guia-de-uso)
- [Componentes Principais](#-componentes-principais)
- [Desenvolvimento](#-desenvolvimento)
- [Troubleshooting](#-troubleshooting)

## 🎯 Visão Geral

Este sistema implementa uma arquitetura RAG avançada que vai além dos sistemas tradicionais, oferecendo:

- **Multi-Agentes Especializados**: Agentes com especialização em diferentes tipos de análise
- **Reasoning ReAct Avançado**: Sistema de raciocínio estruturado com persistência
- **Memória Distribuída**: Sistema de memória hierárquica com cache inteligente
- **Busca Otimizada**: Pipeline de busca otimizado com reranking semântico
- **Especialização por Contexto**: Adaptação automática baseada no tipo de consulta

### 🏗️ Diferencial Técnico

- **Separação de Responsabilidades**: Busca + reranking separado da geração de resposta
- **Cache Hierárquico**: Sistema L1/L2 para otimização de performance
- **Checkpoint Automático**: Persistência automática do estado de reasoning
- **Detecção Avançada de Loops**: Análise semântica para evitar reasoning circular
- **Métricas de Confiança**: Sistema multidimensional de avaliação de qualidade

## 🏛️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    SISTEMA RAG MULTI-AGENTE             │
├─────────────────────────────────────────────────────────┤
│  🧠 CAMADA DE REASONING                                 │
│  ├── ReAct Enhanced (reasoning estruturado)            │
│  ├── Loop Detection (análise semântica)                │
│  ├── Confidence Metrics (métricas multidimensionais)   │
│  └── Checkpoint System (persistência automática)       │
├─────────────────────────────────────────────────────────┤
│  👥 CAMADA DE AGENTES                                   │
│  ├── Lead Researcher (coordenação)                     │
│  ├── Concept Extraction (análise conceitual)           │
│  ├── Comparative Analysis (análise comparativa)        │
│  ├── Technical Detail (detalhes técnicos)              │
│  └── Example Finder (casos de uso)                     │
├─────────────────────────────────────────────────────────┤
│  🔍 CAMADA DE BUSCA                                     │
│  ├── Vector Search (Astra DB + Voyage embeddings)      │
│  ├── Semantic Reranking (GPT-4o reranking)            │
│  ├── Relevance Checking (validação de relevância)      │
│  └── Focus Area Adaptation (adaptação por contexto)    │
├─────────────────────────────────────────────────────────┤
│  💾 CAMADA DE MEMÓRIA                                   │
│  ├── Distributed Storage (armazenamento distribuído)   │
│  ├── Hierarchical Cache (cache L1/L2)                  │
│  ├── Semantic Indexing (indexação semântica)           │
│  └── Pattern Learning (aprendizado de padrões)         │
├─────────────────────────────────────────────────────────┤
│  📊 CAMADA DE MONITORAMENTO                             │
│  ├── Performance Metrics (métricas de performance)     │
│  ├── Resource Management (gestão de recursos)          │
│  ├── Cache Statistics (estatísticas de cache)          │
│  └── Success Rate Tracking (acompanhamento de sucesso) │
└─────────────────────────────────────────────────────────┘
```

## ⚙️ Instalação e Configuração

### Pré-requisitos

- Python 3.11+
- Acesso à API do OpenAI
- Acesso à API do Voyage AI
- Instância do Astra DB (Cassandra)

### 1. Configuração do Ambiente

```bash
# Clone o repositório
git clone <repository-url>
cd rag

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
```

### 2. Configuração do `.env`

```env
# APIs Essenciais
OPENAI_API_KEY=sk-...
VOYAGE_API_KEY=pa-...

# Banco de Dados
ASTRA_DB_API_ENDPOINT=https://...
ASTRA_DB_APPLICATION_TOKEN=AstraCS:...

# Configurações do Multi-Agente
MAX_SUBAGENTS=3
MULTIAGENT_MODEL=gpt-4o-mini
PARALLEL_EXECUTION=true
USE_LLM_DECOMPOSITION=true
SUBAGENT_TIMEOUT=180.0

# Configurações de Performance
MAX_TOKENS_DECOMPOSITION=1000
```

### 3. Indexação dos Documentos

```bash
# Indexar documentos PDF
python indexer.py

# Verificar indexação
python -c "from search import ProductionConversationalRAG; rag = ProductionConversationalRAG(); print('✅ Sistema funcionando')"
```

## 🎮 Guia de Uso

### Uso Básico - Interface Interativa

```bash
# Executar sistema interativo
python main_multiagent.py

# Opções disponíveis:
# 1. Modo Interativo (perguntas manuais)
# 2. Modo Demonstração (perguntas pré-definidas)
```

### Uso Programático

```python
import asyncio
from researcher.agents.openai_lead_researcher import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext

async def consulta_rag():
    # Configurar sistema
    config = OpenAILeadConfig.from_env()
    agent = OpenAILeadResearcher(
        agent_id="meu-sistema",
        name="Sistema RAG",
        config=config
    )
    
    # Criar contexto
    context = AgentContext(
        query="O que é Zep e como funciona?",
        objective="Compreender conceito e funcionamento",
        constraints=["Foco em aspectos técnicos"]
    )
    
    # Executar consulta
    result = await agent.run(context)
    print(result.output)

# Executar
asyncio.run(consulta_rag())
```

### Testes do Sistema

```bash
# Teste simples das funcionalidades
python teste_melhorias_simples.py

# Teste direto do RAG
python teste_direto.py

# Teste do sistema limpo
python teste_sistema_limpo.py

# Avaliação completa
python evaluator.py
```

## 🧩 Componentes Principais

### 1. **Agentes Lead (Coordenadores)**

#### OpenAI Lead Researcher
- **Localização**: `multi-agent-researcher/src/researcher/agents/openai_lead_researcher.py`
- **Função**: Coordena múltiplos subagentes usando LLM para decomposição inteligente
- **Características**:
  - Decomposição automática de queries complexas
  - Coordenação paralela de subagentes
  - Síntese inteligente de resultados
  - Sistema ReAct integrado

#### Basic Lead Researcher  
- **Localização**: `multi-agent-researcher/src/researcher/agents/basic_lead_researcher.py`
- **Função**: Coordenador simples sem LLM de decomposição
- **Uso**: Casos onde não é necessária decomposição complexa

### 2. **Subagentes Especializados**

#### Document Search Agent
- **Localização**: `multi-agent-researcher/src/researcher/agents/document_search_agent.py`
- **Função**: Agente base para busca em documentos
- **Características**:
  - Busca otimizada com foco por área
  - Processamento especializado de documentos
  - Formatação adaptativa de respostas

#### Enhanced RAG Subagent
- **Localização**: `multi-agent-researcher/src/researcher/agents/enhanced_rag_subagent.py`
- **Especialistas**:
  - **ConceptExtractionSubagent**: Extração de conceitos e definições
  - **ComparativeAnalysisSubagent**: Análises comparativas
  - **TechnicalDetailSubagent**: Detalhes técnicos e implementação
  - **ExampleFinderSubagent**: Exemplos e casos de uso

### 3. **Sistema de Reasoning**

#### Enhanced ReAct Reasoning
- **Localização**: `multi-agent-researcher/src/researcher/reasoning/enhanced_react_reasoning.py`
- **Características**:
  - Reasoning estruturado em 5 fases
  - Detecção avançada de loops
  - Métricas de confiança multidimensionais
  - Persistência automática com checkpoints
  - Aprendizado de padrões

#### Fases do ReAct:
1. **Fact Gathering**: Coleta de fatos e suposições
2. **Planning**: Criação de plano estruturado
3. **Execution**: Execução das ações planejadas
4. **Validation**: Verificação de progresso
5. **Reflection**: Reflexão e ajustes

### 4. **Sistema de Memória**

#### Enhanced Memory System
- **Localização**: `multi-agent-researcher/src/researcher/memory/enhanced_memory.py`
- **Características**:
  - Armazenamento distribuído com sharding
  - Cache hierárquico (L1/L2)
  - Indexação múltipla (hash, btree, semântica)
  - Busca semântica avançada
  - Compressão e otimização automática

### 5. **Ferramentas de Busca**

#### Optimized RAG Search Tool
- **Localização**: `multi-agent-researcher/src/researcher/tools/optimized_rag_search.py`
- **Inovação**: Separa busca+reranking da geração de resposta
- **Vantagens**:
  - Maior flexibilidade para especialização
  - Redução de calls desnecessários para LLM
  - Cache de resultados de busca
  - Adaptação automática por área de foco

### 6. **Módulos Utilitários**

#### Cache System (`utils/cache.py`)
- Cache hierárquico com TTL
- Estratégias de eviction (LRU, LFU)
- Estatísticas de performance
- Decorators para cache automático

#### Metrics System (`utils/metrics.py`)
- Métricas de processamento
- Medição automática de tempo
- Context managers para tracking
- Relatórios de performance

#### Validation System (`utils/validation.py`)
- Validação de documentos e embeddings
- Verificação de variáveis de ambiente
- Sanitização de nomes de arquivo
- Validação de caminhos e permissões

#### Resource Manager (`utils/resource_manager.py`)
- Gestão de recursos temporários
- Limpeza automática de arquivos antigos
- Organização de diretórios
- Backup e recovery

## 📈 Desenvolvimento

### Estrutura de Diretórios

```
/workspaces/rag/
├── 📁 multi-agent-researcher/src/researcher/
│   ├── agents/                    # Agentes do sistema
│   ├── reasoning/                 # Sistema de reasoning
│   ├── memory/                    # Sistema de memória  
│   └── tools/                     # Ferramentas especializadas
├── 📁 utils/                      # Módulos utilitários
├── 📁 tests/                      # Testes do sistema
├── 📄 search.py                   # Sistema RAG principal
├── 📄 indexer.py                  # Sistema de indexação
├── 📄 evaluator.py                # Sistema de avaliação
└── 📄 main_multiagent.py          # Interface principal
```

### Extensão do Sistema

#### Adicionando Novo Especialista

```python
# 1. Criar classe especializada
class NovoEspecialistaSubagent(RAGResearchSubagent):
    _focus_area = "nova_especialidade"
    
    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        return [{
            "query": f"palavra-chave-especializada {context.query}",
            "objective": context.objective,
            "focus_area": "nova_area",
            "expected_output": "Tipo de resultado esperado"
        }]

# 2. Registrar no SpecialistSelector
self.specialists[SpecialistType.NOVA_AREA] = NovoEspecialistaSubagent

# 3. Adicionar padrões de detecção
self.query_patterns[SpecialistType.NOVA_AREA] = [
    "palavra1", "palavra2", "padrão específico"
]
```

#### Adicionando Nova Ferramenta

```python
# 1. Herdar de Tool base
class NovaFerramenta(Tool):
    def __init__(self):
        super().__init__(
            name="nova_ferramenta",
            description="Descrição da nova ferramenta"
        )
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        # Implementar lógica da ferramenta
        pass

# 2. Integrar no agente
self.nova_ferramenta = NovaFerramenta()
```

### Testes

#### Executar Testes Unitários

```bash
# Todos os testes
python -m pytest tests/ -v

# Testes específicos
python -m pytest tests/unit/test_cache.py -v
python -m pytest tests/functional/test_search.py -v
```

#### Criar Novo Teste

```python
import pytest
from utils.validation import validate_query

def test_nova_funcionalidade():
    # Arrange
    input_data = "dados de teste"
    
    # Act
    result = funcao_sendo_testada(input_data)
    
    # Assert
    assert result.success == True
    assert "palavra_esperada" in result.output
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Astra DB
```
Erro: "Connection failed"
Solução: Verificar ASTRA_DB_API_ENDPOINT e ASTRA_DB_APPLICATION_TOKEN
```

#### 2. Timeout nos Agentes
```
Erro: "Agent timeout"
Solução: Aumentar SUBAGENT_TIMEOUT no .env
```

#### 3. Erro de API Key
```
Erro: "Invalid API key"
Solução: Verificar OPENAI_API_KEY e VOYAGE_API_KEY
```

#### 4. Memória Insuficiente
```
Erro: "Out of memory"
Solução: Reduzir MAX_SUBAGENTS ou implementar batch processing
```

### Logs e Debug

#### Ativar Logs Detalhados

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Verificar Métricas de Performance

```python
from utils.metrics import ProcessingMetrics
metrics = ProcessingMetrics()
# Use metrics.log_summary() para ver estatísticas
```

#### Analisar Cache

```python
from utils.cache import global_cache
stats = global_cache.stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

### Otimização de Performance

#### 1. Ajustar Cache
- Aumentar tamanho do cache L1/L2
- Ajustar TTL baseado no padrão de uso
- Usar cache function decorators

#### 2. Otimizar Queries
- Usar queries mais específicas
- Aproveitar focus_area para direcionamento
- Implementar cache de embeddings

#### 3. Paralelismo
- Aumentar MAX_SUBAGENTS (cuidado com rate limits)
- Usar PARALLEL_EXECUTION=true
- Otimizar timeout de subagentes

## 📚 Recursos Adicionais

- **Documentação da API**: Consulte docstrings nas classes
- **Exemplos**: Veja arquivos `teste_*.py` para exemplos práticos
- **Arquitetura**: Consulte diagramas em `docs/` (se disponível)
- **Performance**: Use `evaluator.py` para métricas detalhadas

---

**Desenvolvido com ❤️ para pesquisa avançada com IA**