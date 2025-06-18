"""Lead RAG agent that orchestrates the multimodal RAG process using OpenAI and Instructor."""

from typing import List, Optional, Type, Dict, Any
import asyncio
import time
from datetime import datetime
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from ..agents.base import Agent, AgentContext, AgentResult
from ..models.rag_models import (
    RAGDecomposition, QueryContext, RAGResult, ProcessingStep,
    StructuredAnswer, ContextAnalysis, RankedDocuments
)


class LeadRAGConfig(BaseModel):
    """Configuration for Lead RAG Agent."""
    openai_api_key: Optional[str] = None
    model: str = "gpt-4o"
    max_subagents: int = 4
    parallel_execution: bool = True
    context_window_limit: int = 128000
    subagent_timeout: float = 300.0
    min_confidence_threshold: float = 0.7
    
    @classmethod
    def from_env(cls, config_manager=None):
        """Create config from environment variables."""
        import os
        if config_manager:
            return cls(
                openai_api_key=config_manager.get("OPENAI_API_KEY"),
                model=config_manager.get("LLM_MODEL", "gpt-4o")
            )
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4o")
        )


class LeadRAGAgent(Agent[RAGResult]):
    """Lead agent that orchestrates multimodal RAG processing using OpenAI and Instructor."""
    
    def __init__(
        self,
        retriever_agent: Agent,
        reranker_agent: Agent,
        context_analyzer_agent: Agent,
        answer_generator_agent: Agent,
        config: Optional[LeadRAGConfig] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.retriever = retriever_agent
        self.reranker = reranker_agent
        self.context_analyzer = context_analyzer_agent
        self.answer_generator = answer_generator_agent
        self.config = config or LeadRAGConfig()
        
        # Initialize OpenAI client with Instructor
        client = AsyncOpenAI(api_key=self.config.openai_api_key)
        self.client = instructor.from_openai(client)
        
        self.processing_steps: List[ProcessingStep] = []
        
    async def plan(self, context: AgentContext) -> RAGDecomposition:
        """Decompose query into structured RAG plan using OpenAI with Instructor."""
        self.add_thinking(f"Analyzing query for RAG decomposition: {context.query}")
        
        start_time = time.time()
        
        try:
            # Use Instructor to get structured decomposition from OpenAI
            decomposition = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at analyzing queries for multimodal RAG systems.
                        
Your task is to decompose user queries into structured plans that will guide:
1. Document retrieval (text + image content)
2. Relevance ranking 
3. Context analysis
4. Answer generation

Consider both textual and visual information needs. Think about what types of diagrams, 
tables, charts, or other visual content might be relevant."""
                    },
                    {
                        "role": "user", 
                        "content": f"""Analyze this query for multimodal RAG processing:

Query: "{context.query}"
Objective: {context.objective}
Constraints: {context.constraints}

Decompose this into a structured plan covering:
- What type of question this is
- Key aspects to search for
- Search strategies (including visual content needs)
- How to rank and evaluate results
- What format the response should take"""
                    }
                ],
                response_model=RAGDecomposition,
                max_retries=2
            )
            
            processing_time = time.time() - start_time
            self.tokens_used += 500  # Estimate for decomposition
            
            self.processing_steps.append(ProcessingStep(
                step_name="query_decomposition",
                agent_name=self.name,
                input_summary=f"Query: {context.query[:100]}...",
                output_summary=f"Type: {decomposition.query_type}, Strategies: {len(decomposition.search_strategies)}",
                processing_time=processing_time,
                tokens_used=500,
                confidence_score=0.9
            ))
            
            self.add_thinking(f"Query decomposed - Type: {decomposition.query_type}, "
                            f"Strategies: {len(decomposition.search_strategies)}")
            
            return decomposition
            
        except Exception as e:
            self.add_thinking(f"Error in query decomposition: {e}")
            # Fallback to simple decomposition
            return self._create_fallback_decomposition(context.query)
    
    async def execute(self, decomposition: RAGDecomposition) -> RAGResult:
        """Execute the complete RAG pipeline with specialized agents."""
        start_time = time.time()
        
        try:
            # Step 1: Retrieve documents using multimodal search
            self.add_thinking("Step 1: Retrieving documents with multimodal search")
            retrieval_context = AgentContext(
                query=decomposition.key_aspects[0] if decomposition.key_aspects else "general search",
                objective="Retrieve relevant multimodal documents",
                metadata={"search_strategies": decomposition.search_strategies}
            )
            
            retrieval_result = await self.retriever.run(retrieval_context)
            candidates = retrieval_result.output
            
            # Step 2: Re-rank documents intelligently
            self.add_thinking("Step 2: Re-ranking documents with multimodal analysis")
            ranking_context = AgentContext(
                query=retrieval_context.query,
                objective="Rank documents by relevance and quality",
                metadata={
                    "candidates": candidates,
                    "ranking_criteria": decomposition.ranking_criteria
                }
            )
            
            ranking_result = await self.reranker.run(ranking_context)
            ranked_docs: RankedDocuments = ranking_result.output
            
            # Step 3: Analyze context quality
            self.add_thinking("Step 3: Analyzing context completeness and quality")
            analysis_context = AgentContext(
                query=retrieval_context.query,
                objective="Analyze context quality and completeness",
                metadata={
                    "ranked_documents": ranked_docs,
                    "visual_requirements": decomposition.visual_requirements,
                    "confidence_threshold": decomposition.confidence_threshold
                }
            )
            
            analysis_result = await self.context_analyzer.run(analysis_context)
            context_analysis: ContextAnalysis = analysis_result.output
            
            # Step 4: Generate answer if context is sufficient
            self.add_thinking(f"Step 4: Context quality check - {context_analysis.recommended_action}")
            
            if context_analysis.recommended_action == "proceed":
                answer_context = AgentContext(
                    query=retrieval_context.query,
                    objective="Generate comprehensive multimodal answer",
                    metadata={
                        "ranked_documents": ranked_docs,
                        "context_analysis": context_analysis,
                        "response_format": decomposition.response_format
                    }
                )
                
                answer_result = await self.answer_generator.run(answer_context)
                final_answer: StructuredAnswer = answer_result.output
                
            elif context_analysis.recommended_action == "partial_answer":
                # Generate partial answer with caveats
                final_answer = await self._generate_partial_answer(
                    ranked_docs, context_analysis, decomposition
                )
            else:
                # Context insufficient - return informative response
                final_answer = await self._generate_insufficient_context_response(
                    context_analysis, decomposition
                )
            
            # Compile processing steps from all agents
            self._compile_processing_steps([
                retrieval_result, ranking_result, analysis_result,
                answer_result if 'answer_result' in locals() else None
            ])
            
            total_processing_time = time.time() - start_time
            total_tokens = sum(step.tokens_used for step in self.processing_steps)
            
            return RAGResult(
                answer=final_answer,
                processing_steps=self.processing_steps,
                total_processing_time=total_processing_time,
                total_tokens_used=total_tokens,
                query_decomposition=decomposition,
                context_analysis=context_analysis,
                ranked_documents=ranked_docs
            )
            
        except Exception as e:
            self.add_thinking(f"Error in RAG execution: {e}")
            raise
    
    def _create_fallback_decomposition(self, query: str) -> RAGDecomposition:
        """Create fallback decomposition when structured analysis fails."""
        from ..models.rag_models import SearchStrategy, RankingCriterion
        
        return RAGDecomposition(
            query_type="factual",
            key_aspects=[query],
            search_strategies=[
                SearchStrategy(
                    primary_queries=[query],
                    fallback_queries=[f"information about {query}"],
                    content_filters=[],
                    max_candidates=10
                )
            ],
            ranking_criteria=[
                RankingCriterion(
                    aspect="relevance",
                    weight=0.8,
                    evaluation_method="semantic_similarity"
                )
            ],
            response_format="conversational"
        )
    
    async def _generate_partial_answer(
        self, 
        ranked_docs: RankedDocuments, 
        context_analysis: ContextAnalysis,
        decomposition: RAGDecomposition
    ) -> StructuredAnswer:
        """Generate partial answer when context is incomplete but usable."""
        
        limited_context = AgentContext(
            query="Generate partial answer with available context",
            objective="Provide what information is available with clear limitations",
            metadata={
                "ranked_documents": ranked_docs,
                "information_gaps": context_analysis.information_gaps,
                "partial_response": True
            }
        )
        
        result = await self.answer_generator.run(limited_context)
        answer = result.output
        
        # Add limitations to the answer
        answer.limitations.extend([
            f"Incomplete information: {gap}" for gap in context_analysis.information_gaps
        ])
        answer.evidence_strength = "low"
        
        return answer
    
    async def _generate_insufficient_context_response(
        self,
        context_analysis: ContextAnalysis,
        decomposition: RAGDecomposition
    ) -> StructuredAnswer:
        """Generate response when context is insufficient."""
        
        return StructuredAnswer(
            main_response=f"I don't have sufficient information to answer your question comprehensively. "
                         f"The available documents don't cover the key aspects you're asking about.",
            evidence_strength="low",
            sources_used=[],
            visual_elements_used=[],
            limitations=[
                "Insufficient context in available documents",
                f"Missing information about: {', '.join(context_analysis.information_gaps)}"
            ],
            follow_up_suggestions=[
                "Try rephrasing your question",
                "Ask about specific aspects separately",
                "Check if additional documents are available"
            ],
            multimodal_confidence=0.0,
            processing_metadata={
                "reason": "insufficient_context",
                "completeness_score": context_analysis.completeness_score
            }
        )
    
    def _compile_processing_steps(self, agent_results: List[Optional[AgentResult]]) -> None:
        """Compile processing steps from all agent results."""
        for result in agent_results:
            if result is None:
                continue
                
            step = ProcessingStep(
                step_name=result.output.__class__.__name__.lower() if hasattr(result.output, '__class__') else "unknown",
                agent_name=getattr(result, 'agent_name', 'unknown'),
                input_summary="Processed by agent",
                output_summary=f"Status: {result.status}",
                processing_time=(result.end_time - result.start_time).total_seconds() if result.end_time else 0.0,
                tokens_used=result.tokens_used,
                confidence_score=0.8  # Default confidence
            )
            self.processing_steps.append(step)