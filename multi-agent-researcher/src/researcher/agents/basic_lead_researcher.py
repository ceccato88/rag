"""Ultra-simplified lead researcher for RAG coordination."""

import asyncio
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

# Load environment variables from project root
from dotenv import load_dotenv, find_dotenv

# Find and load .env file from any parent directory
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)

from researcher.agents.base import Agent, AgentContext, AgentResult, AgentState
from researcher.agents.document_search_agent import RAGResearchSubagent, RAGSubagentConfig
from pydantic import BaseModel


class SimpleLeadConfig(BaseModel):
    """Configuration for simplified lead researcher."""
    max_subagents: int = 2
    parallel_execution: bool = True


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
        
        # Simple decomposition: create different search angles
        tasks = [
            {
                "query": context.query,
                "objective": f"General research: {context.objective}",
                "focus": "general"
            }
        ]
        
        # Add a second task with slightly different angle if max_subagents > 1
        if self.config.max_subagents > 1:
            tasks.append({
                "query": f"{context.query} detailed analysis",
                "objective": f"Detailed analysis: {context.objective}",
                "focus": "detailed"
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
                metadata={"focus": task["focus"]}
            )
            
            # Add to parallel execution
            coroutines.append(subagent.run(context))
        
        # Execute all in parallel
        try:
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
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
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow()
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
                metadata={"focus": task["focus"]}
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
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow()
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
                    f"## Task {i+1}: {task['focus'].title()} Analysis",
                    f"**Query**: {task['query']}",
                    "",
                    result.output,
                    "",
                    "---",
                    ""
                ])
            else:
                report_lines.extend([
                    f"## Task {i+1}: {task['focus'].title()} Analysis ❌",
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
        start_time = datetime.utcnow()
        
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
            self._result.end_time = datetime.utcnow()
            
            return self._result
            
        except Exception as e:
            self.state = AgentState.FAILED
            self._result.status = AgentState.FAILED
            self._result.error = str(e)
            self._result.end_time = datetime.utcnow()
            self.add_thinking(f"Multi-agent research failed: {e}")
            
            return self._result
