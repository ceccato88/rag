#!/usr/bin/env python3
"""
🔥 Sistema Enhanced - Multi-Agent RAG
Combinação robusta do sistema original com arquitetura RAG vetorial atual
"""

from .enhanced_models import (
    QueryComplexity,
    RAGSearchStrategy, 
    SpecialistType,
    RAGSubagentTaskSpec,
    RAGDecomposition,
    EnhancedRAGResult,
    RAGTaskFactory
)

from .enhanced_decomposition import (
    QueryAnalyzer,
    RAGDecomposer
)

from .enhanced_evaluation import (
    DocumentAnalyzer,
    IterativeRAGEvaluator,
    SubagentExecutor
)

from .enhanced_synthesis import (
    ConflictResolver,
    QualityAssessor,
    EnhancedSynthesizer
)

from .enhanced_integration import (
    EnhancedRAGSystem,
    EnhancedAPIAdapter,
    EnhancedLeadResearcher,
    create_enhanced_lead_researcher,
    integrate_enhanced_system
)

__version__ = "1.0.0"

__all__ = [
    # Modelos e Enums
    'QueryComplexity',
    'RAGSearchStrategy',
    'SpecialistType', 
    'RAGSubagentTaskSpec',
    'RAGDecomposition',
    'EnhancedRAGResult',
    'RAGTaskFactory',
    
    # Decomposição
    'QueryAnalyzer',
    'RAGDecomposer',
    
    # Avaliação
    'DocumentAnalyzer',
    'IterativeRAGEvaluator',
    'SubagentExecutor',
    
    # Síntese
    'ConflictResolver',
    'QualityAssessor',
    'EnhancedSynthesizer',
    
    # Integração
    'EnhancedRAGSystem',
    'EnhancedAPIAdapter',
    'EnhancedLeadResearcher',
    'create_enhanced_lead_researcher',
    'integrate_enhanced_system'
]