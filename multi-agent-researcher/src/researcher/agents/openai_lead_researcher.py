"""OpenAI-based lead researcher with ReAct reasoning pattern."""

import asyncio
import uuid
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))
from config import SystemConfig

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
    subagent_tasks: List[Dict[str, Any]] = []  # Default empty list to prevent validation errors


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
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE and self.config.use_llm_decomposition:
            api_key = self.config.api_key
            if api_key:
                try:
                    base_client = AsyncOpenAI(api_key=api_key)
                    self.client = instructor.from_openai(base_client)
                    self.reasoner.add_reasoning_step(
                        "initialization",
                        f"✅ OpenAI client initialized with model: {self.config.model}",
                        f"API key present: {'Yes' if api_key else 'No'}"
                    )
                except Exception as e:
                    self.reasoner.add_reasoning_step(
                        "initialization",
                        f"❌ Failed to initialize OpenAI client: {e}",
                        "Falling back to heuristic decomposition"
                    )
                    self.client = None
            else:
                self.reasoner.add_reasoning_step(
                    "initialization",
                    "⚠️ No OpenAI API key found",
                    "Using heuristic decomposition instead"
                )
                self.client = None
        else:
            if not OPENAI_AVAILABLE:
                self.reasoner.add_reasoning_step(
                    "initialization",
                    "⚠️ OpenAI/instructor not available",
                    "Using heuristic decomposition"
                )
            else:
                self.reasoner.add_reasoning_step(
                    "initialization",
                    "ℹ️ LLM decomposition disabled",
                    "Using heuristic decomposition"
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
        
        facts.recalled_facts = [
            "RAG systems work best with specific, focused queries",
            "Multiple perspectives improve research completeness",
            f"Maximum {self.config.max_subagents} subagents available",
            "Parallel execution can speed up research" if self.config.parallel_execution else "Sequential execution is more reliable"
        ]
        
        facts.assumptions = [
            "Query requires multi-faceted investigation",
            "Document search will be the primary research method",
            "Different angles will yield complementary results"
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
                "OpenAI GPT-4o mini" if self.client else "Heuristic decomposition",
                "RAG subagents",
                "Document search capabilities"
            ]
        )
        
        if self.client and self.config.use_llm_decomposition:
            return await self._plan_with_llm(context)
        else:
            return await self._plan_heuristic(context)
    
    async def _plan_with_llm(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Plan using OpenAI GPT-4o mini with ReAct reasoning."""
        
        self.reasoner.add_reasoning_step(
            "planning",
            "Using LLM-based decomposition for query planning",
            f"Query complexity requires intelligent analysis using {self.config.model}"
        )

        system_prompt = """You are an expert research coordinator. Analyze the given query and decompose it into specific tasks for RAG (document search) subagents.

Consider:
1. What are the key aspects that need investigation?
2. How can this be divided into independent search tasks?
3. What search strategies would be most effective?
4. How many subagents are needed (1-5)?

IMPORTANT: You must return a JSON response with the following structure:
{
  "reasoning": "Explanation of your decomposition strategy",
  "complexity": "simple|moderate|complex",
  "number_of_subagents": <number>,
  "subagent_tasks": [
    {
      "query": "specific search query",
      "objective": "what this task should accomplish",
      "focus": "area of focus"
    }
  ]
}

Focus on creating diverse, complementary tasks that together provide comprehensive coverage of the query."""

        user_prompt = f"""
Query: {context.query}
Objective: {context.objective}
Constraints: {', '.join(context.constraints) if context.constraints else 'None'}

Decompose this into specific research tasks for document search agents. Each task should focus on a different aspect or angle of the query.

Return the decomposition in the exact JSON format specified in the system prompt.
"""

        try:
            self.reasoner.add_reasoning_step(
                "execution",
                "Executing LLM-based query decomposition",
                f"Sending request to {self.config.model}"
            )
            
            decomposition = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_model=QueryDecomposition
            )
            
            self.reasoner.add_reasoning_step(
                "execution",
                f"✅ LLM decomposition successful: {decomposition.complexity} complexity, {decomposition.number_of_subagents} subagents",
                f"Reasoning: {decomposition.reasoning}"
            )
            
            # Limit subagents to config max
            tasks = decomposition.subagent_tasks[:self.config.max_subagents]
            
            return tasks
            
        except Exception as e:
            self.reasoner.add_reasoning_step(
                "execution",
                f"❌ LLM decomposition failed: {e}",
                "Falling back to heuristic decomposition"
            )
            return await self._plan_heuristic(context)
    
    async def _plan_heuristic(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Fallback heuristic-based planning with ReAct reasoning."""
        
        self.reasoner.add_reasoning_step(
            "planning",
            "Using heuristic decomposition as fallback",
            "LLM not available or failed, using rule-based approach"
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
        return tasks
    
    async def execute(self, plan: List[Dict[str, Any]]) -> str:
        """Execute research plan with RAG subagents."""
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
        """Synthesize results from multiple RAG subagents."""
        successful_results = [r for r in results if r.status == AgentState.COMPLETED and r.output]
        
        if not successful_results:
            return "❌ No results obtained from RAG research. Check if documents are indexed."
        
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
