"""OpenAI-based lead researcher with ReAct reasoning pattern."""

import asyncio
import uuid
import sys
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))
from src.core.config import SystemConfig

# Load environment variables from project root
from dotenv import load_dotenv, find_dotenv

# Find and load .env file from any parent directory
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)
    print(f"✅ Loaded .env from: {env_file}")
else:
    print("⚠️ No .env file found in parent directories")

from researcher.agents.base import Agent, AgentContext, AgentResult, AgentState
from researcher.agents.document_search_agent import RAGResearchSubagent, RAGSubagentConfig
from researcher.reasoning.react_reasoning import ReActReasoner, ValidationResult
from researcher.reasoning.react_prompts import ReActPrompts
from pydantic import BaseModel

# OpenAI imports
try:
    import openai
    from openai import AsyncOpenAI
    import instructor
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configuração centralizada
system_config = SystemConfig()


class OpenAILeadConfig(BaseModel):
    """Configuration for OpenAI-powered lead researcher."""
    max_subagents: int = system_config.multiagent.max_subagents
    parallel_execution: bool = system_config.multiagent.parallel_execution
    model: str = system_config.multiagent.model
    api_key: Optional[str] = None
    use_llm_decomposition: bool = system_config.multiagent.use_llm_decomposition
    max_tokens: int = system_config.multiagent.max_tokens
    subagent_timeout: float = system_config.multiagent.subagent_timeout

    @classmethod
    def from_env(cls) -> "OpenAILeadConfig":
        """Create config from environment variables using centralized system config."""
        return cls(
            max_subagents=system_config.multiagent.max_subagents,
            parallel_execution=system_config.multiagent.parallel_execution,
            model=system_config.multiagent.model,
            api_key=system_config.multiagent.openai_api_key,
            use_llm_decomposition=system_config.multiagent.use_llm_decomposition,
            max_tokens=system_config.multiagent.max_tokens,
            subagent_timeout=system_config.multiagent.subagent_timeout
        )


class QueryDecomposition(BaseModel):
    """Structured query decomposition using Instructor."""
    reasoning: str
    complexity: str  # "simple", "moderate", "complex" 
    number_of_subagents: int
    subagent_tasks: List[Dict[str, Any]]  # Required field - LLM must provide tasks


class OpenAILeadResearcher(Agent[str]):
    """
    OpenAI-powered lead researcher using ReAct reasoning pattern.
    Uses structured reasoning instead of simple "thinking" chains.
    """
    
    def __init__(
        self,
        config: Optional[OpenAILeadConfig] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.config = config or OpenAILeadConfig()
        self.subagents: List[RAGResearchSubagent] = []
        self.client = None
        self.reasoner = ReActReasoner(f"OpenAI Lead Researcher ({self.agent_id})")
        
        # Initialize OpenAI client for both decomposition AND synthesis
        if OPENAI_AVAILABLE:
            api_key = self.config.api_key
            if api_key:
                try:
                    base_client = AsyncOpenAI(api_key=api_key)
                    self.client = instructor.from_openai(base_client)
                    self.reasoner.add_reasoning_step(
                        "initialization",
                        f"✅ OpenAI client initialized for decomposition and synthesis",
                        f"Models: decomposition={self.config.model}, coordinator={system_config.rag.coordinator_model}"
                    )
                except Exception as e:
                    self.reasoner.add_reasoning_step(
                        "initialization",
                        f"❌ Failed to initialize OpenAI client: {e}",
                        "Will use fallback methods"
                    )
                    self.client = None
            else:
                self.reasoner.add_reasoning_step(
                    "initialization",
                    "⚠️ No OpenAI API key found",
                    "Cannot use advanced synthesis"
                )
                self.client = None
        else:
            self.reasoner.add_reasoning_step(
                "initialization",
                "⚠️ OpenAI/instructor not available",
                "Cannot use advanced synthesis"
            )
            self.client = None

    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Create research plan using ReAct reasoning pattern."""
        # Fact gathering phase
        facts = self.reasoner.gather_facts(
            task=f"Research planning for: {context.query}",
            context=f"Objective: {context.objective}\nConstraints: {', '.join(context.constraints) if context.constraints else 'None'}"
        )
        
        # Add facts about the query
        facts.given_facts = [
            f"Query: {context.query}",
            f"Objective: {context.objective}",
            f"Available constraints: {len(context.constraints) if context.constraints else 0}"
        ]
        
        # Enhanced reasoning with critical analysis from the start
        facts.recalled_facts = [
            "RAG systems work best with specific, focused queries",
            "Multiple perspectives improve research completeness and reduce bias",
            f"Maximum {self.config.max_subagents} subagents available for parallel investigation",
            "Parallel execution can speed up research" if self.config.parallel_execution else "Sequential execution is more reliable",
            "Focus area specialization improves query precision and result relevance",
            "Cross-referencing between different focus areas reveals connections and contradictions",
            "Document-based evidence provides more reliable foundation than web search"
        ]
        
        # More sophisticated assumptions based on query analysis
        query_lower = context.query.lower()
        facts.assumptions = [
            "Query requires multi-faceted investigation to avoid incomplete analysis",
            "Document search will be the primary research method for evidence-based findings",
            "Different focus areas will yield complementary and potentially contradictory results",
            f"Query complexity level: {'high' if len(context.query.split()) > 10 else 'moderate' if len(context.query.split()) > 5 else 'low'}",
            f"Technical depth expected: {'high' if any(tech in query_lower for tech in ['implement', 'algorithm', 'architecture']) else 'moderate'}",
            f"Conceptual clarity needed: {'high' if any(concept in query_lower for concept in ['what is', 'define', 'explain']) else 'moderate'}",
            "Results will require critical evaluation for consistency and reliability"
        ]
        
        # Planning phase
        team_capabilities = f"""
RAG Research Subagents: Can search and analyze documents for specific topics
- Maximum concurrent agents: {self.config.max_subagents}
- Execution mode: {'Parallel' if self.config.parallel_execution else 'Sequential'}
- LLM decomposition: {'Available' if self.client else 'Not available'}
"""
        
        plan = self.reasoner.create_plan(
            objective=f"Create comprehensive research plan for: {context.query}",
            available_resources=[
                f"OpenAI {self.config.model}" if self.client else "Heuristic decomposition",
                "RAG subagents",
                "Document search capabilities"
            ]
        )
        
        # Use LLM decomposition if client available AND enabled
        if self.client and self.config.use_llm_decomposition:
            return await self._plan_with_llm(context, facts, plan)
        else:
            # Use heuristic decomposition (but client will still be available for synthesis)
            return await self._plan_heuristic(context, facts, plan)
    
    async def _plan_with_llm(self, context: AgentContext, facts, plan) -> List[Dict[str, Any]]:
        """Plan using OpenAI GPT-4o mini with ReAct reasoning."""
        
        self.reasoner.add_reasoning_step(
            "planning",
            "Using LLM-based decomposition informed by ReAct reasoning",
            f"Integrating manual reasoning with {self.config.model} for optimal focus area selection"
        )

        system_prompt = """You are an expert research coordinator. Analyze the given query and decompose it into specific tasks for specialized RAG (document search) subagents.

🎯 AVAILABLE FOCUS AREAS (choose the most relevant for each task):

• **conceptual**: Definitions, concepts, fundamentals, theoretical foundations
  → Use when: user asks "what is", needs basic understanding, theoretical background

• **technical**: Implementation details, architecture, algorithms, how-to guides
  → Use when: user wants to implement, needs technical specifics, code examples

• **comparative**: Comparisons, differences, advantages/disadvantages, alternatives
  → Use when: user asks "vs", "difference", "better than", needs evaluation

• **examples**: Use cases, case studies, practical examples, demonstrations
  → Use when: user wants concrete examples, real-world applications, proof of concept

• **overview**: General introduction, broad survey, comprehensive summary
  → Use when: user needs general understanding, broad perspective, getting started

• **applications**: Practical applications, real-world usage, industry implementations
  → Use when: user wants to know practical uses, business applications, deployment

• **general**: Broad, comprehensive research without specific focus
  → Use when: query is very general or doesn't fit other categories

STRATEGY: Choose 2-4 complementary focus areas that together provide comprehensive coverage of the query.

Consider:
1. What are the key aspects that need investigation?
2. Which focus areas best complement each other for this query?
3. What search strategies would be most effective?
4. How many subagents are needed (1-5)?

CRITICAL: You MUST provide a complete response with ALL required fields. The subagent_tasks list cannot be empty.

Required JSON structure:
{
  "reasoning": "Explanation of your decomposition strategy and why you chose these specific focus areas",
  "complexity": "simple|moderate|complex",
  "number_of_subagents": <number>,
  "subagent_tasks": [
    {
      "query": "specific search query for documents",
      "objective": "what this search should accomplish",
      "focus": "conceptual|technical|comparative|examples|overview|applications|general"
    }
  ]
}

IMPORTANT: The number of items in subagent_tasks MUST match number_of_subagents. Create diverse, complementary search tasks using different focus areas."""

        # Integrate ReAct reasoning with LLM prompt
        reasoning_context = f"""
REACT REASONING ANALYSIS:
Given Facts: {', '.join(facts.given_facts)}
Recalled Facts: {', '.join(facts.recalled_facts)}
Assumptions: {', '.join(facts.assumptions)}
Planned Approach: {plan.objective if plan else 'No specific plan'}
Available Resources: {', '.join(plan.resources_needed) if plan and plan.resources_needed else 'Standard RAG capabilities'}
"""

        user_prompt = f"""
Query: {context.query}
Objective: {context.objective}
Constraints: {', '.join(context.constraints) if context.constraints else 'None'}

{reasoning_context}

Based on the ReAct reasoning analysis above, decompose this into specific research tasks for document search agents. Each task should focus on a different aspect or angle of the query, taking into account the facts, assumptions, and planned approach identified.

Choose focus areas that complement the reasoning analysis and provide comprehensive coverage.

Return the decomposition in the exact JSON format specified in the system prompt.
"""

        try:
            print(f"🔧 [DEBUG] Starting LLM decomposition for query: {context.query}")
            print(f"🔧 [DEBUG] LLM client available: {self.client is not None}")
            self.reasoner.add_reasoning_step(
                "execution",
                "Executing LLM-based query decomposition",
                f"Sending request to {self.config.model}"
            )
            
            print(f"🔧 [DEBUG] Calling OpenAI with model: {self.config.model}")
            decomposition = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=QueryDecomposition
            )
            print(f"🔧 [DEBUG] LLM response received: {decomposition}")
            
            self.reasoner.add_reasoning_step(
                "execution",
                f"✅ LLM decomposition successful: {decomposition.complexity} complexity, {decomposition.number_of_subagents} subagents",
                f"Reasoning: {decomposition.reasoning}"
            )
            
            # Limit subagents to config max
            tasks = decomposition.subagent_tasks[:self.config.max_subagents]
            
            print(f"🔧 [DEBUG] LLM plan returning {len(tasks)} tasks: {tasks}")
            return tasks
            
        except Exception as e:
            self.reasoner.add_reasoning_step(
                "execution",
                f"❌ LLM decomposition failed: {e}",
                "Falling back to heuristic decomposition"
            )
            return await self._plan_heuristic(context, facts, plan)
    
    async def _plan_heuristic(self, context: AgentContext, facts, plan) -> List[Dict[str, Any]]:
        """Fallback heuristic-based planning with ReAct reasoning."""
        
        self.reasoner.add_reasoning_step(
            "planning",
            "Using heuristic decomposition informed by ReAct reasoning",
            f"LLM not available, using rule-based approach with {len(facts.given_facts)} facts and {len(facts.assumptions)} assumptions"
        )
        
        # Base task
        tasks = [{
            "query": context.query,
            "objective": f"General research: {context.objective}",
            "focus": "overview"
        }]
        
        # Technical details if technical keywords present
        technical_keywords = ["algorithm", "implementation", "architecture", "system", "method", "technique", "model", "framework"]
        if any(keyword in context.query.lower() for keyword in technical_keywords):
            tasks.append({
                "query": f"{context.query} technical details implementation",
                "objective": f"Technical analysis: {context.objective}",
                "focus": "technical"
            })
        
        # Applications and examples
        if len(tasks) < self.config.max_subagents:
            tasks.append({
                "query": f"{context.query} applications examples use cases",
                "objective": f"Practical applications: {context.objective}",
                "focus": "applications"
            })
        
        self.reasoner.add_reasoning_step(
            "planning",
            f"📝 Heuristic decomposition created {len(tasks)} tasks",
            f"Tasks: {[task.get('focus', 'general') for task in tasks]}"
        )
        print(f"🔧 [DEBUG] Heuristic plan returning {len(tasks)} tasks: {tasks}")
        return tasks
    
    async def execute(self, plan: List[Dict[str, Any]]) -> str:
        """Execute research plan with RAG subagents."""
        print(f"🔧 [DEBUG] Execute called with plan length: {len(plan)}")
        print(f"🔧 [DEBUG] Plan contents: {plan}")
        
        self.reasoner.add_reasoning_step(
            "execution",
            f"🚀 Executing {len(plan)} research tasks",
            f"Execution mode: {'Parallel' if self.config.parallel_execution else 'Sequential'}"
        )
        
        if self.config.parallel_execution:
            results = await self._execute_parallel(plan)
        else:
            results = await self._execute_sequential(plan)
        
        # Synthesize results
        synthesis = self._synthesize_results(plan, results)
        return synthesis
    
    async def _execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[AgentResult]:
        """Execute subagents in parallel."""
        coroutines = []
        
        for i, task in enumerate(tasks):
            # Create RAG subagent
            subagent = RAGResearchSubagent(
                agent_id=str(uuid.uuid4()),
                name=f"RAG-Agent-{i+1}"
            )
            
            # Inject RAG system if available
            if hasattr(self, 'rag_system') and self.rag_system:
                print(f"🔧 [DEBUG] Lead Researcher injecting RAG into subagent: {type(self.rag_system).__name__}")
                subagent.rag_tool.set_rag_system(self.rag_system)
            elif hasattr(self, 'inject_rag_to_subagent'):
                print(f"🔧 [DEBUG] Using external RAG injection method")
                self.inject_rag_to_subagent(subagent)
            else:
                print(f"🔧 [DEBUG] Lead Researcher has no RAG system to inject. Has rag_system attr: {hasattr(self, 'rag_system')}, Value: {getattr(self, 'rag_system', None)}")
            
            self.subagents.append(subagent)
            
            # Create context
            context = AgentContext(
                query=task["query"],
                objective=task["objective"],
                metadata={"focus": task.get("focus", "general")}
            )
            
            # Add to parallel execution
            coroutines.append(
                asyncio.wait_for(
                    subagent.run(context),
                    timeout=self.config.subagent_timeout
                )
            )
        
        # Execute all in parallel
        try:
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.reasoner.add_reasoning_step(
                        "execution",
                        f"❌ Subagent {i+1} failed: {result}",
                        "Subagent execution error in parallel mode"
                    )
                    processed_results.append(AgentResult(
                        agent_id=f"failed-{i}",
                        status=AgentState.FAILED,
                        error=str(result),
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow()
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            self.reasoner.add_reasoning_step(
                "execution",
                f"❌ Parallel execution failed: {e}",
                "Falling back to sequential execution"
            )
            return []
    
    async def _execute_sequential(self, tasks: List[Dict[str, Any]]) -> List[AgentResult]:
        """Execute subagents sequentially."""
        results = []
        
        for i, task in enumerate(tasks):
            self.reasoner.add_reasoning_step(
                "execution",
                f"🔄 Executing task {i+1}/{len(tasks)}: {task.get('focus', 'general')}",
                f"Task details: {task}"
            )
            
            # Create RAG subagent
            subagent = RAGResearchSubagent(
                agent_id=str(uuid.uuid4()),
                name=f"RAG-Agent-{i+1}"
            )
            
            # Inject RAG system if available
            if hasattr(self, 'rag_system') and self.rag_system:
                print(f"🔧 [DEBUG] Lead Researcher injecting RAG into subagent: {type(self.rag_system).__name__}")
                subagent.rag_tool.set_rag_system(self.rag_system)
            elif hasattr(self, 'inject_rag_to_subagent'):
                print(f"🔧 [DEBUG] Using external RAG injection method")
                self.inject_rag_to_subagent(subagent)
            else:
                print(f"🔧 [DEBUG] Lead Researcher has no RAG system to inject. Has rag_system attr: {hasattr(self, 'rag_system')}, Value: {getattr(self, 'rag_system', None)}")
            
            self.subagents.append(subagent)
            
            # Create context
            context = AgentContext(
                query=task["query"],
                objective=task["objective"],
                metadata={"focus": task.get("focus", "general")}
            )
            
            # Execute
            try:
                result = await asyncio.wait_for(
                    subagent.run(context),
                    timeout=self.config.subagent_timeout
                )
                results.append(result)
                self.reasoner.add_reasoning_step(
                    "execution",
                    f"✅ Task {i+1} completed: {result.status.name}",
                    f"Result summary: {result.result[:100] if result.result else 'No content'}..."
                )
                
            except asyncio.TimeoutError:
                self.reasoner.add_reasoning_step(
                    "execution",
                    f"⏰ Task {i+1} timed out after {self.config.subagent_timeout}s",
                    "Task exceeded timeout limit"
                )
                results.append(AgentResult(
                    agent_id=f"timeout-{i}",
                    status=AgentState.FAILED,
                    error=f"Timeout after {self.config.subagent_timeout}s",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow()
                ))
            except Exception as e:
                self.reasoner.add_reasoning_step(
                    "execution",
                    f"❌ Task {i+1} failed: {e}",
                    "Unexpected error during task execution"
                )
                results.append(AgentResult(
                    agent_id=f"error-{i}",
                    status=AgentState.FAILED,
                    error=str(e),
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow()
                ))
        
        return results
    
    def _synthesize_results(self, tasks: List[Dict[str, Any]], results: List[AgentResult]) -> str:
        """Synthesize results from multiple RAG subagents using advanced coordinator model."""
        successful_results = [r for r in results if r.status == AgentState.COMPLETED and r.output]
        
        if not successful_results:
            return "❌ No results obtained from RAG research. Check if documents are indexed."
        
        # ALWAYS try advanced AI synthesis using coordinator model (gpt-4.1)
        if self.client and successful_results:
            try:
                return self._advanced_ai_synthesis(tasks, successful_results)
            except Exception as e:
                self.reasoner.add_reasoning_step(
                    "synthesis",
                    f"❌ Advanced AI synthesis failed: {e}",
                    "Error will be raised - coordinator must use gpt-4.1"
                )
                # Re-raise the exception to ensure we don't fallback
                raise Exception(f"Coordinator synthesis failed: {e}")
        
        # Only fallback if no client available (configuration error)
        if not self.client:
            self.reasoner.add_reasoning_step(
                "synthesis",
                "⚠️ No OpenAI client available for advanced synthesis",
                "Using basic synthesis as emergency fallback"
            )
        
        return self._basic_synthesis(tasks, results, successful_results)
    
    def _advanced_ai_synthesis(self, tasks: List[Dict[str, Any]], successful_results: List[AgentResult]) -> str:
        """Advanced AI-powered synthesis using coordinator model (gpt-4.1)."""
        coordinator_model = system_config.rag.coordinator_model
        
        # Prepare subagent findings for analysis
        findings_summary = []
        for i, (task, result) in enumerate(zip(tasks, successful_results)):
            findings_summary.append({
                "task_focus": task.get('focus', 'general'),
                "query": task['query'],
                "findings": result.output[:2000]  # Limit for token management
            })
        
        # Integrate ReAct reasoning trace with synthesis
        reasoning_trace = self.reasoner.get_reasoning_trace()
        
        synthesis_prompt = f"""Como coordenador de pesquisa AI, analise criticamente os resultados dos subagentes e sintetize uma resposta final abrangente e estruturada.

CONTEXTO DO PROCESSO DE REASONING:
{reasoning_trace}

RESULTADOS DOS SUBAGENTES:
{chr(10).join([f"### {f['task_focus'].title()}: {f['query']}{chr(10)}{f['findings']}{chr(10)}" for f in findings_summary])}

INSTRUÇÕES PARA SÍNTESE CRÍTICA AVANÇADA:
1. **Continuidade do Reasoning**: Continue o processo de raciocínio iniciado no planejamento, mantendo consistência lógica
2. **Análise Cross-Reference**: Identifique conexões, contradições e padrões entre os achados
3. **Validação Crítica**: Avalie a consistência e confiabilidade das informações baseado no reasoning trace
4. **Síntese Estruturada**: Organize em seções lógicas que reflitam o desenvolvimento do reasoning
5. **Insights Originais**: Derive conclusões que não estão explícitas, mas são logicamente consistentes com o reasoning inicial
6. **Reflexão sobre o Processo**: Avalie se os resultados confirmam ou contradizem as assumptions iniciais
7. **Gaps e Limitações**: Identifique lacunas baseado no que foi planejado vs. o que foi encontrado

FORMATO DA RESPOSTA:
- Use markdown estruturado com headers (##, ###)
- Inclua seções: Resumo Executivo, Achados Principais, Análise Crítica, Validação do Reasoning, Conclusões
- Cite evidências específicas dos subagentes
- Referencie o reasoning trace quando relevante
- Mantenha tom profissional e acadêmico

Produza uma síntese que demonstre continuidade e evolução do reasoning inicial, integrando pensamento crítico avançado."""

        try:
            self.reasoner.add_reasoning_step(
                "synthesis",
                f"🧠 Executing advanced synthesis with {coordinator_model}",
                f"Processing {len(successful_results)} subagent results"
            )
            
            # Create a separate OpenAI client for synthesis (synchronous)
            from openai import OpenAI
            sync_client = OpenAI(api_key=self.api_key)
            response = sync_client.chat.completions.create(
                model=coordinator_model,
                messages=[{"role": "user", "content": synthesis_prompt}],
                max_tokens=system_config.rag.max_tokens,
                temperature=system_config.rag.temperature
            )
            
            synthesized_content = response.choices[0].message.content.strip()
            
            # Add metadata header
            final_report = f"""# 🤖 AI-Coordinated Research Synthesis

**Coordinator Model**: {coordinator_model}
**Synthesis Method**: Advanced AI Critical Analysis
**Subagents Processed**: {len(successful_results)}/{len(tasks)}
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{synthesized_content}

---

## 📊 Research Metadata
- **Decomposition**: {'LLM-based' if self.client else 'Heuristic'}
- **Total Tasks**: {len(tasks)}
- **Success Rate**: {len(successful_results)}/{len(tasks)} ({len(successful_results)/len(tasks)*100:.0f}%)
- **AI Models**: Subagents ({self.config.model}) + Coordinator ({coordinator_model})
"""
            
            # Final reasoning validation
            self.reasoner.add_reasoning_step(
                "synthesis",
                f"✅ Advanced synthesis completed successfully",
                f"Generated {len(synthesized_content)} characters of synthesized content"
            )
            
            # Validate reasoning consistency
            validation = self.reasoner.validate_progress(f"Synthesis for: {tasks[0]['query'] if tasks else 'unknown query'}")
            
            self.reasoner.add_reasoning_step(
                "validation",
                f"🔍 Final reasoning validation: {'Consistent' if not validation.is_in_loop else 'Potential inconsistencies detected'}",
                f"Confidence: {validation.confidence_level:.2f}, Progress: {validation.progress_summary}"
            )
            
            return final_report
            
        except Exception as e:
            self.reasoner.add_reasoning_step(
                "synthesis",
                f"❌ Advanced synthesis failed: {e}",
                "Error in coordinator model processing"
            )
            raise
    
    def _basic_synthesis(self, tasks: List[Dict[str, Any]], results: List[AgentResult], successful_results: List[AgentResult]) -> str:
        """Basic synthesis fallback method."""
        # Build comprehensive report
        report_lines = [
            "# 🤖 OpenAI-Coordinated RAG Research Report",
            "",
            f"**Model**: {self.config.model}",
            f"**Decomposition Method**: {'LLM-based' if self.client else 'Heuristic'}",
            f"**Tasks Executed**: {len(results)}",
            f"**Successful Tasks**: {len(successful_results)}",
            f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Add individual results
        for i, (task, result) in enumerate(zip(tasks, results)):
            if result.status == AgentState.COMPLETED and result.output:
                report_lines.extend([
                    f"## 🎯 Task {i+1}: {task.get('focus', 'General').title()} Analysis",
                    f"**Query**: {task['query']}",
                    f"**Objective**: {task['objective']}",
                    "",
                    result.output,
                    "",
                    "---",
                    ""
                ])
            else:
                report_lines.extend([
                    f"## ❌ Task {i+1}: {task.get('focus', 'General').title()} Analysis",
                    f"**Status**: Failed - {result.error or 'Unknown error'}",
                    "",
                    "---",
                    ""
                ])
        
        # Add synthesis summary
        report_lines.extend([
            "## 📊 Research Summary",
            f"- **Total Subagents**: {len(self.subagents)}",
            f"- **Success Rate**: {len(successful_results)}/{len(results)} ({len(successful_results)/len(results)*100:.0f}%)",
            f"- **Research Method**: Multi-agent RAG coordination",
            f"- **AI Assistance**: {'OpenAI ' + self.config.model if self.client else 'Heuristic-based'}",
            ""
        ])
        
        return "\\n".join(report_lines)
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the complete OpenAI-coordinated research process."""
        self.state = AgentState.PLANNING
        start_time = datetime.utcnow()
        
        # Initialize result
        self._result = AgentResult(
            agent_id=self.agent_id,
            status=self.state,
            start_time=start_time
        )
        
        try:
            self.reasoner.add_reasoning_step(
                "execution",
                f"🚀 Starting OpenAI-coordinated RAG research: '{context.query}'",
                f"Research objective: {context.objective}"
            )
            
            # Planning
            plan = await self.plan(context)
            
            # Execution
            self.state = AgentState.EXECUTING
            self._result.status = self.state
            output = await self.execute(plan)
            
            # Success
            self.state = AgentState.COMPLETED
            self._result.status = AgentState.COMPLETED
            self._result.output = output
            self._result.end_time = datetime.utcnow()
            
            return self._result
            
        except Exception as e:
            self.state = AgentState.FAILED
            self._result.status = AgentState.FAILED
            self._result.error = str(e)
            self._result.end_time = datetime.utcnow()
            self.reasoner.add_reasoning_step(
                "execution",
                f"❌ OpenAI research failed: {e}",
                "Critical error in research process"
            )
            
            return self._result
    
    def get_reasoning_trace(self) -> str:
        """Get the complete reasoning trace from the ReAct reasoner."""
        return self.reasoner.get_reasoning_trace()
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get a summary of the reasoning process."""
        return {
            "total_steps": len(self.reasoner.reasoning_history),
            "step_types": [step.step_type for step in self.reasoner.reasoning_history],
            "iteration_count": self.reasoner.iteration_count,
            "current_facts": self.reasoner.current_facts.model_dump() if self.reasoner.current_facts else None,
            "current_plan": self.reasoner.current_plan.model_dump() if self.reasoner.current_plan else None,
            "confidence": self.reasoner._calculate_confidence()
        }
