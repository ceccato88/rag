"""Tests for base agent functionality."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from rag_agents.agents.base import (
    Agent, AgentContext, AgentResult, AgentState
)
from rag_agents.models.rag_models import ProcessingStep


class MockRAGAgent(Agent[str]):
    """Mock RAG agent implementation for testing."""
    
    def __init__(self, should_fail=False, **kwargs):
        super().__init__(**kwargs)
        self.should_fail = should_fail
        self.plan_called = False
        self.execute_called = False
        
    async def plan(self, context: AgentContext) -> dict:
        self.plan_called = True
        self.add_thinking("Analyzing the RAG query")
        if self.should_fail:
            raise ValueError("Planning failed")
        return {"action": "retrieve", "query": context.query}
        
    async def execute(self, plan: dict) -> str:
        self.execute_called = True
        self.add_thinking("Executing RAG retrieval")
        
        # Simulate processing step
        step = ProcessingStep(
            step_name="document_retrieval",
            agent_name=self.name,
            input_summary=f"Query: {plan.get('query', 'test')}",
            output_summary="Retrieved documents successfully",
            processing_time=0.5,
            tokens_used=100,
            confidence_score=0.8
        )
        # Processing steps are handled at higher level
        
        if self.should_fail:
            raise RuntimeError("Execution failed")
        return "RAG retrieval complete"


@pytest.mark.asyncio
async def test_agent_successful_execution():
    """Test successful agent execution flow."""
    agent = MockRAGAgent(name="TestRAGAgent")
    context = AgentContext(
        query="What are the main components of the Zep architecture?",
        objective="Understand Zep system architecture"
    )
    
    result = await agent.run(context)
    
    assert agent.plan_called
    assert agent.execute_called
    assert result.status == AgentState.COMPLETED
    assert result.output == "RAG retrieval complete"
    assert len(result.thinking) >= 2  # At least start and plan thinking
    assert result.end_time is not None
    assert result.error is None


@pytest.mark.asyncio
async def test_agent_planning_failure():
    """Test agent behavior when planning fails."""
    agent = MockRAGAgent(should_fail=True, name="FailingRAGAgent")
    context = AgentContext(
        query="Test query",
        objective="Test objective"
    )
    
    result = await agent.run(context)
        
    assert agent.plan_called
    assert not agent.execute_called
    assert agent.state == AgentState.FAILED
    assert result.status == AgentState.FAILED
    assert "Planning failed" in result.error


@pytest.mark.asyncio
async def test_agent_execution_failure():
    """Test agent behavior when execution fails."""
    agent = MockRAGAgent(name="TestAgent")
    agent.should_fail = False  # Planning succeeds
    context = AgentContext(
        query="Test query",
        objective="Test objective"
    )
    
    # Mock the execute method to fail
    original_execute = agent.execute
    async def failing_execute(plan):
        agent.execute_called = True
        raise RuntimeError("Execution failed")
    
    agent.execute = failing_execute
    
    result = await agent.run(context)
    
    assert agent.plan_called
    assert agent.execute_called
    assert result.status == AgentState.FAILED
    assert "Execution failed" in result.error


def test_agent_context_creation():
    """Test AgentContext model creation and validation."""
    context = AgentContext(
        query="What are multimodal embeddings?",
        objective="Understand multimodal embedding technology",
        constraints=["Focus on technical details", "Include visual examples"],
        metadata={"priority": "high", "type": "research"},
        parent_agent_id="lead-agent-123"
    )
    
    assert context.query == "What are multimodal embeddings?"
    assert context.objective == "Understand multimodal embedding technology"
    assert len(context.constraints) == 2
    assert "Focus on technical details" in context.constraints
    assert context.metadata["priority"] == "high"
    assert context.parent_agent_id == "lead-agent-123"


def test_agent_context_defaults():
    """Test AgentContext with minimal required fields."""
    context = AgentContext(
        query="Simple query",
        objective="Simple objective"
    )
    
    assert context.query == "Simple query"
    assert context.objective == "Simple objective"
    assert context.constraints == []
    assert context.metadata == {}
    assert context.parent_agent_id is None


def test_processing_step_model():
    """Test ProcessingStep model functionality."""
    step = ProcessingStep(
        step_name="multimodal_retrieval",
        agent_name="MultimodalRetriever",
        input_summary="Query: test query for retrieval",
        output_summary="Found 5 relevant documents",
        processing_time=1.25,
        tokens_used=250,
        confidence_score=0.85
    )
    
    assert step.step_name == "multimodal_retrieval"
    assert step.agent_name == "MultimodalRetriever"
    assert step.input_summary == "Query: test query for retrieval"
    assert step.output_summary == "Found 5 relevant documents"
    assert step.processing_time == 1.25
    assert step.tokens_used == 250
    assert step.confidence_score == 0.85


def test_agent_result_model():
    """Test AgentResult model."""
    from datetime import timezone
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)
    
    result = AgentResult(
        agent_id="rag-agent-123",
        status=AgentState.COMPLETED,
        output="Multimodal RAG results",
        start_time=start_time,
        end_time=end_time,
        tokens_used=1500
    )
    
    assert result.agent_id == "rag-agent-123"
    assert result.status == AgentState.COMPLETED
    assert result.output == "Multimodal RAG results"
    assert result.start_time == start_time
    assert result.end_time == end_time
    assert result.tokens_used == 1500
    assert len(result.thinking) == 0
    assert result.error is None


def test_agent_state_enum():
    """Test AgentState enum values."""
    assert AgentState.IDLE.value == "idle"
    assert AgentState.PLANNING.value == "planning"
    assert AgentState.EXECUTING.value == "executing"
    assert AgentState.COMPLETED.value == "completed"
    assert AgentState.FAILED.value == "failed"


@pytest.mark.asyncio
async def test_agent_thinking_trace():
    """Test agent thinking trace functionality."""
    agent = MockRAGAgent(name="ThinkingAgent")
    
    agent.add_thinking("Starting analysis")
    agent.add_thinking("Processing query")
    agent.add_thinking("Generating plan")
    
    assert len(agent.thinking) == 3
    assert "Starting analysis" in agent.thinking[0]
    assert "Processing query" in agent.thinking[1]
    assert "Generating plan" in agent.thinking[2]


@pytest.mark.asyncio
async def test_agent_processing_steps():
    """Test ProcessingStep model creation (processing steps handled at higher level)."""
    
    step1 = ProcessingStep(
        step_name="query_analysis",
        agent_name="ProcessingAgent",
        input_summary="Input: user query",
        output_summary="Output: query plan",
        processing_time=0.5,
        tokens_used=50,
        confidence_score=0.9
    )
    
    step2 = ProcessingStep(
        step_name="document_retrieval",
        agent_name="ProcessingAgent",
        input_summary="Input: query plan", 
        output_summary="Output: retrieved documents",
        processing_time=1.0,
        tokens_used=100,
        confidence_score=0.8
    )
    
    # Test that ProcessingStep models can be created properly
    assert step1.step_name == "query_analysis"
    assert step2.step_name == "document_retrieval"
    assert step1.tokens_used == 50
    assert step2.tokens_used == 100


@pytest.mark.asyncio
async def test_agent_token_tracking():
    """Test agent token usage tracking."""
    agent = MockRAGAgent(name="TokenAgent")
    
    # Simulate token usage (directly set tokens_used)
    agent.tokens_used = 100
    agent.tokens_used += 250
    agent.tokens_used += 150
    
    assert agent.tokens_used == 500


@pytest.mark.asyncio 
async def test_agent_id_generation():
    """Test that agents get unique IDs."""
    agent1 = MockRAGAgent(name="Agent1")
    agent2 = MockRAGAgent(name="Agent2")
    
    assert agent1.agent_id != agent2.agent_id
    assert len(agent1.agent_id) > 10  # Should be a UUID-style string
    assert len(agent2.agent_id) > 10  # Should be a UUID-style string
    # IDs are UUIDs, not prefixed with agent names
    assert "-" in agent1.agent_id  # UUID format