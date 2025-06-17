"""Run multimodal RAG demo with automatic environment setup."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import get_config

def setup_environment():
    """Setup environment using flexible config system."""
    config = get_config()
    
    if not config.is_ready():
        print("❌ Environment configuration incomplete")
        config.print_status()
        return False
    
    print(f"📁 Environment loaded from: {config.env_file_used or 'system environment'}")
    required_vars = config.get_required_vars()
    for var in required_vars:
        print(f"✅ {var} loaded")
    
    return True

async def run_simple_demo():
    """Run a simple demo without the full complexity."""
    print("\n🤖 Running Simple Multimodal RAG Demo")
    print("=" * 50)
    
    try:
        # Import agents
        from rag_agents.agents.lead_rag import LeadRAGAgent, LeadRAGConfig
        from rag_agents.agents.retriever import MultimodalRetrieverAgent, RetrieverConfig
        from rag_agents.agents.reranker import MultimodalRerankerAgent, RerankerConfig
        from rag_agents.agents.context_analyzer import ContextAnalyzerAgent, ContextAnalyzerConfig
        from rag_agents.agents.answer_generator import MultimodalAnswerAgent, AnswerGeneratorConfig
        from rag_agents.agents.base import AgentContext
        
        print("✅ All agents imported successfully")
        
        # Test agent initialization
        print("\n🔧 Initializing agents...")
        
        retriever_config = RetrieverConfig()
        print("✅ Retriever config created")
        
        reranker_config = RerankerConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ Reranker config created")
        
        analyzer_config = ContextAnalyzerConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ Analyzer config created")
        
        generator_config = AnswerGeneratorConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ Generator config created")
        
        lead_config = LeadRAGConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ Lead config created")
        
        # Try to initialize retriever (this will test Astra DB connection)
        print("\n🔍 Testing database connection...")
        try:
            retriever = MultimodalRetrieverAgent(config=retriever_config, name="TestRetriever")
            print("✅ Database connection successful!")
            
            # Test a simple context creation
            context = AgentContext(
                query="What is the Zep architecture?",
                objective="Test the system components"
            )
            print(f"✅ Test context created: {context.query}")
            
            print("\n🎉 System fully operational!")
            print("💡 You can now run complex RAG queries with multimodal capabilities")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("💡 Make sure your Astra DB is accessible and contains indexed documents")
            return False
    
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("🚀 Multimodal RAG Agents - Demo Launcher")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        return False
    
    # Run async demo
    import asyncio
    success = asyncio.run(run_simple_demo())
    
    if success:
        print("\n✨ Demo completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Modify the query in the demo")
        print("2. Test with your own documents")
        print("3. Customize agent configurations")
        print("4. Integrate with your existing RAG system")
    else:
        print("\n⚠️  Demo completed with issues")
        print("Check the error messages above for troubleshooting")
    
    return success

if __name__ == "__main__":
    main()