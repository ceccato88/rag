"""Context analyzer agent that evaluates the quality and completeness of retrieved context."""

import time
from typing import List, Optional, Dict, Any
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from ..agents.base import Agent, AgentContext
from ..models.rag_models import (
    RankedDocuments, ContextAnalysis, DocumentCandidate
)


class ContextQualityAssessment(BaseModel):
    """Structured assessment of context quality using Instructor."""
    completeness_score: float
    confidence_level: str
    information_gaps: List[str]
    conflicting_sources: List[str]
    visual_coverage_score: float
    coverage_analysis: str
    recommended_action: str
    reasoning: str


class ContextAnalyzerConfig(BaseModel):
    """Configuration for context analyzer."""
    openai_api_key: Optional[str] = None
    model: str = "gpt-4o"
    max_tokens: int = 1024
    completeness_threshold: float = 0.7
    confidence_threshold: float = 0.6
    
    @classmethod
    def from_env(cls, config_manager=None):
        """Create config from environment variables."""
        import os
        if config_manager:
            return cls(
                openai_api_key=config_manager.get("OPENAI_API_KEY"),
                model=config_manager.get("CONTEXT_ANALYZER_MODEL", "gpt-4o"),
                max_tokens=int(config_manager.get("MAX_TOKENS_CONTEXT_ANALYSIS", "1024"))
            )
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("CONTEXT_ANALYZER_MODEL", "gpt-4o"),
            max_tokens=int(os.getenv("MAX_TOKENS_CONTEXT_ANALYSIS", "1024"))
        )


class ContextAnalyzerAgent(Agent[ContextAnalysis]):
    """Agent that analyzes context quality and completeness for RAG responses."""
    
    def __init__(self, config: Optional[ContextAnalyzerConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or ContextAnalyzerConfig()
        
        # Initialize OpenAI client with Instructor
        client = AsyncOpenAI(api_key=self.config.openai_api_key)
        self.client = instructor.from_openai(client)
    
    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        """Plan context analysis strategy."""
        self.add_thinking("Planning context quality analysis")
        
        ranked_docs: RankedDocuments = context.metadata.get("ranked_documents")
        visual_requirements: List[str] = context.metadata.get("visual_requirements", [])
        confidence_threshold: float = context.metadata.get("confidence_threshold", 0.7)
        
        plan = {
            "ranked_documents": ranked_docs,
            "visual_requirements": visual_requirements,
            "confidence_threshold": confidence_threshold,
            "analysis_aspects": [
                "completeness",
                "consistency", 
                "visual_coverage",
                "information_quality"
            ]
        }
        
        self.add_thinking(f"Analysis plan: {len(ranked_docs.documents) if ranked_docs else 0} documents, "
                         f"{len(visual_requirements)} visual requirements")
        return plan
    
    async def execute(self, plan: Dict[str, Any]) -> ContextAnalysis:
        """Execute comprehensive context analysis."""
        ranked_docs: RankedDocuments = plan["ranked_documents"]
        
        if not ranked_docs or not ranked_docs.documents:
            return self._create_empty_context_analysis()
        
        # Step 1: Analyze completeness and quality
        self.add_thinking("Analyzing context completeness and quality")
        quality_assessment = await self._assess_context_quality(
            ranked_docs.documents, plan
        )
        
        # Step 2: Check visual coverage
        self.add_thinking("Evaluating visual content coverage")
        visual_coverage = self._evaluate_visual_coverage(
            ranked_docs.documents, plan["visual_requirements"]
        )
        
        # Step 3: Detect conflicts and inconsistencies
        self.add_thinking("Checking for conflicts and inconsistencies")
        conflicts = await self._detect_conflicts(ranked_docs.documents)
        
        # Step 4: Make final recommendation
        recommendation = self._make_recommendation(
            quality_assessment, visual_coverage, plan["confidence_threshold"]
        )
        
        return ContextAnalysis(
            completeness_score=quality_assessment.completeness_score,
            confidence_level=quality_assessment.confidence_level,
            information_gaps=quality_assessment.information_gaps,
            conflicting_sources=conflicts,
            visual_coverage=visual_coverage,
            recommended_action=recommendation
        )
    
    async def _assess_context_quality(
        self, 
        documents: List[DocumentCandidate],
        plan: Dict[str, Any]
    ) -> ContextQualityAssessment:
        """Assess overall context quality using OpenAI with Instructor."""
        
        # Prepare document summaries for analysis
        doc_summaries = []
        for i, doc in enumerate(documents, 1):
            summary = f"""
Document {i} (Page {doc.page_num} from {doc.doc_source}):
Similarity: {doc.similarity_score:.3f}
Content: {doc.markdown_text[:400]}...
Visual Type: {doc.visual_content_type or 'text'}
"""
            doc_summaries.append(summary)
        
        combined_content = "\n".join(doc_summaries)
        
        try:
            assessment = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at evaluating context quality for RAG systems.

Analyze the provided documents and assess:
1. Completeness: How well do the documents cover the information needed?
2. Quality: How reliable and detailed is the information?
3. Gaps: What important information is missing?
4. Visual coverage: How well are visual information needs met?

Use these guidelines:
- Completeness score 0.8-1.0: Comprehensive coverage
- Completeness score 0.6-0.8: Good coverage with minor gaps  
- Completeness score 0.4-0.6: Partial coverage with significant gaps
- Completeness score 0.0-0.4: Poor coverage with major gaps

Confidence levels:
- "high": Strong, consistent information from multiple sources
- "medium": Good information but some uncertainty or single source
- "low": Weak or inconsistent information"""
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this context for completeness and quality:

Query Context: {plan.get('query_context', 'General analysis')}
Visual Requirements: {plan.get('visual_requirements', [])}

Documents to analyze:
{combined_content}

Provide a comprehensive quality assessment."""
                    }
                ],
                response_model=ContextQualityAssessment,
                max_retries=2
            )
            
            return assessment
            
        except Exception as e:
            self.add_thinking(f"Context quality assessment failed: {e}")
            return self._create_fallback_assessment(documents)
    
    def _evaluate_visual_coverage(
        self, 
        documents: List[DocumentCandidate],
        visual_requirements: List[str]
    ) -> float:
        """Evaluate how well visual requirements are covered."""
        if not visual_requirements:
            return 1.0  # No visual requirements means perfect coverage
        
        # Count visual content types found
        visual_types_found = set()
        for doc in documents:
            if doc.visual_content_type:
                visual_types_found.add(doc.visual_content_type)
        
        # Check coverage of requirements
        covered_requirements = 0
        for requirement in visual_requirements:
            requirement_lower = requirement.lower()
            if any(req_term in requirement_lower for req_term in visual_types_found):
                covered_requirements += 1
        
        coverage_score = covered_requirements / len(visual_requirements) if visual_requirements else 1.0
        
        self.add_thinking(f"Visual coverage: {covered_requirements}/{len(visual_requirements)} "
                         f"requirements met (score: {coverage_score:.2f})")
        
        return coverage_score
    
    async def _detect_conflicts(self, documents: List[DocumentCandidate]) -> List[str]:
        """Detect potential conflicts between sources."""
        if len(documents) < 2:
            return []
        
        # Simple conflict detection based on source diversity
        sources = [doc.doc_source for doc in documents]
        unique_sources = set(sources)
        
        conflicts = []
        
        # If all documents are from the same source, no conflicts expected
        if len(unique_sources) == 1:
            return conflicts
        
        # For now, implement basic conflict detection
        # In a more sophisticated version, this would use LLM analysis
        if len(unique_sources) > 1:
            # Check for significantly different similarity scores from different sources
            source_scores = {}
            for doc in documents:
                if doc.doc_source not in source_scores:
                    source_scores[doc.doc_source] = []
                source_scores[doc.doc_source].append(doc.similarity_score)
            
            # Detect if sources have very different average scores
            avg_scores = {source: sum(scores)/len(scores) 
                         for source, scores in source_scores.items()}
            
            max_score = max(avg_scores.values())
            min_score = min(avg_scores.values())
            
            if max_score - min_score > 0.3:  # Significant difference
                conflicts.append("Significant difference in relevance between sources")
        
        return conflicts
    
    def _make_recommendation(
        self, 
        assessment: ContextQualityAssessment,
        visual_coverage: float,
        confidence_threshold: float
    ) -> str:
        """Make recommendation based on analysis."""
        
        # Calculate overall quality score
        overall_score = (assessment.completeness_score + visual_coverage) / 2
        
        if overall_score >= confidence_threshold and assessment.confidence_level == "high":
            return "proceed"
        elif overall_score >= 0.5 and assessment.confidence_level in ["medium", "high"]:
            return "partial_answer"
        else:
            return "search_more"
    
    def _create_empty_context_analysis(self) -> ContextAnalysis:
        """Create analysis for empty context."""
        return ContextAnalysis(
            completeness_score=0.0,
            confidence_level="low",
            information_gaps=["No documents retrieved"],
            conflicting_sources=[],
            visual_coverage=0.0,
            recommended_action="search_more"
        )
    
    def _create_fallback_assessment(
        self, 
        documents: List[DocumentCandidate]
    ) -> ContextQualityAssessment:
        """Create fallback assessment when LLM analysis fails."""
        # Simple fallback based on similarity scores and document count
        avg_similarity = sum(doc.similarity_score for doc in documents) / len(documents)
        
        completeness = min(avg_similarity * len(documents) / 3, 1.0)  # Rough heuristic
        
        return ContextQualityAssessment(
            completeness_score=completeness,
            confidence_level="medium" if completeness > 0.6 else "low",
            information_gaps=["Assessment unavailable - using fallback"],
            conflicting_sources=[],
            visual_coverage_score=0.5,  # Neutral assumption
            coverage_analysis="Fallback analysis based on similarity scores",
            recommended_action="proceed" if completeness > 0.7 else "partial_answer",
            reasoning="Fallback assessment due to analysis failure"
        )