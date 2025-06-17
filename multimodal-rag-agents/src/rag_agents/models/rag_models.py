"""Pydantic models for structured RAG processing with Instructor."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SearchStrategy(BaseModel):
    """Strategy for searching documents."""
    primary_queries: List[str] = Field(description="Main search queries to execute")
    fallback_queries: List[str] = Field(description="Backup queries if primary fails")
    content_filters: List[str] = Field(description="Content type filters (e.g., 'tables', 'diagrams')")
    max_candidates: int = Field(default=10, description="Maximum documents to retrieve")
    focus_type: Literal["textual", "visual", "balanced"] = Field(default="balanced")
    
    
class RankingCriterion(BaseModel):
    """Criterion for ranking documents."""
    aspect: str = Field(description="What aspect to evaluate (e.g., 'relevance', 'visual_content')")
    weight: float = Field(description="Weight for this criterion (0.0-1.0)")
    evaluation_method: str = Field(description="How to evaluate this aspect")


class RAGDecomposition(BaseModel):
    """Structured decomposition of user query for RAG processing."""
    query_type: Literal["factual", "comparative", "analytical", "procedural", "visual"] = Field(
        description="Type of question being asked"
    )
    key_aspects: List[str] = Field(
        description="Key aspects or topics the query is asking about"
    )
    search_strategies: List[SearchStrategy] = Field(
        description="Different search strategies to try"
    )
    ranking_criteria: List[RankingCriterion] = Field(
        description="Criteria for ranking retrieved documents"
    )
    response_format: Literal["detailed", "summary", "structured", "conversational"] = Field(
        description="Desired format for the response"
    )
    visual_requirements: List[str] = Field(
        default_factory=list,
        description="Types of visual content needed (diagrams, tables, etc.)"
    )
    confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence needed to provide answer"
    )


class DocumentCandidate(BaseModel):
    """A candidate document from retrieval."""
    doc_id: str
    file_path: str
    page_num: int
    doc_source: str
    markdown_text: str
    similarity_score: float
    visual_content_type: Optional[str] = None
    

class RankingAnalysis(BaseModel):
    """Analysis of document ranking."""
    document_scores: Dict[str, float] = Field(description="Score for each document")
    ranking_rationale: str = Field(description="Explanation of ranking decisions")
    selected_documents: List[str] = Field(description="IDs of selected documents")
    diversity_score: float = Field(description="How diverse the selected set is")
    

class ContextAnalysis(BaseModel):
    """Analysis of retrieved context quality."""
    completeness_score: float = Field(description="How complete the context is (0.0-1.0)")
    confidence_level: Literal["high", "medium", "low"] = Field(
        description="Overall confidence in the context"
    )
    information_gaps: List[str] = Field(
        description="What information is missing"
    )
    conflicting_sources: List[str] = Field(
        description="Sources that provide conflicting information"
    )
    visual_coverage: float = Field(
        description="How well visual requirements are covered (0.0-1.0)"
    )
    recommended_action: Literal["proceed", "search_more", "partial_answer"] = Field(
        description="What to do next based on context quality"
    )


class SourceCitation(BaseModel):
    """Citation for a source used in the answer."""
    document: str = Field(description="Document name")
    page_number: int = Field(description="Page number")
    content_type: str = Field(description="Type of content (text, image, table, etc.)")
    excerpt: str = Field(description="Brief excerpt from the source")


class StructuredAnswer(BaseModel):
    """Structured answer with evidence and metadata."""
    main_response: str = Field(description="The primary answer to the question")
    evidence_strength: Literal["high", "medium", "low"] = Field(
        description="How strong the evidence is for this answer"
    )
    sources_used: List[SourceCitation] = Field(
        description="Sources that support this answer"
    )
    visual_elements_used: List[str] = Field(
        description="Visual elements referenced in the answer"
    )
    limitations: List[str] = Field(
        description="Limitations or caveats about this answer"
    )
    follow_up_suggestions: List[str] = Field(
        description="Suggested follow-up questions"
    )
    multimodal_confidence: float = Field(
        description="Confidence score for multimodal aspects (0.0-1.0)"
    )
    processing_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about how this answer was generated"
    )


class QueryContext(BaseModel):
    """Extended context for query processing."""
    original_query: str
    processed_query: str
    user_intent: str
    domain_context: Optional[str] = None
    conversation_history: List[str] = Field(default_factory=list)
    preferred_sources: List[str] = Field(default_factory=list)
    exclude_sources: List[str] = Field(default_factory=list)
    

class MultimodalSearchPlan(BaseModel):
    """Plan for multimodal search execution."""
    text_queries: List[str] = Field(description="Text-based search queries")
    visual_concepts: List[str] = Field(description="Visual concepts to prioritize")
    embedding_strategy: str = Field(description="How to generate embeddings")
    retrieval_params: Dict[str, Any] = Field(description="Parameters for retrieval")
    
    
class VisualAnalysis(BaseModel):
    """Analysis of visual content in documents."""
    visual_relevance_score: float = Field(description="How visually relevant (0.0-1.0)")
    content_types_found: List[str] = Field(description="Types of visual content found")
    visual_quality_score: float = Field(description="Quality of visual content (0.0-1.0)")
    text_image_alignment: float = Field(description="How well text and images align (0.0-1.0)")
    visual_summary: str = Field(description="Summary of visual content")
    

class RankedDocuments(BaseModel):
    """Documents ranked by relevance and quality."""
    documents: List[DocumentCandidate] = Field(description="Ranked list of documents")
    ranking_analysis: RankingAnalysis = Field(description="Analysis of ranking process")
    total_candidates_processed: int = Field(description="Total candidates considered")
    selection_strategy_used: str = Field(description="Strategy used for selection")
    

class ProcessingStep(BaseModel):
    """A step in the RAG processing pipeline."""
    step_name: str
    agent_name: str
    input_summary: str
    output_summary: str
    processing_time: float
    tokens_used: int
    confidence_score: float
    

class RAGResult(BaseModel):
    """Complete result from RAG processing."""
    answer: StructuredAnswer
    processing_steps: List[ProcessingStep] = Field(description="Steps taken to generate answer")
    total_processing_time: float
    total_tokens_used: int
    query_decomposition: RAGDecomposition
    context_analysis: ContextAnalysis
    ranked_documents: RankedDocuments