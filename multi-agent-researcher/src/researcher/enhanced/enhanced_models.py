#!/usr/bin/env python3
"""
Modelos Enhanced baseados no sistema original, adaptados para RAG vetorial
Combina a sofisticação do sistema original com nossa arquitetura RAG atual
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS E TIPOS BÁSICOS
# =============================================================================

class QueryComplexity(str, Enum):
    """Complexidade da query adaptada para RAG"""
    SIMPLE = "simple"           # 1 specialist, busca direta
    MODERATE = "moderate"       # 1-2 specialists, 2-3 focus areas
    COMPLEX = "complex"         # 2-3 specialists, estratégia coordenada
    VERY_COMPLEX = "very_complex"  # 3+ specialists, decomposição completa

class RAGSearchStrategy(str, Enum):
    """Estratégias de busca adaptadas para RAG vetorial"""
    DIRECT_SEARCH = "direct_search"                    # Busca direta simples
    SEMANTIC_EXPANSION = "semantic_expansion"          # Expandir semanticamente
    ITERATIVE_REFINEMENT = "iterative_refinement"     # Refinar iterativamente
    MULTI_PERSPECTIVE = "multi_perspective"           # Múltiplas perspectivas
    COMPREHENSIVE_COVERAGE = "comprehensive_coverage" # Cobertura completa
    FOCUSED_DEEP_DIVE = "focused_deep_dive"          # Mergulho profundo

class DocumentRelevance(str, Enum):
    """Níveis de relevância de documentos"""
    HIGHLY_RELEVANT = "highly_relevant"
    RELEVANT = "relevant" 
    SOMEWHAT_RELEVANT = "somewhat_relevant"
    NOT_RELEVANT = "not_relevant"

class SpecialistType(str, Enum):
    """Tipos de especialistas adaptados"""
    GENERAL = "general"
    CONCEPTUAL = "conceptual"
    COMPARATIVE = "comparative"
    TECHNICAL = "technical"
    EXAMPLES = "examples"


# =============================================================================
# MODELOS DE TAREFA E ESPECIFICAÇÃO
# =============================================================================

class RAGSubagentTaskSpec(BaseModel):
    """Especificação de tarefa para subagente RAG (adaptado do sistema original)"""
    
    specialist_type: SpecialistType = Field(
        description="Tipo de especialista que executará a tarefa"
    )
    
    focus_areas: List[str] = Field(
        description="Áreas específicas de foco para a busca vetorial",
        min_length=1
    )
    
    search_keywords: List[str] = Field(
        description="Palavras-chave específicas para busca vetorial",
        min_length=1
    )
    
    semantic_context: str = Field(
        description="Contexto semântico para melhorar a busca vetorial"
    )
    
    expected_findings: str = Field(
        description="Tipos de informações esperadas dos documentos"
    )
    
    similarity_threshold: float = Field(
        default=0.65,  # Otimizado: mais permissivo que sistema atual
        ge=0.1, le=1.0,
        description="Threshold mínimo de similaridade para documentos"
    )
    
    max_candidates: int = Field(
        default=3,  # Otimizado: 2-5 páginas diretas (sem reranking)
        ge=2, le=5,  # Limite ajustado para performance
        description="Máximo de páginas diretas da busca por similaridade"
    )
    
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Prioridade da tarefa"
    )
    
    iterative_refinement: bool = Field(
        default=False,
        description="Se deve usar refinamento iterativo"
    )

class RAGApproach(BaseModel):
    """Abordagem de pesquisa RAG (adaptado do sistema original)"""
    
    complexity: QueryComplexity = Field(
        description="Complexidade determinada da query"
    )
    
    strategy: RAGSearchStrategy = Field(
        description="Estratégia principal de busca vetorial"
    )
    
    estimated_subagents: int = Field(
        ge=1, le=5,
        description="Número estimado de subagentes necessários"
    )
    
    approach_steps: List[str] = Field(
        description="Passos sequenciais da abordagem de pesquisa"
    )
    
    key_aspects: List[str] = Field(
        description="Aspectos-chave a serem investigados"
    )
    
    document_types_needed: List[str] = Field(
        description="Tipos de documentos/seções mais relevantes"
    )
    
    reranking_strategy: str = Field(
        description="Estratégia específica de reranking para esta query"
    )
    
    synthesis_approach: str = Field(
        description="Como sintetizar os resultados dos subagentes"
    )


# =============================================================================
# DECOMPOSIÇÃO ESTRUTURADA
# =============================================================================

class RAGDecomposition(BaseModel):
    """Decomposição estruturada para pesquisa RAG (inspirado no sistema original)"""
    
    original_query: str = Field(
        description="Query original do usuário"
    )
    
    refined_query: str = Field(
        description="Query refinada para melhor busca vetorial"
    )
    
    approach: RAGApproach = Field(
        description="Abordagem determinada para a pesquisa"
    )
    
    subagent_tasks: List[RAGSubagentTaskSpec] = Field(
        description="Tarefas específicas para cada subagente",
        min_length=1
    )
    
    global_context: str = Field(
        description="Contexto global para todos os subagentes"
    )
    
    synthesis_instructions: str = Field(
        description="Instruções específicas para síntese final"
    )
    
    quality_criteria: List[str] = Field(
        description="Critérios de qualidade para avaliar resultados"
    )
    
    fallback_strategy: Optional[str] = Field(
        default=None,
        description="Estratégia de fallback se busca principal falhar"
    )


# =============================================================================
# AVALIAÇÃO E RESULTADOS
# =============================================================================

class DocumentEvaluation(BaseModel):
    """Avaliação de documento individual"""
    
    document_id: str = Field(description="ID do documento")
    page_number: int = Field(description="Número da página")
    similarity_score: float = Field(description="Score de similaridade original")
    
    relevance_level: DocumentRelevance = Field(
        description="Nível de relevância avaliado"
    )
    
    key_findings: List[str] = Field(
        description="Descobertas-chave extraídas do documento"
    )
    
    coverage_areas: List[str] = Field(
        description="Áreas da query que este documento cobre"
    )
    
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Score de qualidade do conteúdo (0-1)"
    )
    
    extraction_summary: str = Field(
        description="Resumo do que foi extraído"
    )

class RAGSearchEvaluation(BaseModel):
    """Avaliação de resultados de busca RAG (adaptado do sistema original)"""
    
    task_spec: RAGSubagentTaskSpec = Field(
        description="Especificação da tarefa original"
    )
    
    documents_evaluated: List[DocumentEvaluation] = Field(
        description="Avaliação de cada documento encontrado"
    )
    
    overall_relevance_score: float = Field(
        ge=0.0, le=1.0,
        description="Score geral de relevância dos resultados"
    )
    
    coverage_completeness: float = Field(
        ge=0.0, le=1.0,
        description="Quão completa foi a cobertura da query"
    )
    
    gaps_identified: List[str] = Field(
        description="Lacunas identificadas nos resultados"
    )
    
    refinement_suggestions: List[str] = Field(
        description="Sugestões para refinar a busca"
    )
    
    sufficient_information: bool = Field(
        description="Se as informações são suficientes para responder"
    )
    
    next_search_keywords: List[str] = Field(
        description="Palavras-chave para próxima iteração (se necessário)"
    )
    
    synthesis_guidance: str = Field(
        description="Orientação para síntese baseada nos achados"
    )

class SubagentResult(BaseModel):
    """Resultado de um subagente específico"""
    
    specialist_type: SpecialistType = Field(
        description="Tipo do especialista que executou"
    )
    
    task_completed: RAGSubagentTaskSpec = Field(
        description="Tarefa que foi executada"
    )
    
    search_evaluation: RAGSearchEvaluation = Field(
        description="Avaliação da busca realizada"
    )
    
    extracted_information: str = Field(
        description="Informação extraída e processada"
    )
    
    confidence_level: float = Field(
        ge=0.0, le=1.0,
        description="Nível de confiança nos resultados"
    )
    
    sources_used: List[Dict[str, Any]] = Field(
        description="Documentos/páginas utilizados como fonte"
    )
    
    processing_time: float = Field(
        description="Tempo de processamento em segundos"
    )
    
    iterations_performed: int = Field(
        default=1,
        description="Número de iterações realizadas"
    )


# =============================================================================
# SÍNTESE COORDENADA
# =============================================================================

class SynthesisInstructions(BaseModel):
    """Instruções específicas para síntese (inspirado no sistema original)"""
    
    synthesis_approach: str = Field(
        description="Abordagem geral de síntese"
    )
    
    priority_aspects: List[str] = Field(
        description="Aspectos que devem ter prioridade na síntese"
    )
    
    integration_strategy: str = Field(
        description="Como integrar resultados de diferentes especialistas"
    )
    
    conflict_resolution: str = Field(
        description="Como resolver conflitos entre especialistas"
    )
    
    output_format: str = Field(
        description="Formato desejado para a resposta final"
    )
    
    quality_checks: List[str] = Field(
        description="Verificações de qualidade a serem aplicadas"
    )
    
    citation_requirements: str = Field(
        description="Como citar as fontes na resposta final"
    )

class EnhancedRAGResult(BaseModel):
    """Resultado final do sistema RAG enhanced"""
    
    original_query: str = Field(
        description="Query original do usuário"
    )
    
    decomposition_used: RAGDecomposition = Field(
        description="Decomposição que foi aplicada"
    )
    
    subagent_results: List[SubagentResult] = Field(
        description="Resultados de todos os subagentes"
    )
    
    synthesis_instructions: SynthesisInstructions = Field(
        description="Instruções aplicadas para síntese"
    )
    
    final_answer: str = Field(
        description="Resposta final sintetizada"
    )
    
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Score de confiança geral"
    )
    
    sources_cited: List[Dict[str, Any]] = Field(
        description="Todas as fontes citadas na resposta"
    )
    
    total_processing_time: float = Field(
        description="Tempo total de processamento"
    )
    
    quality_metrics: Dict[str, float] = Field(
        description="Métricas de qualidade da resposta"
    )
    
    reasoning_trace: List[str] = Field(
        description="Trace do raciocínio aplicado"
    )


# =============================================================================
# VALIDAÇÕES ESPECÍFICAS
# =============================================================================

class RAGDecomposition(RAGDecomposition):
    """Versão com validações específicas"""
    
    @field_validator('subagent_tasks')
    @classmethod
    def validate_task_distribution(cls, v):
        """Valida distribuição equilibrada de tarefas"""
        if not v:
            raise ValueError("Pelo menos uma tarefa deve ser definida")
        
        # Verificar se há especialistas duplicados desnecessários
        specialist_types = [task.specialist_type for task in v]
        if len(specialist_types) != len(set(specialist_types)) and len(v) > 3:
            raise ValueError("Muitos especialistas duplicados para query complexa")
        
        return v
    
    @field_validator('approach')
    @classmethod
    def validate_approach_consistency(cls, v):
        """Valida consistência da abordagem"""
        if v.complexity == QueryComplexity.SIMPLE and v.estimated_subagents > 1:
            raise ValueError("Query simples não deve ter múltiplos subagentes")
        
        if v.complexity == QueryComplexity.VERY_COMPLEX and v.estimated_subagents < 2:
            raise ValueError("Query muito complexa deve ter múltiplos subagentes")
        
        return v


# =============================================================================
# FACTORY E HELPERS
# =============================================================================

class RAGTaskFactory:
    """Factory para criar tarefas RAG baseadas no sistema original"""
    
    @staticmethod
    def create_simple_task(query: str, specialist_type: SpecialistType) -> RAGSubagentTaskSpec:
        """Cria tarefa simples para query direta"""
        return RAGSubagentTaskSpec(
            specialist_type=specialist_type,
            focus_areas=["general"],
            search_keywords=[query],
            semantic_context=f"Direct search for: {query}",
            expected_findings="Direct answer to user query",
            similarity_threshold=0.7,
            max_candidates=2,  # Ajustado para 2 páginas diretas
            priority="high",
            iterative_refinement=False
        )
    
    @staticmethod
    def create_complex_task(
        query: str, 
        specialist_type: SpecialistType,
        focus_areas: List[str],
        keywords: List[str]
    ) -> RAGSubagentTaskSpec:
        """Cria tarefa complexa com múltiplos focos"""
        return RAGSubagentTaskSpec(
            specialist_type=specialist_type,
            focus_areas=focus_areas,
            search_keywords=keywords,
            semantic_context=f"Complex analysis for: {query}",
            expected_findings="Comprehensive information covering multiple aspects",
            similarity_threshold=0.55,  # Ainda mais permissivo para queries complexas
            max_candidates=4,  # 4 páginas diretas para análise complexa
            priority="high",
            iterative_refinement=True
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'QueryComplexity', 'RAGSearchStrategy', 'DocumentRelevance', 'SpecialistType',
    
    # Modelos principais
    'RAGSubagentTaskSpec', 'RAGApproach', 'RAGDecomposition',
    
    # Avaliação
    'DocumentEvaluation', 'RAGSearchEvaluation', 'SubagentResult',
    
    # Síntese
    'SynthesisInstructions', 'EnhancedRAGResult',
    
    # Utilities
    'RAGTaskFactory'
]