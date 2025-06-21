"""Ultra-simplified lead researcher for RAG coordination."""

import asyncio
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# Load environment variables from project root
from dotenv import load_dotenv, find_dotenv

# Find and load .env file from any parent directory
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)

from researcher.agents.base import Agent, AgentContext, AgentResult, AgentState
from researcher.agents.document_search_agent import RAGResearchSubagent, RAGSubagentConfig
from pydantic import BaseModel

# Import constants
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))
from src.core.constants import MULTIAGENT_CONFIG


class SimpleLeadConfig(BaseModel):
    """Configuration for simplified lead researcher."""
    max_subagents: int = MULTIAGENT_CONFIG['MAX_SUBAGENTS']
    parallel_execution: bool = MULTIAGENT_CONFIG['PARALLEL_EXECUTION']


class SimpleLeadResearcher(Agent[str]):
    """
    Ultra-simplified lead researcher that coordinates RAG subagents.
    
    No external dependencies, no complex decomposition - just clean coordination.
    """
    
    def __init__(
        self,
        config: Optional[SimpleLeadConfig] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.config = config or SimpleLeadConfig()
        self.subagents: List[RAGResearchSubagent] = []
        
    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Create simple research plan."""
        self.add_thinking(f"Planning multi-agent RAG research for: {context.query}")
        
        # Create specialized research tasks based on available focus areas
        # Available focus areas: conceptual, technical, comparative, examples, general
        focus_areas = ["conceptual", "technical", "comparative", "examples"]
        
        tasks = []
        
        # Always start with conceptual analysis
        tasks.append({
            "query": context.query,
            "objective": f"Conceptual analysis: {context.objective}",
            "focus_area": "conceptual"
        })
        
        # Add additional specialized tasks based on max_subagents
        additional_areas = focus_areas[1:self.config.max_subagents]  # Skip conceptual (already added)
        for area in additional_areas:
            if area == "technical":
                tasks.append({
                    "query": f"{context.query} technical implementation",
                    "objective": f"Technical details: {context.objective}",
                    "focus_area": "technical"
                })
            elif area == "comparative":
                tasks.append({
                    "query": f"{context.query} comparison analysis",
                    "objective": f"Comparative analysis: {context.objective}",
                    "focus_area": "comparative"
                })
            elif area == "examples":
                tasks.append({
                    "query": f"{context.query} examples and use cases",
                    "objective": f"Examples and use cases: {context.objective}",
                    "focus_area": "examples"
                })
        
        self.add_thinking(f"Created {len(tasks)} research tasks")
        return tasks
    
    async def execute(self, plan: List[Dict[str, Any]]) -> str:
        """Execute research plan with RAG subagents."""
        self.add_thinking(f"Executing {len(plan)} RAG research tasks")
        
        if self.config.parallel_execution:
            results = await self._execute_parallel(plan)
        else:
            results = await self._execute_sequential(plan)
        
        # Synthesize results
        synthesis = self._synthesize_results(plan, results)
        return synthesis
    
    async def _execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[AgentResult]:
        """Execute subagents in parallel with concurrency control."""
        # Control concurrency
        semaphore = asyncio.Semaphore(MULTIAGENT_CONFIG['CONCURRENCY_LIMIT'])
        
        async def run_with_semaphore(task_data):
            async with semaphore:
                i, task = task_data
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
                    metadata={"focus_area": task["focus_area"]}
                )
                
                return await subagent.run(context)
        
        # Create tasks with concurrency control
        task_data = [(i, task) for i, task in enumerate(tasks)]
        
        # Execute all in parallel with concurrency limit
        try:
            results = await asyncio.gather(
                *[run_with_semaphore(td) for td in task_data], 
                return_exceptions=True
            )
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.add_thinking(f"Subagent {i+1} failed: {result}")
                    # Create failed result
                    processed_results.append(AgentResult(
                        agent_id=f"failed-{i}",
                        status=AgentState.FAILED,
                        error=str(result),
                        start_time=datetime.now(timezone.utc),
                        end_time=datetime.now(timezone.utc)
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            self.add_thinking(f"Parallel execution failed: {e}")
            return []
    
    async def _execute_sequential(self, tasks: List[Dict[str, Any]]) -> List[AgentResult]:
        """Execute subagents sequentially."""
        results = []
        
        for i, task in enumerate(tasks):
            self.add_thinking(f"Executing task {i+1}/{len(tasks)}: {task['focus']}")
            
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
                metadata={"focus_area": task["focus_area"]}
            )
            
            # Execute
            try:
                result = await subagent.run(context)
                results.append(result)
                self.add_thinking(f"Task {i+1} completed: {result.status.name}")
                
            except Exception as e:
                self.add_thinking(f"Task {i+1} failed: {e}")
                results.append(AgentResult(
                    agent_id=f"error-{i}",
                    status=AgentState.FAILED,
                    error=str(e),
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc)
                ))
        
        return results
    
    def _synthesize_results(self, tasks: List[Dict[str, Any]], results: List[AgentResult]) -> str:
        """Synthesize results from multiple RAG subagents."""
        successful_results = [r for r in results if r.status == AgentState.COMPLETED and r.output]
        
        if not successful_results:
            return "❌ No results obtained from RAG research. Check if documents are indexed."
        
        # Build synthesis
        report_lines = [
            "# Multi-Agent RAG Research Report",
            "",
            f"**Research Tasks**: {len(results)}",
            f"**Successful**: {len(successful_results)}",
            f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Add individual results
        for i, (task, result) in enumerate(zip(tasks, results)):
            if result.status == AgentState.COMPLETED and result.output:
                report_lines.extend([
                    f"## Task {i+1}: {task['focus_area'].title()} Analysis",
                    f"**Query**: {task['query']}",
                    "",
                    result.output,
                    "",
                    "---",
                    ""
                ])
            else:
                report_lines.extend([
                    f"## Task {i+1}: {task['focus_area'].title()} Analysis ❌",
                    f"**Status**: Failed - {result.error or 'Unknown error'}",
                    "",
                    "---",
                    ""
                ])
        
        # Add summary
        report_lines.extend([
            "## Summary",
            f"- Executed {len(results)} RAG research tasks",
            f"- Success rate: {len(successful_results)}/{len(results)} ({len(successful_results)/len(results)*100:.0f}%)",
            f"- Total subagents: {len(self.subagents)}",
            ""
        ])
        
        return "\\n".join(report_lines)
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the complete multi-agent research process."""
        self.state = AgentState.PLANNING
        start_time = datetime.now(timezone.utc)
        
        # Initialize result
        self._result = AgentResult(
            agent_id=self.agent_id,
            status=self.state,
            start_time=start_time
        )
        
        try:
            self.add_thinking(f"Starting multi-agent RAG research: '{context.query}'")
            
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
            self._result.end_time = datetime.now(timezone.utc)
            
            return self._result
            
        except Exception as e:
            self.state = AgentState.FAILED
            self._result.status = AgentState.FAILED
            self._result.error = str(e)
            self._result.end_time = datetime.now(timezone.utc)
            self.add_thinking(f"Multi-agent research failed: {e}")
            
            return self._result
