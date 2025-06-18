"""Multimodal reranker agent using OpenAI for intelligent document ranking."""

import asyncio
import time
from typing import List, Optional, Dict, Any
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from ..agents.base import Agent, AgentContext
from ..models.rag_models import (
    DocumentCandidate, RankedDocuments, RankingAnalysis, 
    RankingCriterion, VisualAnalysis
)


class MultimodalRankingDecision(BaseModel):
    """Structured decision for document ranking using Instructor."""
    selected_document_ids: List[str]
    ranking_scores: Dict[str, float]
    ranking_rationale: str
    diversity_assessment: str
    visual_content_priority: List[str]
    recommended_count: int


class RerankerConfig(BaseModel):
    """Configuration for multimodal reranker."""
    openai_api_key: Optional[str] = None
    model: str = "gpt-4o"
    max_tokens: int = 2048
    max_documents_to_analyze: int = 15
    target_selection_count: int = 5
    
    @classmethod
    def from_env(cls, config_manager=None):
        """Create config from environment variables."""
        import os
        if config_manager:
            return cls(
                openai_api_key=config_manager.get("OPENAI_API_KEY"),
                model=config_manager.get("RERANKER_MODEL", "gpt-4o"),
                max_tokens=int(config_manager.get("MAX_TOKENS_RERANK", "2048"))
            )
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("RERANKER_MODEL", "gpt-4o"),
            max_tokens=int(os.getenv("MAX_TOKENS_RERANK", "2048"))
        )


class MultimodalRerankerAgent(Agent[RankedDocuments]):
    """Agent that re-ranks documents using multimodal analysis with OpenAI."""
    
    def __init__(self, config: Optional[RerankerConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or RerankerConfig()
        
        # Initialize OpenAI client with Instructor
        client = AsyncOpenAI(api_key=self.config.openai_api_key)
        self.client = instructor.from_openai(client)
        
    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        """Plan the reranking strategy based on context."""
        self.add_thinking("Planning multimodal reranking strategy")
        
        candidates: List[DocumentCandidate] = context.metadata.get("candidates", [])
        ranking_criteria: List[RankingCriterion] = context.metadata.get("ranking_criteria", [])
        
        # Limit candidates to avoid token overflow
        limited_candidates = candidates[:self.config.max_documents_to_analyze]
        
        plan = {
            "candidates": limited_candidates,
            "ranking_criteria": ranking_criteria,
            "analysis_strategy": "multimodal_combined",
            "target_count": min(self.config.target_selection_count, len(limited_candidates))
        }
        
        self.add_thinking(f"Reranking plan: {len(limited_candidates)} candidates, "
                         f"target {plan['target_count']} selections")
        return plan
    
    async def execute(self, plan: Dict[str, Any]) -> RankedDocuments:
        """Execute intelligent multimodal reranking."""
        candidates = plan["candidates"]
        
        if not candidates:
            return RankedDocuments(
                documents=[],
                ranking_analysis=RankingAnalysis(
                    document_scores={},
                    ranking_rationale="No candidates provided",
                    selected_documents=[],
                    diversity_score=0.0
                ),
                total_candidates_processed=0,
                selection_strategy_used="none"
            )
        
        # Step 1: Analyze visual content of candidates
        self.add_thinking("Step 1: Analyzing visual content of candidates")
        visual_analyses = await self._analyze_visual_content(candidates)
        
        # Step 2: Perform intelligent ranking using OpenAI with Instructor
        self.add_thinking("Step 2: Performing intelligent multimodal ranking")
        ranking_decision = await self._perform_intelligent_ranking(
            candidates, visual_analyses, plan
        )
        
        # Step 3: Compile final ranked results
        self.add_thinking("Step 3: Compiling final ranked results")
        ranked_docs = self._compile_ranked_results(
            candidates, ranking_decision, visual_analyses
        )
        
        return ranked_docs
    
    async def _analyze_visual_content(
        self, 
        candidates: List[DocumentCandidate]
    ) -> Dict[str, VisualAnalysis]:
        """Analyze visual content of candidate documents."""
        visual_analyses = {}
        
        for candidate in candidates:
            try:
                # Encode image if available
                from .retriever import MultimodalRetrieverAgent
                image_b64 = MultimodalRetrieverAgent.encode_image_to_base64(candidate.file_path)
                
                if image_b64:
                    analysis = await self._analyze_single_image(candidate, image_b64)
                    visual_analyses[candidate.doc_id] = analysis
                else:
                    # Text-only analysis
                    visual_analyses[candidate.doc_id] = VisualAnalysis(
                        visual_relevance_score=0.0,
                        content_types_found=["text_only"],
                        visual_quality_score=0.0,
                        text_image_alignment=0.0,
                        visual_summary="No visual content available"
                    )
                    
            except Exception as e:
                self.add_thinking(f"Visual analysis failed for {candidate.doc_id}: {e}")
                visual_analyses[candidate.doc_id] = VisualAnalysis(
                    visual_relevance_score=0.0,
                    content_types_found=["analysis_failed"],
                    visual_quality_score=0.0,
                    text_image_alignment=0.0,
                    visual_summary="Analysis failed"
                )
        
        return visual_analyses
    
    async def _analyze_single_image(
        self, 
        candidate: DocumentCandidate, 
        image_b64: str
    ) -> VisualAnalysis:
        """Analyze a single image using OpenAI Vision."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analyze this image for a RAG system. The associated text is: "{candidate.markdown_text[:200]}..."
                                
Please provide a structured analysis of:
1. Visual relevance score (0.0-1.0)
2. Types of visual content found
3. Visual quality score (0.0-1.0) 
4. How well text and image align (0.0-1.0)
5. Brief visual summary"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                response_model=VisualAnalysis,
                max_retries=1
            )
            
            return response
            
        except Exception as e:
            self.add_thinking(f"Image analysis failed: {e}")
            return VisualAnalysis(
                visual_relevance_score=0.5,
                content_types_found=["unknown"],
                visual_quality_score=0.5,
                text_image_alignment=0.5,
                visual_summary="Analysis unavailable"
            )
    
    async def _perform_intelligent_ranking(
        self,
        candidates: List[DocumentCandidate],
        visual_analyses: Dict[str, VisualAnalysis],
        plan: Dict[str, Any]
    ) -> MultimodalRankingDecision:
        """Perform intelligent ranking using OpenAI with Instructor."""
        
        # Prepare candidate information for the LLM
        candidate_info = []
        for candidate in candidates:
            visual_analysis = visual_analyses.get(candidate.doc_id)
            
            info = {
                "id": candidate.doc_id,
                "page": candidate.page_num,
                "source": candidate.doc_source,
                "similarity_score": candidate.similarity_score,
                "text_preview": candidate.markdown_text[:300],
                "visual_summary": visual_analysis.visual_summary if visual_analysis else "No visual analysis",
                "visual_relevance": visual_analysis.visual_relevance_score if visual_analysis else 0.0,
                "content_types": visual_analysis.content_types_found if visual_analysis else []
            }
            candidate_info.append(info)
        
        # Get structured ranking decision from OpenAI
        try:
            decision = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at ranking documents for multimodal RAG systems.
                        
Your task is to intelligently select and rank the most relevant documents considering:
1. Semantic relevance (similarity scores)
2. Visual content quality and relevance  
3. Diversity of information
4. Complementarity between text and images
5. Coverage of different aspects

Prioritize documents that:
- Have high semantic relevance
- Contain useful visual elements (diagrams, tables, charts)
- Provide diverse perspectives or information
- Have good text-image alignment"""
                    },
                    {
                        "role": "user",
                        "content": f"""Rank these {len(candidate_info)} documents for the query.

Target selection count: {plan['target_count']}

Candidates:
{self._format_candidates_for_llm(candidate_info)}

Select the best documents considering both textual and visual relevance. 
Explain your ranking rationale and assess diversity."""
                    }
                ],
                response_model=MultimodalRankingDecision,
                max_retries=2
            )
            
            return decision
            
        except Exception as e:
            self.add_thinking(f"Intelligent ranking failed: {e}")
            # Fallback to similarity-based ranking
            return self._fallback_ranking(candidates, plan['target_count'])
    
    def _format_candidates_for_llm(self, candidate_info: List[Dict]) -> str:
        """Format candidate information for LLM processing."""
        formatted = []
        for i, info in enumerate(candidate_info, 1):
            formatted.append(f"""
Document {i} (ID: {info['id']}):
- Source: {info['source']}, Page: {info['page']}
- Similarity Score: {info['similarity_score']:.3f}
- Visual Relevance: {info['visual_relevance']:.2f}
- Content Types: {', '.join(info['content_types'])}
- Text Preview: {info['text_preview']}...
- Visual Summary: {info['visual_summary']}
""")
        return "\n".join(formatted)
    
    def _fallback_ranking(
        self, 
        candidates: List[DocumentCandidate], 
        target_count: int
    ) -> MultimodalRankingDecision:
        """Fallback ranking based on similarity scores."""
        sorted_candidates = sorted(candidates, key=lambda x: x.similarity_score, reverse=True)
        selected = sorted_candidates[:target_count]
        
        return MultimodalRankingDecision(
            selected_document_ids=[doc.doc_id for doc in selected],
            ranking_scores={doc.doc_id: doc.similarity_score for doc in selected},
            ranking_rationale="Fallback ranking based on similarity scores only",
            diversity_assessment="Not assessed in fallback mode",
            visual_content_priority=[],
            recommended_count=len(selected)
        )
    
    def _compile_ranked_results(
        self,
        candidates: List[DocumentCandidate],
        decision: MultimodalRankingDecision,
        visual_analyses: Dict[str, VisualAnalysis]
    ) -> RankedDocuments:
        """Compile final ranked results."""
        
        # Get selected documents in rank order
        selected_docs = []
        candidates_by_id = {doc.doc_id: doc for doc in candidates}
        
        for doc_id in decision.selected_document_ids:
            if doc_id in candidates_by_id:
                selected_docs.append(candidates_by_id[doc_id])
        
        # Create ranking analysis
        ranking_analysis = RankingAnalysis(
            document_scores=decision.ranking_scores,
            ranking_rationale=decision.ranking_rationale,
            selected_documents=decision.selected_document_ids,
            diversity_score=len(set(doc.doc_source for doc in selected_docs)) / len(selected_docs) if selected_docs else 0.0
        )
        
        return RankedDocuments(
            documents=selected_docs,
            ranking_analysis=ranking_analysis,
            total_candidates_processed=len(candidates),
            selection_strategy_used="multimodal_intelligent_ranking"
        )