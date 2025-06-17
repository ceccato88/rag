"""Test the multimodal RAG system with a real query."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path and setup environment
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import get_config

def setup_environment():
    """Setup environment using flexible config system."""
    config = get_config()
    
    if not config.is_ready():
        print("❌ Environment configuration incomplete")
        config.print_status()
        return False
    
    print(f"✅ Environment loaded from: {config.env_file_used or 'system environment'}")
    return True

async def test_real_query():
    """Test the system with a real query."""
    print("🧪 Testing Multimodal RAG with Real Query")
    print("=" * 50)
    
    try:
        # Import agents
        from rag_agents.agents.lead_rag import LeadRAGAgent, LeadRAGConfig
        from rag_agents.agents.retriever import MultimodalRetrieverAgent, RetrieverConfig
        from rag_agents.agents.reranker import MultimodalRerankerAgent, RerankerConfig
        from rag_agents.agents.context_analyzer import ContextAnalyzerAgent, ContextAnalyzerConfig
        from rag_agents.agents.answer_generator import MultimodalAnswerAgent, AnswerGeneratorConfig
        from rag_agents.agents.base import AgentContext
        
        print("✅ Agents imported")
        
        # Initialize configurations
        retriever_config = RetrieverConfig(max_candidates=5)
        reranker_config = RerankerConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        analyzer_config = ContextAnalyzerConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        generator_config = AnswerGeneratorConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        lead_config = LeadRAGConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        print("✅ Configurations created")
        
        # Initialize agents
        retriever = MultimodalRetrieverAgent(config=retriever_config, name="Retriever")
        reranker = MultimodalRerankerAgent(config=reranker_config, name="Reranker")
        context_analyzer = ContextAnalyzerAgent(config=analyzer_config, name="ContextAnalyzer")
        answer_generator = MultimodalAnswerAgent(config=generator_config, name="AnswerGenerator")
        
        print("✅ Agents initialized")
        
        # Create lead agent
        lead_agent = LeadRAGAgent(
            retriever_agent=retriever,
            reranker_agent=reranker,
            context_analyzer_agent=context_analyzer,
            answer_generator_agent=answer_generator,
            config=lead_config,
            name="LeadAgent"
        )
        
        print("✅ Lead agent created")
        
        # Test query
        test_query = "What are the main components of the Zep architecture?"
        context = AgentContext(
            query=test_query,
            objective="Understand the technical architecture of the Zep system",
            constraints=["Focus on technical details", "Include visual diagrams if available"]
        )
        
        print(f"\n🔍 Running query: {test_query}")
        print("🕒 This may take a few moments...")
        
        # Run the RAG system
        start_time = asyncio.get_event_loop().time()
        result = await lead_agent.run(context)
        end_time = asyncio.get_event_loop().time()
        
        print(f"\n⏱️  Processing completed in {end_time - start_time:.2f} seconds")
        print(f"📊 Status: {result.status}")
        
        if result.status.value == "completed" and result.output:
            rag_result = result.output
            
            print("\n🎉 RAG Query Successful!")
            print("=" * 50)
            
            print(f"📋 Query Type: {rag_result.query_decomposition.query_type}")
            print(f"🎯 Key Aspects: {', '.join(rag_result.query_decomposition.key_aspects)}")
            print(f"📊 Total Processing Time: {rag_result.total_processing_time:.2f}s")
            print(f"🔧 Processing Steps: {len(rag_result.processing_steps)}")
            print(f"💰 Total Tokens: {rag_result.total_tokens_used}")
            print(f"📚 Documents Used: {len(rag_result.ranked_documents.documents)}")
            print(f"🎯 Confidence: {rag_result.answer.multimodal_confidence:.2f}")
            print(f"⚖️  Evidence Strength: {rag_result.answer.evidence_strength}")
            
            print(f"\n📄 Answer:")
            print("-" * 60)
            print(rag_result.answer.main_response)
            print("-" * 60)
            
            if rag_result.answer.sources_used:
                print(f"\n📚 Sources ({len(rag_result.answer.sources_used)}):")
                for i, source in enumerate(rag_result.answer.sources_used, 1):
                    print(f"   {i}. {source.document} - Page {source.page_number}")
            
            if rag_result.answer.limitations:
                print(f"\n⚠️  Limitations:")
                for limitation in rag_result.answer.limitations:
                    print(f"   • {limitation}")
            
            return True
        else:
            print(f"\n❌ Query failed: {result.error}")
            if result.thinking:
                print("🧠 Agent thinking:")
                for thought in result.thinking[-5:]:  # Show last 5 thoughts
                    print(f"   {thought}")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    if not setup_environment():
        print("❌ Environment setup failed")
        return
    
    success = asyncio.run(test_real_query())
    
    if success:
        print(f"\n✨ Test completed successfully!")
        print("💡 The multimodal RAG system is working with your documents!")
    else:
        print(f"\n⚠️  Test had issues - check errors above")

if __name__ == "__main__":
    main()