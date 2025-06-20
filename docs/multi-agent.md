# 🤖 Sistema Multi-Agente

## 🎯 Conceito Fundamental

O sistema utiliza uma arquitetura hierárquica inovadora que combina **eficiência** (subagentes especializados) com **qualidade** (coordenador avançado) para pesquisa inteligente.

## 🧠 Hierarquia de Agentes

### 🎖️ Lead Researcher (Coordenador)
**Modelo**: GPT-4.1 (modelo completo para pensamento crítico superior)

**Responsabilidades**:
- 🔍 **Query Decomposition**: Análise e quebra de queries complexas
- 🎯 **Focus Area Selection**: Escolha inteligente de especializações
- ⚡ **Orchestration**: Coordenação da execução paralela
- 🧠 **Advanced Synthesis**: Síntese crítica com análise cross-reference

**Capabilities Únicas**:
- ReAct reasoning estruturado
- Detecção de contradições entre achados
- Geração de insights originais
- Validação de consistência lógica

### ⚡ Subagentes RAG (Especialistas)
**Modelo**: GPT-4.1-mini (otimizado para eficiência e foco)

**Execução**: Paralela (até 3 simultâneos)

**Especializações**:

#### 🎓 Conceptual Agent
- **Foco**: Definições, conceitos, fundamentos teóricos
- **Quando usar**: Queries tipo "O que é...", "Defina...", necessidade de base conceitual
- **Query adjustment**: `definition concepts fundamentals {query}`
- **Processing**: Extrai definições, significados, frameworks teóricos

#### 🔧 Technical Agent  
- **Foco**: Implementação, arquitetura, algoritmos, código
- **Quando usar**: "Como implementar...", especificações técnicas, arquiteturas
- **Query adjustment**: `technical implementation architecture {query}`
- **Processing**: Identifica padrões técnicos, código, diagramas de arquitetura

#### ⚖️ Comparative Agent
- **Foco**: Comparações, análises, vantagens/desvantagens
- **Quando usar**: "X vs Y", "diferenças entre...", avaliações
- **Query adjustment**: `comparison analysis differences {query}`
- **Processing**: Extrai comparações, tabelas, análises de trade-offs

#### 💡 Examples Agent
- **Foco**: Casos de uso, exemplos práticos, demonstrações
- **Quando usar**: "Exemplos de...", casos práticos, proof-of-concept
- **Query adjustment**: `examples use cases applications {query}`
- **Processing**: Identifica screenshots, demos, casos reais

#### 📖 Overview Agent
- **Foco**: Visão geral, introduções, surveys amplos
- **Quando usar**: Necessidade de contexto geral, getting started
- **Query adjustment**: `overview general introduction {query}`
- **Processing**: Estrutura visões panorâmicas, roadmaps, introduções

#### 🏢 Applications Agent
- **Foco**: Aplicações empresariais, uso em produção, deployment
- **Quando usar**: Interesse em uso real, implementações empresariais
- **Query adjustment**: `practical applications real-world usage {query}`
- **Processing**: Identifica casos empresariais, métricas de produção

#### 🌐 General Agent
- **Foco**: Pesquisa abrangente sem especialização específica
- **Quando usar**: Queries muito gerais, exploração ampla
- **Query adjustment**: Sem modificação da query original
- **Processing**: Análise geral sem filtros especializados

## 🔄 Fluxo de Coordenação

### 1. 📋 Query Analysis & Decomposition
```python
async def plan(self, context: AgentContext):
    # Fact gathering com ReAct reasoning
    facts = self.reasoner.gather_facts(
        task=f"Research planning for: {context.query}",
        context=context
    )
    
    # Análise de complexidade
    complexity = self._assess_complexity(context.query)
    
    # Seleção inteligente de focus areas
    focus_areas = self._select_focus_areas(context.query, complexity)
    
    # Criação de tasks especializadas
    tasks = self._create_specialized_tasks(focus_areas, context)
    
    return tasks
```

### 2. ⚡ Parallel Execution
```python
async def execute_parallel(self, tasks):
    # Criação de subagentes especializados
    subagents = [
        RAGResearchSubagent(focus=task["focus"]) 
        for task in tasks
    ]
    
    # Execução paralela com timeout
    coroutines = [
        asyncio.wait_for(
            subagent.run(context), 
            timeout=self.config.subagent_timeout
        )
        for subagent, context in zip(subagents, task_contexts)
    ]
    
    # Aguarda todos resultados
    results = await asyncio.gather(*coroutines, return_exceptions=True)
    
    return self._process_results(results)
```

### 3. 🧠 Advanced Synthesis
```python
def _advanced_ai_synthesis(self, tasks, results):
    # Integra ReAct reasoning trace
    reasoning_trace = self.reasoner.get_reasoning_trace()
    
    # Prompt sofisticado para GPT-4.1
    synthesis_prompt = f"""
    CONTEXTO DO PROCESSO DE REASONING:
    {reasoning_trace}
    
    RESULTADOS DOS SUBAGENTES:
    {format_subagent_results(results)}
    
    INSTRUÇÕES PARA SÍNTESE CRÍTICA AVANÇADA:
    1. **Continuidade do Reasoning**: Continue o raciocínio iniciado
    2. **Análise Cross-Reference**: Identifique conexões e contradições
    3. **Validação Crítica**: Avalie consistência baseado no reasoning
    4. **Insights Originais**: Derive conclusões não explícitas
    5. **Reflexão sobre Processo**: Valide assumptions vs resultados
    """
    
    # Usa coordenador GPT-4.1 para síntese avançada
    return self._generate_critical_synthesis(synthesis_prompt)
```

## 🎯 Focus Area Selection Logic

### Análise Automática de Query
```python
def _select_focus_areas(self, query: str, complexity: str):
    """Seleção inteligente baseada em padrões linguísticos"""
    
    query_lower = query.lower()
    selected_areas = []
    
    # Padrões conceituais
    if any(pattern in query_lower for pattern in 
           ["what is", "define", "o que é", "conceito"]):
        selected_areas.append("conceptual")
    
    # Padrões técnicos  
    if any(pattern in query_lower for pattern in
           ["implement", "architecture", "como fazer"]):
        selected_areas.append("technical")
    
    # Padrões comparativos
    if any(pattern in query_lower for pattern in
           ["vs", "versus", "compare", "diferença"]):
        selected_areas.append("comparative")
    
    # Padrões de exemplos
    if any(pattern in query_lower for pattern in
           ["example", "caso", "exemplo", "use case"]):
        selected_areas.append("examples")
    
    # Garantir diversidade mínima
    if len(selected_areas) == 0:
        selected_areas = ["overview"]
    elif len(selected_areas) == 1:
        selected_areas.append("general")
    
    # Limitar ao máximo de subagentes
    return selected_areas[:self.config.max_subagents]
```

### LLM-Based Selection (Avançado)
```python
def _llm_focus_selection(self, query: str, context: str):
    """Seleção usando LLM quando padrões não são suficientes"""
    
    system_prompt = """
    Analise a query e selecione 2-3 focus areas complementares:
    
    🎯 AVAILABLE FOCUS AREAS:
    • conceptual: Definições, conceitos, fundamentos
    • technical: Implementação, arquitetura, algoritmos  
    • comparative: Comparações, diferenças, avaliações
    • examples: Casos de uso, demonstrações práticas
    • overview: Visão geral, introdução ampla
    • applications: Aplicações reais, uso empresarial
    • general: Pesquisa abrangente
    
    STRATEGY: Escolha areas que juntas forneçam cobertura completa.
    """
    
    return self.client.create_structured_response(
        system_prompt, query, response_model=FocusAreaSelection
    )
```

## 🔍 Subagent Specialization

### Query Refinement por Focus
```python
class OptimizedRAGSearchTool:
    def _adjust_query_for_focus(self, query: str, focus_area: str):
        """Ajusta query para especialização específica"""
        
        adjustments = {
            "conceptual": f"definition concepts fundamentals {query}",
            "technical": f"technical implementation architecture {query}",
            "comparative": f"comparison analysis differences {query}",
            "examples": f"examples use cases applications {query}",
            "overview": f"overview general introduction {query}",
            "applications": f"practical applications real-world usage {query}",
            "general": query  # Sem modificação
        }
        
        return adjustments.get(focus_area, query)
```

### Document Processing Specialization
```python
class DocumentProcessor:
    @staticmethod
    def extract_by_focus(documents, focus_area):
        """Processamento especializado por focus area"""
        
        processors = {
            "conceptual": ConceptProcessor.extract_concepts,
            "technical": TechnicalProcessor.extract_technical_details,
            "comparative": ComparativeProcessor.extract_comparisons,
            "examples": ExampleProcessor.extract_examples,
            # ... outros processadores
        }
        
        processor = processors.get(focus_area, GeneralProcessor.extract_general)
        return processor(documents)

class ConceptProcessor:
    @staticmethod
    def extract_concepts(documents):
        """Extrai definições e conceitos específicamente"""
        concepts = []
        definitions = []
        
        for doc in documents:
            content = doc.get("content", "")
            
            # Padrões de definição
            if any(pattern in content.lower() for pattern in 
                   ["is defined as", "refers to", "means", "é definido como"]):
                definitions.append({
                    "source": doc.get("document_id"),
                    "definition": content[:200] + "..."
                })
            
            # Extração de termos técnicos
            technical_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
            concepts.extend(technical_terms[:3])
        
        return {
            "concepts": list(set(concepts)),
            "definitions": definitions,
            "focus_quality": len(definitions) / max(len(documents), 1)
        }
```

## ⚡ Performance Optimization

### Parallel Execution Benefits
```python
# Sem paralelo (sequencial): 3 * 4s = 12s
# Com paralelo: max(4s, 3.5s, 4.2s) = 4.2s
# Speedup: ~3x para 3 subagentes
```

### Memory Management
```python
class AgentMemoryManager:
    def __init__(self):
        self.agent_cache = {}  # Cache por agente
        self.shared_cache = {}  # Cache compartilhado
        
    def cache_result(self, agent_id: str, query: str, result: Any):
        """Cache inteligente baseado em agent specialization"""
        
        # Cache local do agente
        agent_key = f"{agent_id}:{hash(query)}"
        self.agent_cache[agent_key] = result
        
        # Cache compartilhado para resultados similares
        if self._is_shareable(result):
            shared_key = f"shared:{hash(query)}"
            self.shared_cache[shared_key] = result
```

### Resource Management
```python
class ResourceManager:
    def __init__(self, max_subagents: int = 3):
        self.semaphore = asyncio.Semaphore(max_subagents)
        self.active_agents = {}
        
    async def execute_with_limits(self, agent_func, *args):
        """Executa com limites de recursos"""
        async with self.semaphore:
            agent_id = str(uuid.uuid4())
            self.active_agents[agent_id] = time.time()
            
            try:
                result = await agent_func(*args)
                return result
            finally:
                del self.active_agents[agent_id]
```

## 📊 Quality Metrics

### Agent Performance Tracking
```python
@dataclass
class AgentMetrics:
    agent_id: str
    focus_area: str
    execution_time: float
    success_rate: float
    relevance_score: float
    documents_found: int
    
    def quality_score(self) -> float:
        """Pontuação de qualidade do agente"""
        return (
            self.success_rate * 0.4 +
            self.relevance_score * 0.4 + 
            min(1.0, self.documents_found / 5) * 0.2
        )
```

### Synthesis Quality Assessment
```python
class SynthesisQualityAssessor:
    def assess_synthesis(self, synthesis: str, subagent_results: List[str]):
        """Avalia qualidade da síntese final"""
        
        metrics = {
            "completeness": self._assess_completeness(synthesis, subagent_results),
            "coherence": self._assess_coherence(synthesis),
            "insight_generation": self._assess_insights(synthesis),
            "contradiction_handling": self._assess_contradictions(synthesis)
        }
        
        return sum(metrics.values()) / len(metrics)
```

## 🔄 Error Handling & Fallbacks

### Agent Failure Recovery
```python
async def execute_with_fallback(self, tasks):
    """Execução com recovery automático"""
    
    primary_results = await self._try_parallel_execution(tasks)
    
    # Identificar falhas
    failed_tasks = [
        task for task, result in zip(tasks, primary_results)
        if isinstance(result, Exception)
    ]
    
    if failed_tasks:
        # Retry com timeout maior
        recovery_results = await self._retry_failed_tasks(
            failed_tasks, timeout_multiplier=1.5
        )
        
        # Merge resultados
        final_results = self._merge_results(primary_results, recovery_results)
    else:
        final_results = primary_results
    
    return final_results
```

### Quality Degradation Graceful
```python
def _ensure_minimum_quality(self, results):
    """Garante qualidade mínima mesmo com falhas"""
    
    successful_results = [r for r in results if not isinstance(r, Exception)]
    
    if len(successful_results) == 0:
        # Emergency fallback to simple RAG
        return self._emergency_simple_search()
    elif len(successful_results) < 2:
        # Supplement with general search
        general_result = self._supplement_with_general_search()
        successful_results.append(general_result)
    
    return successful_results
```

---

## 📚 Links Relacionados

- [🏛️ Arquitetura Geral](architecture.md) - Visão completa do sistema
- [🔍 ReAct Reasoning](reasoning.md) - Padrão de raciocínio dos agentes  
- [📊 Pipeline RAG](rag-pipeline.md) - Sistema de retrieval
- [⚡ Performance](performance.md) - Otimizações e métricas
- [🔧 Troubleshooting](troubleshooting.md) - Resolução de problemas