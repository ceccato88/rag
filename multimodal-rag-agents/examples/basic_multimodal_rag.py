"""Basic example of multimodal RAG system usage."""

import asyncio
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import get_config
from rag_agents.agents.lead_rag import LeadRAGAgent, LeadRAGConfig
from rag_agents.agents.retriever import MultimodalRetrieverAgent, RetrieverConfig
from rag_agents.agents.reranker import MultimodalRerankerAgent, RerankerConfig
from rag_agents.agents.context_analyzer import ContextAnalyzerAgent, ContextAnalyzerConfig
from rag_agents.agents.answer_generator import MultimodalAnswerAgent, AnswerGeneratorConfig
from rag_agents.agents.base import AgentContext


async def main():
    """Run a basic multimodal RAG example."""
    
    print("🤖 Multimodal RAG Agents Demo")
    print("=" * 50)
    
    # Check environment configuration
    config = get_config()
    if not config.is_ready():
        print("❌ Environment configuration incomplete")
        config.print_status()
        return
    
    print(f"✅ Environment loaded from: {config.env_file_used or 'system environment'}")
    
    try:
        # Initialize agent configurations from environment
        retriever_config = RetrieverConfig.from_env(config)
        reranker_config = RerankerConfig.from_env(config)
        analyzer_config = ContextAnalyzerConfig.from_env(config)
        generator_config = AnswerGeneratorConfig.from_env(config)
        lead_config = LeadRAGConfig.from_env(config)
        
        # Initialize agents
        print("🔧 Initializing agents...")
        retriever = MultimodalRetrieverAgent(config=retriever_config, name="MultimodalRetriever")
        reranker = MultimodalRerankerAgent(config=reranker_config, name="IntelligentReranker")
        context_analyzer = ContextAnalyzerAgent(config=analyzer_config, name="ContextAnalyzer")
        answer_generator = MultimodalAnswerAgent(config=generator_config, name="AnswerGenerator")
        
        # Create lead agent
        lead_agent = LeadRAGAgent(
            retriever_agent=retriever,
            reranker_agent=reranker,
            context_analyzer_agent=context_analyzer,
            answer_generator_agent=answer_generator,
            config=lead_config,
            name="LeadRAGAgent"
        )
        
        print("✅ All agents initialized successfully!")
        
        # Create query context
        context = AgentContext(
            query="What are the main components of the Zep architecture and how do they work together?",
            objective="Provide a comprehensive overview of Zep system architecture including visual elements",
            constraints=[
                "Include both textual explanations and visual diagrams",
                "Focus on architectural components and their relationships",
                "Provide specific technical details"
            ]
        )
        
        print(f"\n🔍 Processing query: {context.query}")
        print(f"📋 Objective: {context.objective}")
        
        # Run the multimodal RAG system
        start_time = asyncio.get_event_loop().time()
        result = await lead_agent.run(context)
        end_time = asyncio.get_event_loop().time()
        
        if result.status.value == "completed":
            rag_result = result.output
            
            print("\n✅ RAG Processing Completed!")
            print("=" * 50)
            
            # Display processing statistics
            print(f"⏱️  Total Processing Time: {end_time - start_time:.2f}s")
            print(f"🔧 Processing Steps: {len(rag_result.processing_steps)}")
            print(f"📊 Total Tokens Used: {rag_result.total_tokens_used:,}")
            print(f"📚 Documents Analyzed: {len(rag_result.ranked_documents.documents)}")
            print(f"🎯 Multimodal Confidence: {rag_result.answer.multimodal_confidence:.2f}")
            
            # Display query decomposition
            print(f"\n📋 Query Analysis:")
            print(f"   Type: {rag_result.query_decomposition.query_type}")
            print(f"   Key Aspects: {', '.join(rag_result.query_decomposition.key_aspects)}")
            print(f"   Visual Requirements: {', '.join(rag_result.query_decomposition.visual_requirements)}")
            
            # Display context quality
            print(f"\n📊 Context Quality Assessment:")
            print(f"   Completeness: {rag_result.context_analysis.completeness_score:.2f}")
            print(f"   Confidence Level: {rag_result.context_analysis.confidence_level}")
            print(f"   Visual Coverage: {rag_result.context_analysis.visual_coverage:.2f}")
            print(f"   Recommended Action: {rag_result.context_analysis.recommended_action}")
            
            # Display sources used
            print(f"\n📚 Sources Used ({len(rag_result.answer.sources_used)}):")
            for i, source in enumerate(rag_result.answer.sources_used, 1):
                print(f"   {i}. {source.document} (Page {source.page_number}) - {source.content_type}")
            
            # Display visual elements
            if rag_result.answer.visual_elements_used:
                print(f"\n🖼️  Visual Elements Referenced:")
                for element in rag_result.answer.visual_elements_used:
                    print(f"   • {element}")
            
            # Display main answer
            print(f"\n💬 Answer:")
            print("-" * 80)
            print(rag_result.answer.main_response)
            print("-" * 80)
            
            # Display evidence strength and limitations
            print(f"\n⚖️  Evidence Strength: {rag_result.answer.evidence_strength}")
            
            if rag_result.answer.limitations:
                print(f"\n⚠️  Limitations:")
                for limitation in rag_result.answer.limitations:
                    print(f"   • {limitation}")
            
            # Display follow-up suggestions
            if rag_result.answer.follow_up_suggestions:
                print(f"\n💡 Follow-up Suggestions:")
                for suggestion in rag_result.answer.follow_up_suggestions:
                    print(f"   • {suggestion}")
            
            # Display processing steps
            print(f"\n🔄 Processing Pipeline:")
            for i, step in enumerate(rag_result.processing_steps, 1):
                print(f"   {i}. {step.step_name} ({step.agent_name})")
                print(f"      Time: {step.processing_time:.2f}s, Tokens: {step.tokens_used}")
                print(f"      Confidence: {step.confidence_score:.2f}")
        
        else:
            print(f"\n❌ RAG Processing Failed!")
            print(f"Status: {result.status}")
            print(f"Error: {result.error}")
            
            if result.thinking:
                print(f"\n🧠 Agent Thinking Process:")
                for thought in result.thinking:
                    print(f"   {thought}")
    
    except Exception as e:
        print(f"\n❌ Error running multimodal RAG demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Multimodal RAG Agents - Basic Demo")
    print("=" * 40)
    asyncio.run(main())