"""Simple test of RAG integration."""

import sys
import os
from pathlib import Path

# Add both paths
sys.path.append('/workspaces/rag')
sys.path.append('/workspaces/rag/multi-agent-researcher')

async def test_basic_integration():
    """Test basic integration between RAG and multi-agent system."""
    
    print("🧪 Testing RAG Multi-Agent Integration")
    
    # Test 1: Import RAG system
    print("\\n1. Testing RAG system import...")
    try:
        from search import ProductionConversationalRAG
        print("   ✅ RAG system imported successfully")
        
        # Test RAG initialization
        rag = ProductionConversationalRAG()
        print("   ✅ RAG system initialized")
        
    except Exception as e:
        print(f"   ❌ RAG system failed: {e}")
        return False
    
    # Test 2: Import multi-agent components
    print("\\n2. Testing multi-agent imports...")
    try:
        from src.researcher.agents.rag_subagent import RAGResearchSubagent, RAGSubagentConfig
        from src.researcher.agents.simple_lead import SimpleLeadResearcher, SimpleLeadConfig
        from src.researcher.agents.base import AgentContext
        from src.researcher.memory.base import InMemoryStorage, ResearchMemory
        from src.researcher.tools.base import ToolRegistry
        print("   ✅ Multi-agent components imported successfully")
        
    except Exception as e:
        print(f"   ❌ Multi-agent import failed: {e}")
        return False
    
    # Test 3: Create RAG subagent
    print("\\n3. Testing RAG subagent creation...")
    try:
        config = RAGSubagentConfig(enable_thinking=True)
        agent = RAGResearchSubagent(config=config)
        print("   ✅ RAG subagent created successfully")
        
    except Exception as e:
        print(f"   ❌ RAG subagent creation failed: {e}")
        return False
    
    # Test 4: Test simple query
    print("\\n4. Testing simple query execution...")
    try:
        context = AgentContext(
            query="What is machine learning?",
            objective="Understand machine learning basics",
            metadata={"focus_areas": ["definition", "applications"]}
        )
        
        result = await agent.run(context)
        print(f"   ✅ Query executed - Status: {result.status.value}")
        
        if result.output:
            print(f"   📄 Output preview: {result.output[:100]}...")
        
        if result.tool_calls:
            print(f"   🔧 Tool calls made: {len(result.tool_calls)}")
        
    except Exception as e:
        print(f"   ❌ Query execution failed: {e}")
        return False
    
    # Test 5: Test lead researcher
    print("\\n5. Testing simplified lead researcher...")
    try:
        storage = InMemoryStorage()
        memory = ResearchMemory(storage)
        registry = ToolRegistry()
        
        lead_config = SimpleLeadConfig(max_subagents=2, parallel_execution=False)
        lead = SimpleLeadResearcher(
            memory=memory,
            tool_registry=registry,
            subagent_class=RAGResearchSubagent,
            subagent_config=config,
            config=lead_config
        )
        
        context = AgentContext(
            query="How do neural networks work?",
            objective="Understand neural network fundamentals"
        )
        
        result = await lead.run(context)
        print(f"   ✅ Lead researcher executed - Status: {result.status.value}")
        print(f"   🤖 Subagents used: {len(result.subagent_results)}")
        
    except Exception as e:
        print(f"   ❌ Lead researcher failed: {e}")
        return False
    
    print("\\n🎉 All integration tests passed!")
    print("\\n💡 Your RAG system is now successfully integrated as a multi-agent subagent!")
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_basic_integration())
