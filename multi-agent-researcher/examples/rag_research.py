"""Example using RAG system as a research subagent."""

import asyncio
import sys
from pathlib import Path

# Load environment variables from project root
from dotenv import load_dotenv, find_dotenv

# Find and load .env file from any parent directory
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)
    print(f"✅ Loaded .env from: {env_file}")

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.researcher.agents.simple_lead import SimpleLeadResearcher, SimpleLeadConfig
from src.researcher.agents.rag_subagent import RAGResearchSubagent, RAGSubagentConfig
from src.researcher.agents.base import AgentContext
from src.researcher.memory.base import InMemoryStorage, ResearchMemory
from src.researcher.tools.base import ToolRegistry

console = Console()


async def rag_research_example():
    """Example using RAG system for document research."""
    
    console.print(Panel("🏗️ Setting up RAG-based multi-agent research system...", style="blue"))
    
    # Setup components
    storage = InMemoryStorage()
    memory = ResearchMemory(storage)
    
    # Tools registry (empty since RAG agent has direct access to RAG system)
    registry = ToolRegistry()
    
    # Configure RAG subagent
    rag_config = RAGSubagentConfig(
        max_search_iterations=2,
        enable_thinking=True,
        cache_ttl=1800
    )
    
    # Configure lead researcher to use RAG subagents
    lead_config = SimpleLeadConfig(
        max_subagents=2,
        parallel_execution=True,
        enable_thinking=True
    )
    
    # Create lead researcher with RAG subagent
    lead = SimpleLeadResearcher(
        memory=memory,
        tool_registry=registry,
        subagent_class=RAGResearchSubagent,
        subagent_config=rag_config,
        config=lead_config
    )
    
    console.print("✅ System initialized with RAG-based subagents")
    
    # Test queries
    test_queries = [
        {
            "query": "What is machine learning and how is it applied?",
            "objective": "Understand machine learning fundamentals and applications",
            "description": "Basic ML research"
        },
        {
            "query": "Compare different neural network architectures",
            "objective": "Analyze various neural network types and their use cases",
            "description": "Comparative analysis"
        },
        {
            "query": "Recent advances in transformer models",
            "objective": "Research latest developments in transformer technology",
            "description": "Cutting-edge research"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        console.print(f"\\n{Panel(f'🔍 Test {i}: {test_case[\"description\"]}', style='green')}")
        console.print(f"Query: {test_case['query']}")
        console.print(f"Objective: {test_case['objective']}\\n")
        
        # Create context
        context = AgentContext(
            query=test_case["query"],
            objective=test_case["objective"],
            metadata={
                "focus_areas": ["applications", "technical details", "examples"],
                "depth": "comprehensive"
            }
        )
        
        try:
            # Execute research
            console.print("🔄 Starting research...")
            result = await lead.run(context)
            
            if result.status.value == "completed":
                console.print(Panel("✅ Research completed successfully!", style="green"))
                
                # Display results
                if result.output:
                    console.print("\\n📄 **Research Results:**")
                    console.print(Markdown(result.output))
                
                # Display thinking process
                if result.thinking:
                    console.print("\\n🧠 **Thinking Process:**")
                    for thought in result.thinking[-3:]:  # Show last 3 thoughts
                        console.print(f"   • {thought}")
                
                # Display subagent results
                if result.subagent_results:
                    console.print(f"\\n🤖 **Subagents Used:** {len(result.subagent_results)}")
                    for j, subresult in enumerate(result.subagent_results, 1):
                        console.print(f"   Agent {j}: {subresult.status.value}")
                        if subresult.tool_calls:
                            console.print(f"      Tool calls: {len(subresult.tool_calls)}")
                
            else:
                console.print(Panel(f"❌ Research failed: {result.error}", style="red"))
                
        except Exception as e:
            console.print(Panel(f"💥 Error during research: {e}", style="red"))
        
        # Wait between tests
        if i < len(test_queries):
            console.print("\\n" + "="*60)
            await asyncio.sleep(1)
    
    console.print(Panel("🎉 RAG-based multi-agent research demo completed!", style="green"))


async def single_rag_subagent_test():
    """Test a single RAG subagent directly."""
    
    console.print(Panel("🧪 Testing single RAG subagent...", style="yellow"))
    
    # Create RAG subagent directly
    config = RAGSubagentConfig(enable_thinking=True)
    agent = RAGResearchSubagent(config=config)
    
    # Test context
    context = AgentContext(
        query="What are the main components of a transformer model?",
        objective="Understand transformer architecture",
        metadata={"focus_areas": ["attention mechanism", "encoder", "decoder"]}
    )
    
    console.print(f"Query: {context.query}")
    console.print("🔄 Running subagent...")
    
    try:
        result = await agent.run(context)
        
        console.print(f"\\nStatus: {result.status.value}")
        
        if result.output:
            console.print("\\n📄 **Output:**")
            console.print(result.output)
        
        if result.thinking:
            console.print("\\n🧠 **Agent Thinking:**")
            for thought in result.thinking:
                console.print(f"   • {thought}")
        
        if result.tool_calls:
            console.print(f"\\n🔧 **Tool Calls:** {len(result.tool_calls)}")
            for call in result.tool_calls:
                status = "✅" if not call.error else "❌"
                console.print(f"   {status} {call.tool_name}: {call.parameters.get('query', 'N/A')}")
        
    except Exception as e:
        console.print(Panel(f"❌ Error: {e}", style="red"))


async def main():
    """Main demo function."""
    
    console.print(Panel("🚀 RAG Multi-Agent Research System Demo", style="bold blue"))
    console.print("This demo shows how to use your RAG system as specialized subagents\\n")
    
    # Test menu
    console.print("Choose demo mode:")
    console.print("1. Single subagent test (quick)")
    console.print("2. Full multi-agent research (comprehensive)")
    console.print("3. Both\\n")
    
    # For demo purposes, run both
    choice = "3"
    
    if choice in ["1", "3"]:
        await single_rag_subagent_test()
        console.print("\\n" + "="*80 + "\\n")
    
    if choice in ["2", "3"]:
        await rag_research_example()


if __name__ == "__main__":
    asyncio.run(main())
