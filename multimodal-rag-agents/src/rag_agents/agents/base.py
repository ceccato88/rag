"""Base agent abstractions for multimodal RAG system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timezone
from enum import Enum
import uuid
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Agent execution states."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolCall(BaseModel):
    """Represents a single tool invocation."""
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: Optional[Any] = None
    error: Optional[str] = None


class AgentContext(BaseModel):
    """Context passed between agents."""
    query: str
    objective: str
    constraints: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_agent_id: Optional[str] = None
    
    
class AgentResult(BaseModel):
    """Standardized result from agent execution."""
    agent_id: str
    status: AgentState
    output: Optional[Any] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    thinking: List[str] = Field(default_factory=list)
    subagent_results: List['AgentResult'] = Field(default_factory=list)
    error: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    tokens_used: int = 0


T = TypeVar('T')


class Agent(ABC, Generic[T]):
    """Base agent class with planning and execution phases."""
    
    def __init__(self, name: Optional[str] = None, **kwargs):
        self.agent_id = str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.state = AgentState.IDLE
        self.thinking: List[str] = []
        self.tool_calls: List[ToolCall] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.tokens_used = 0
        
    def add_thinking(self, thought: str) -> None:
        """Add a thinking step."""
        self.thinking.append(f"[{datetime.now(timezone.utc).isoformat()}] {thought}")
        
    def add_tool_call(self, tool_call: ToolCall) -> None:
        """Record a tool call."""
        self.tool_calls.append(tool_call)
        
    @abstractmethod
    async def plan(self, context: AgentContext) -> Any:
        """Create execution plan based on context."""
        pass
        
    @abstractmethod 
    async def execute(self, plan: Any) -> T:
        """Execute the plan and return results."""
        pass
        
    async def run(self, context: AgentContext) -> AgentResult:
        """Run the complete agent lifecycle."""
        self.start_time = datetime.now(timezone.utc)
        self.state = AgentState.PLANNING
        
        try:
            self.add_thinking(f"Starting {self.name} with query: {context.query}")
            
            # Planning phase
            plan = await self.plan(context)
            self.add_thinking(f"Plan created: {plan}")
            
            # Execution phase
            self.state = AgentState.EXECUTING
            result = await self.execute(plan)
            
            self.state = AgentState.COMPLETED
            self.end_time = datetime.now(timezone.utc)
            
            return AgentResult(
                agent_id=self.agent_id,
                status=self.state,
                output=result,
                tool_calls=self.tool_calls,
                thinking=self.thinking,
                start_time=self.start_time,
                end_time=self.end_time,
                tokens_used=self.tokens_used
            )
            
        except Exception as e:
            self.state = AgentState.FAILED
            self.end_time = datetime.now(timezone.utc)
            error_msg = f"Agent {self.name} failed: {str(e)}"
            self.add_thinking(error_msg)
            
            return AgentResult(
                agent_id=self.agent_id,
                status=self.state,
                error=error_msg,
                tool_calls=self.tool_calls,
                thinking=self.thinking,
                start_time=self.start_time,
                end_time=self.end_time,
                tokens_used=self.tokens_used
            )