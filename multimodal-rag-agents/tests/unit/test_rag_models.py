"""Tests for RAG models and Pydantic schemas."""

import pytest
from datetime import datetime
from typing import List
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from rag_agents.models.rag_models import (
    RAGDecomposition, SearchStrategy, RankingCriterion,
    DocumentCandidate, RankedDocuments, ContextAnalysis,
    StructuredAnswer, SourceCitation, RAGResult,
    ProcessingStep
)


def test_search_strategy_creation():
    """Test SearchStrategy model creation and validation."""
    strategy = SearchStrategy(
        primary_queries=["multimodal embeddings", "vector search"],
        fallback_queries=["document retrieval", "semantic search"],
        content_filters=["diagrams", "technical"],
        max_candidates=10
    )
    
    assert len(strategy.primary_queries) == 2
    assert "multimodal embeddings" in strategy.primary_queries
    assert len(strategy.fallback_queries) == 2
    assert "diagrams" in strategy.content_filters
    assert strategy.max_candidates == 10


def test_ranking_criterion_creation():
    """Test RankingCriterion model."""
    criterion = RankingCriterion(
        aspect="relevance",
        weight=0.8,
        evaluation_method="similarity_score"
    )
    
    assert criterion.aspect == "relevance"
    assert criterion.weight == 0.8
    assert criterion.evaluation_method == "similarity_score"


def test_rag_decomposition_complete():
    """Test complete RAGDecomposition model."""
    strategy = SearchStrategy(
        primary_queries=["Zep architecture"],
        fallback_queries=["memory system"],
        content_filters=["technical"],
        max_candidates=5
    )
    
    criterion = RankingCriterion(
        aspect="technical_depth",
        weight=0.7,
        evaluation_method="content_analysis"
    )
    
    decomposition = RAGDecomposition(
        query_type="analytical",
        key_aspects=["components", "data flow", "integrations"],
        search_strategies=[strategy],
        ranking_criteria=[criterion],
        visual_requirements=["diagrams", "flowcharts"],
        response_format="detailed"
    )
    
    assert decomposition.query_type == "analytical"
    assert len(decomposition.key_aspects) == 3
    assert "components" in decomposition.key_aspects
    assert len(decomposition.search_strategies) == 1
    assert len(decomposition.ranking_criteria) == 1
    assert "diagrams" in decomposition.visual_requirements
    assert decomposition.response_format == "detailed"


def test_document_candidate_creation():
    """Test DocumentCandidate model."""
    candidate = DocumentCandidate(
        doc_id="doc_123",
        file_path="/path/to/technical_docs.pdf",
        page_num=15,
        doc_source="technical_docs.pdf",
        markdown_text="Technical documentation about system architecture...",
        similarity_score=0.85,
        visual_content_type="text_with_diagrams"
    )
    
    assert candidate.doc_id == "doc_123"
    assert "Technical documentation" in candidate.markdown_text
    assert candidate.page_num == 15
    assert candidate.similarity_score == 0.85
    assert candidate.visual_content_type == "text_with_diagrams"


def test_ranked_documents_creation():
    """Test RankedDocuments model with multiple documents."""
    from rag_agents.models.rag_models import RankingAnalysis
    
    candidates = [
        DocumentCandidate(
            doc_id="doc_1",
            file_path="/path/to/doc1.pdf",
            page_num=1,
            doc_source="doc1.pdf",
            markdown_text="First document",
            similarity_score=0.9,
            visual_content_type="text"
        ),
        DocumentCandidate(
            doc_id="doc_2",
            file_path="/path/to/doc2.pdf", 
            page_num=2,
            doc_source="doc2.pdf",
            markdown_text="Second document",
            similarity_score=0.8,
            visual_content_type="image"
        )
    ]
    
    ranking_analysis = RankingAnalysis(
        document_scores={"doc_1": 0.9, "doc_2": 0.8},
        ranking_rationale="Ranked by relevance and visual content",
        selected_documents=["doc_1", "doc_2"],
        diversity_score=0.7
    )
    
    ranked = RankedDocuments(
        documents=candidates,
        ranking_analysis=ranking_analysis,
        total_candidates_processed=10,
        selection_strategy_used="multimodal_ranking"
    )
    
    assert len(ranked.documents) == 2
    assert ranked.documents[0].similarity_score == 0.9
    assert ranked.ranking_analysis.diversity_score == 0.7
    assert ranked.total_candidates_processed == 10
    assert "relevance" in ranked.ranking_analysis.ranking_rationale


def test_context_analysis_creation():
    """Test ContextAnalysis model."""
    analysis = ContextAnalysis(
        completeness_score=0.8,
        confidence_level="high",
        information_gaps=["missing recent updates", "limited visual examples"],
        conflicting_sources=[],
        visual_coverage=0.6,
        recommended_action="proceed"
    )
    
    assert analysis.completeness_score == 0.8
    assert analysis.confidence_level == "high"
    assert len(analysis.information_gaps) == 2
    assert "missing recent updates" in analysis.information_gaps
    assert len(analysis.conflicting_sources) == 0
    assert analysis.visual_coverage == 0.6
    assert analysis.recommended_action == "proceed"


def test_source_reference_creation():
    """Test SourceCitation model."""
    source = SourceCitation(
        document="system_architecture.pdf",
        page_number=42,
        content_type="diagram_with_text",
        excerpt="Component overview diagram showing system interactions"
    )
    
    assert source.document == "system_architecture.pdf"
    assert source.page_number == 42
    assert source.content_type == "diagram_with_text"
    assert "Component overview" in source.excerpt


def test_structured_answer_creation():
    """Test StructuredAnswer model."""
    sources = [
        SourceCitation(
            document="doc1.pdf",
            page_number=10,
            content_type="text",
            excerpt="Overview of system components"
        ),
        SourceCitation(
            document="doc2.pdf", 
            page_number=25,
            content_type="diagram",
            excerpt="Detailed architecture diagram"
        )
    ]
    
    answer = StructuredAnswer(
        main_response="The system consists of three main components...",
        sources_used=sources,
        multimodal_confidence=0.85,
        evidence_strength="high",
        visual_elements_used=["architecture_diagram", "flow_chart"],
        limitations=["Limited recent data", "Missing performance metrics"],
        follow_up_suggestions=["Review latest updates", "Check performance docs"]
    )
    
    assert "three main components" in answer.main_response
    assert len(answer.sources_used) == 2
    assert answer.multimodal_confidence == 0.85
    assert answer.evidence_strength == "high"
    assert "architecture_diagram" in answer.visual_elements_used
    assert len(answer.limitations) == 2
    assert len(answer.follow_up_suggestions) == 2


def test_processing_step_creation():
    """Test ProcessingStep model."""
    step = ProcessingStep(
        step_name="multimodal_retrieval",
        agent_name="RetrieverAgent",
        input_summary="Query: test query",
        output_summary="Found 5 documents",
        processing_time=2.5,
        tokens_used=300,
        confidence_score=0.8
    )
    
    assert step.step_name == "multimodal_retrieval"
    assert step.agent_name == "RetrieverAgent"
    assert step.input_summary == "Query: test query"
    assert step.output_summary == "Found 5 documents"
    assert step.processing_time == 2.5
    assert step.tokens_used == 300
    assert step.confidence_score == 0.8


def test_rag_result_complete():
    """Test complete RAGResult model with all components."""
    # Create decomposition
    strategy = SearchStrategy(
        primary_queries=["test query"],
        fallback_queries=[],
        content_filters=[],
        max_candidates=5
    )
    
    decomposition = RAGDecomposition(
        query_type="factual",
        key_aspects=["main topic"],
        search_strategies=[strategy],
        ranking_criteria=[],
        visual_requirements=[],
        response_format="conversational"
    )
    
    # Create ranked documents
    doc = DocumentCandidate(
        doc_id="test_doc",
        file_path="/path/to/test.pdf",
        page_num=1,
        doc_source="test.pdf",
        markdown_text="Test content",
        similarity_score=0.8,
        visual_content_type="text"
    )
    
    from rag_agents.models.rag_models import RankingAnalysis
    ranking_analysis = RankingAnalysis(
        document_scores={"test_doc": 0.8},
        ranking_rationale="Test ranking",
        selected_documents=["test_doc"],
        diversity_score=0.5
    )
    
    ranked_docs = RankedDocuments(
        documents=[doc],
        ranking_analysis=ranking_analysis,
        total_candidates_processed=5,
        selection_strategy_used="test_strategy"
    )
    
    # Create context analysis
    context_analysis = ContextAnalysis(
        completeness_score=0.7,
        confidence_level="medium",
        information_gaps=[],
        conflicting_sources=[],
        visual_coverage=0.3,
        recommended_action="proceed"
    )
    
    # Create answer
    answer = StructuredAnswer(
        main_response="Test response",
        sources_used=[],
        multimodal_confidence=0.7,
        evidence_strength="medium",
        visual_elements_used=[],
        limitations=[],
        follow_up_suggestions=[]
    )
    
    # Create processing steps
    step = ProcessingStep(
        step_name="test_step",
        agent_name="TestAgent",
        input_summary="Test input",
        output_summary="Test output",
        processing_time=1.0,
        tokens_used=100,
        confidence_score=0.8
    )
    
    # Create complete RAG result
    rag_result = RAGResult(
        query_decomposition=decomposition,
        ranked_documents=ranked_docs,
        context_analysis=context_analysis,
        answer=answer,
        processing_steps=[step],
        total_processing_time=3.5,
        total_tokens_used=500
    )
    
    assert rag_result.query_decomposition.query_type == "factual"
    assert len(rag_result.ranked_documents.documents) == 1
    assert rag_result.context_analysis.confidence_level == "medium"
    assert "Test response" in rag_result.answer.main_response
    assert len(rag_result.processing_steps) == 1
    assert rag_result.total_processing_time == 3.5
    assert rag_result.total_tokens_used == 500


def test_model_validation_errors():
    """Test that models properly validate required fields."""
    # Test missing required field
    with pytest.raises(ValueError):
        RAGDecomposition(
            # Missing query_type
            key_aspects=["test"],
            search_strategies=[],
            ranking_criteria=[],
            response_format="detailed"
        )
    
    # Test invalid confidence score would be validated by Pydantic
    # but since we don't have validation constraints, we'll test valid creation
    analysis = ContextAnalysis(
        completeness_score=0.8,
        confidence_level="high",
        information_gaps=[],
        conflicting_sources=[],
        visual_coverage=0.5,
        recommended_action="proceed"
    )
    assert analysis.completeness_score == 0.8


def test_model_defaults():
    """Test model default values."""
    # Test SearchStrategy defaults
    strategy = SearchStrategy(
        primary_queries=["test"]
    )
    
    assert strategy.fallback_queries == []
    assert strategy.content_filters == []
    assert strategy.max_candidates == 10
    assert strategy.focus_type == "balanced"
    
    # Test DocumentCandidate defaults
    candidate = DocumentCandidate(
        doc_id="test",
        file_path="/path/to/test.pdf",
        page_num=1,
        doc_source="test.pdf",
        markdown_text="test content",
        similarity_score=0.5
    )
    
    assert candidate.visual_content_type is None