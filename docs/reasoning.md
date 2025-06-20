# 🔍 ReAct Reasoning Pattern

## 🎯 Conceito Fundamental

O sistema implementa o padrão **ReAct (Reasoning + Acting)** como substituto ao sistema "thinking" tradicional, fornecendo raciocínio estruturado e validação contínua durante todo o processo de pesquisa.

## 🧠 Filosofia do ReAct

### Tradicional "Thinking" vs ReAct Reasoning

| Aspecto | Thinking Tradicional | ReAct Reasoning |
|---------|---------------------|-----------------|
| **Estrutura** | Texto livre, narrativo | Categorizado e estruturado |
| **Validação** | Manual/externa | Automática e contínua |
| **Observações** | Implícitas | Explícitas com next actions |
| **Integração** | Separado do sistema | Integrado no fluxo de execução |
| **Feedback** | Estático | Dinâmico com ajustes |
| **Rastreabilidade** | Limitada | Trace completo e estruturado |

## 🔄 As 5 Fases do ReAct

### 1. 🔍 Fact Gathering
**Objetivo**: Estabelecer base sólida de conhecimento para fundamentar decisões

```python
class FactGathering(BaseModel):
    given_facts: List[str]      # Fatos explicitamente fornecidos
    recalled_facts: List[str]   # Conhecimento do sistema/domínio
    assumptions: List[str]      # Suposições bem fundamentadas

def gather_facts(self, task: str, context: str) -> FactGathering:
    """Coleta sistemática de fatos"""
    
    # Análise da query para extrair fatos dados
    given_facts = self._extract_given_facts(task, context)
    
    # Recall de conhecimento relevante do domínio
    recalled_facts = self._recall_domain_knowledge(task)
    
    # Formulação de assumptions baseadas em análise
    assumptions = self._formulate_assumptions(task, context)
    
    return FactGathering(
        given_facts=given_facts,
        recalled_facts=recalled_facts, 
        assumptions=assumptions
    )
```

**Exemplo Prático**:
```python
# Para query: "Como Zep implementa temporal knowledge graphs?"
facts = FactGathering(
    given_facts=[
        "Query focuses on Zep implementation",
        "Specific interest in temporal knowledge graphs",
        "Technical implementation details requested"
    ],
    recalled_facts=[
        "Zep is a memory system for AI agents",
        "Knowledge graphs structure relational data",
        "Temporal aspects involve time-based relationships"
    ],
    assumptions=[
        "User has basic understanding of knowledge graphs",
        "Implementation details from documentation will be most valuable",
        "Comparison with other systems may provide context"
    ]
)
```

### 2. 📋 Planning
**Objetivo**: Criar estratégia estruturada baseada nos fatos coletados

```python
class TaskPlan(BaseModel):
    objective: str
    steps: List[str]
    expected_outcome: str
    resources_needed: List[str]

def create_plan(self, objective: str, available_resources: List[str]) -> TaskPlan:
    """Planejamento estratégico estruturado"""
    
    plan = TaskPlan(
        objective=objective,
        steps=self._break_down_into_steps(objective),
        expected_outcome=self._define_success_criteria(objective),
        resources_needed=available_resources
    )
    
    # Log reasoning step
    self.add_reasoning_step(
        "planning",
        f"Created plan for: {objective}",
        f"Steps: {len(plan.steps)}, Resources: {len(plan.resources_needed)}",
        "Execute first step of the plan"
    )
    
    return plan
```

**Exemplo de Plan Gerado**:
```python
plan = TaskPlan(
    objective="Create comprehensive research plan for Zep temporal KG implementation",
    steps=[
        "Decompose query into specialized research areas",
        "Assign focus areas based on query analysis", 
        "Execute parallel subagent searches",
        "Synthesize findings with critical analysis"
    ],
    expected_outcome="Structured technical report with implementation details",
    resources_needed=["OpenAI gpt-4.1-mini", "RAG subagents", "Document search capabilities"]
)
```

### 3. ⚡ Execution
**Objetivo**: Executar ações planejadas com monitoramento contínuo

```python
def execute_step(self, step_description: str, action_taken: str, result: str) -> ReasoningStep:
    """Execução monitorada com logging estruturado"""
    
    step = self.add_reasoning_step(
        "execution",
        f"Executing: {step_description}",
        f"Action: {action_taken}\nResult: {result}",
        "Evaluate result and determine next step"
    )
    
    self.iteration_count += 1
    return step
```

**Exemplo de Execution Trace**:
```python
# Step 1
execute_step(
    "Decompose query into specialized tasks",
    "LLM analysis with focus area selection",
    "Generated 3 tasks: conceptual, technical, comparative"
)

# Step 2  
execute_step(
    "Execute parallel subagent searches", 
    "Launched 3 RAG subagents simultaneously",
    "All 3 subagents completed successfully in 4.2s"
)

# Step 3
execute_step(
    "Synthesize results with advanced AI",
    "GPT-4.1 critical analysis of all findings",
    "Generated comprehensive synthesis with cross-references"
)
```

### 4. ✅ Validation
**Objetivo**: Verificar progresso e detectar problemas automaticamente

```python
class ValidationResult(BaseModel):
    is_task_completed: bool
    is_in_loop: bool
    progress_summary: str
    next_instruction: Optional[str]
    confidence_level: float

def validate_progress(self, original_task: str) -> ValidationResult:
    """Validação automática do progresso"""
    
    # Análise de completude
    is_completed = self._assess_task_completion(original_task)
    
    # Detecção de loops de raciocínio
    is_in_loop = self._detect_reasoning_loop()
    
    # Cálculo de confiança baseado em métricas
    confidence = self._calculate_confidence()
    
    # Determinação da próxima ação
    next_instruction = None if is_completed else self._determine_next_action()
    
    validation = ValidationResult(
        is_task_completed=is_completed,
        is_in_loop=is_in_loop,
        progress_summary=self._summarize_progress(),
        next_instruction=next_instruction,
        confidence_level=confidence
    )
    
    return validation
```

**Algoritmos de Detecção**:
```python
def _detect_reasoning_loop(self) -> bool:
    """Detecta padrões repetitivos no reasoning"""
    
    if len(self.reasoning_history) < 4:
        return False
    
    # Analisa últimos 4 steps
    recent_steps = self.reasoning_history[-4:]
    step_types = [s.step_type for s in recent_steps]
    
    # Loop detectado se muita repetição
    return len(set(step_types)) <= 2 and self.iteration_count > 3

def _calculate_confidence(self) -> float:
    """Calcula nível de confiança baseado em progresso"""
    
    execution_steps = len([s for s in self.reasoning_history if s.step_type == "execution"])
    validation_steps = len([s for s in self.reasoning_history if s.step_type == "validation"])
    reflection_steps = len([s for s in self.reasoning_history if s.step_type == "reflection"])
    
    # Fatores positivos
    base_confidence = min(1.0, (execution_steps * 0.3 + validation_steps * 0.2))
    
    # Penalidades
    loop_penalty = 0.3 if self._detect_reasoning_loop() else 0.0
    reflection_penalty = reflection_steps * 0.1
    
    return max(0.0, base_confidence - loop_penalty - reflection_penalty)
```

### 5. 🔄 Reflection & Adjustment
**Objetivo**: Aprender com erros e ajustar estratégia dinamicamente

```python
def reflect_and_adjust(self, what_went_wrong: str) -> TaskPlan:
    """Reflexão crítica e ajuste de estratégia"""
    
    self.add_reasoning_step(
        "reflection",
        f"Reflecting on issues: {what_went_wrong}",
        "Analyzing failures and adjusting approach",
        "Recreate improved plan"
    )
    
    # Atualiza assumptions baseado no que aprendeu
    if "timeout" in what_went_wrong.lower():
        self._adjust_timeout_assumptions()
    elif "no results" in what_went_wrong.lower():
        self._adjust_search_strategy()
    
    # Gera novo plano melhorado
    improved_plan = self._create_improved_plan(what_went_wrong)
    
    return improved_plan
```

## 🔗 Integração com Sistema Multi-Agente

### ReAct no Lead Researcher
```python
class OpenAILeadResearcher:
    def __init__(self):
        self.reasoner = ReActReasoner(f"OpenAI Lead Researcher ({self.agent_id})")
    
    async def plan(self, context: AgentContext):
        """Planning com ReAct reasoning"""
        
        # 1. Fact gathering
        facts = self.reasoner.gather_facts(
            task=f"Research planning for: {context.query}",
            context=f"Objective: {context.objective}"
        )
        
        # 2. Enhanced reasoning com análise crítica
        facts.assumptions = self._create_sophisticated_assumptions(context.query)
        
        # 3. Planning
        plan = self.reasoner.create_plan(
            objective=f"Create comprehensive research plan for: {context.query}",
            available_resources=["OpenAI gpt-4.1-mini", "RAG subagents"]
        )
        
        # 4. Execute planning (LLM ou heuristic)
        return await self._execute_planning_with_reasoning(context, facts, plan)
```

### Continuidade na Síntese
```python
def _advanced_ai_synthesis(self, tasks, successful_results):
    """Síntese que continua o reasoning inicial"""
    
    # Integra trace completo do reasoning
    reasoning_trace = self.reasoner.get_reasoning_trace()
    
    synthesis_prompt = f"""
    CONTEXTO DO PROCESSO DE REASONING:
    {reasoning_trace}
    
    INSTRUÇÕES PARA SÍNTESE CRÍTICA AVANÇADA:
    1. **Continuidade do Reasoning**: Continue o processo iniciado no planejamento
    2. **Validação Crítica**: Avalie consistência baseado no reasoning trace  
    3. **Reflexão sobre o Processo**: Avalie se resultados confirmam assumptions iniciais
    4. **Gaps e Limitações**: Identifique lacunas baseado no planejado vs encontrado
    
    Produza síntese que demonstre continuidade e evolução do reasoning inicial.
    """
    
    # Final validation
    validation = self.reasoner.validate_progress(f"Synthesis for: {tasks[0]['query']}")
    
    return synthesized_result
```

## 📊 Trace Visualization

### Reasoning Trace Format
```python
def get_reasoning_trace(self) -> str:
    """Gera trace legível do processo completo"""
    
    trace = f"=== Trace de Raciocínio - {self.agent_name} ===\n\n"
    
    for i, step in enumerate(self.reasoning_history, 1):
        trace += f"🔍 Passo {i}: {step.step_type.upper()}\n"
        trace += f"⏰ {step.timestamp.strftime('%H:%M:%S')}\n"
        trace += f"💭 {step.content}\n"
        
        if step.observations:
            trace += f"👁️ Observações: {step.observations}\n"
        
        if step.next_action:
            trace += f"➡️ Próxima ação: {step.next_action}\n"
        
        trace += "\n" + "─" * 50 + "\n\n"
    
    return trace
```

**Exemplo de Trace**:
```
=== Trace de Raciocínio - OpenAI Lead Researcher (abc-123) ===

🔍 Passo 1: FACT_GATHERING
⏰ 14:32:15
💭 Coletando fatos para: Research planning for Zep temporal knowledge graphs
👁️ Observações: Query complexity: high, Technical depth: high
➡️ Próxima ação: Analisar fatos dados e relembrar conhecimento relevante

──────────────────────────────────────────────────

🔍 Passo 2: PLANNING  
⏰ 14:32:16
💭 Criando plano para: Create comprehensive research plan for Zep temporal KG
👁️ Observações: Recursos disponíveis: ['OpenAI gpt-4.1-mini', 'RAG subagents']
➡️ Próxima ação: Desenvolver plano estruturado em etapas

──────────────────────────────────────────────────

🔍 Passo 3: EXECUTION
⏰ 14:32:17  
💭 Executando: LLM-based decomposition informed by ReAct reasoning
👁️ Observações: Integrating manual reasoning with gpt-4.1-mini for optimal focus area selection
➡️ Próxima ação: Avaliar resultado e determinar próximo passo
```

## 🎯 Benefits do ReAct Pattern

### 1. **Structured Thinking**
- **Antes**: Pensamento livre e não estruturado
- **Depois**: Categorias claras (fact gathering, planning, execution, validation, reflection)

### 2. **Continuous Validation**
- **Antes**: Validação manual ao final
- **Depois**: Validação automática a cada step com métricas de confiança

### 3. **Loop Detection**
- **Antes**: Loops passavam despercebidos
- **Depois**: Detecção automática e ajuste de estratégia

### 4. **Traceability**
- **Antes**: Difícil rastrear como decisões foram tomadas
- **Depois**: Trace completo de todo o processo de reasoning

### 5. **Dynamic Adjustment**
- **Antes**: Estratégia fixa durante execução
- **Depois**: Ajustes dinâmicos baseados em feedback

## 🔧 Configuration & Tuning

### Reasoning Parameters
```python
class ReActConfig:
    max_iterations: int = 10
    confidence_threshold: float = 0.7
    loop_detection_window: int = 4
    reflection_trigger_threshold: int = 3
    
    # Timeouts
    step_timeout: float = 30.0
    total_reasoning_timeout: float = 300.0
    
    # Quality metrics
    min_execution_steps: int = 1
    min_confidence_for_completion: float = 0.5
```

### Customization Points
```python
class CustomReActReasoner(ReActReasoner):
    def _assess_task_completion(self, original_task: str) -> bool:
        """Custom completion assessment"""
        # Domain-specific completion logic
        return super()._assess_task_completion(original_task)
    
    def _determine_next_action(self) -> Optional[str]:
        """Custom action determination"""
        # Domain-specific next action logic
        return super()._determine_next_action()
```

---

## 📚 Links Relacionados

- [🤖 Sistema Multi-Agente](multi-agent.md) - Como ReAct se integra com agentes
- [🏛️ Arquitetura](architecture.md) - Visão geral do sistema
- [📊 Pipeline RAG](rag-pipeline.md) - RAG com reasoning  
- [⚡ Performance](performance.md) - Impacto do reasoning na performance
- [🔧 Troubleshooting](troubleshooting.md) - Debug de reasoning issues