#!/usr/bin/env python3
"""
Configurações Otimizadas do Sistema Enhanced
Valores testados e ajustados para melhor performance vs qualidade
"""

# =============================================================================
# THRESHOLDS DE SIMILARIDADE OTIMIZADOS
# =============================================================================

SIMILARITY_THRESHOLDS = {
    # Por complexidade da query
    'SIMPLE': 0.70,      # Mais restritivo para queries simples
    'MODERATE': 0.65,    # Balanceado para queries moderadas
    'COMPLEX': 0.55,     # Mais permissivo para queries complexas
    'VERY_COMPLEX': 0.50, # Muito permissivo para máxima cobertura
    
    # Fallbacks
    'DEFAULT': 0.65,
    'MINIMUM': 0.30,     # Limite mínimo absoluto
    'MAXIMUM': 0.90      # Limite máximo para alta precisão
}

# =============================================================================
# CANDIDATOS PARA ANÁLISE
# =============================================================================

MAX_CANDIDATES = {
    # Por complexidade da query (SEM RERANKING - direto da busca por similaridade)
    'SIMPLE': 2,         # 2 páginas para respostas diretas
    'MODERATE': 3,       # 3 páginas para queries moderadas
    'COMPLEX': 4,        # 4 páginas para análise ampla
    'VERY_COMPLEX': 5,   # 5 páginas para cobertura completa
    
    # Limites
    'DEFAULT': 3,
    'MINIMUM': 2,
    'MAXIMUM': 6         # Máximo 6 páginas
}

# =============================================================================
# CRITÉRIOS DE SUFICIÊNCIA OTIMIZADOS
# =============================================================================

SUFFICIENCY_CRITERIA = {
    # Thresholds por complexidade
    'SIMPLE': {
        'relevance_threshold': 0.70,
        'coverage_threshold': 0.60,
        'max_critical_gaps': 1
    },
    'MODERATE': {
        'relevance_threshold': 0.65,
        'coverage_threshold': 0.70,
        'max_critical_gaps': 2
    },
    'COMPLEX': {
        'relevance_threshold': 0.60,
        'coverage_threshold': 0.75,
        'max_critical_gaps': 2
    },
    'VERY_COMPLEX': {
        'relevance_threshold': 0.55,
        'coverage_threshold': 0.80,
        'max_critical_gaps': 3
    }
}

# =============================================================================
# ITERAÇÕES E PERFORMANCE
# =============================================================================

ITERATION_LIMITS = {
    # Por complexidade
    'SIMPLE': 1,         # Uma iteração é suficiente
    'MODERATE': 2,       # Máximo 2 iterações
    'COMPLEX': 2,        # Máximo 2 iterações (otimizado)
    'VERY_COMPLEX': 3,   # Máximo 3 para casos muito complexos
    
    # Configurações
    'DEFAULT': 2,
    'MINIMUM': 1,
    'MAXIMUM': 3         # Limite absoluto para performance
}

# =============================================================================
# TOKENS E LIMITES DE CONTEXT
# =============================================================================

TOKEN_LIMITS_ENHANCED = {
    'MAX_TOKENS_DECOMPOSITION': 1500,    # Mais tokens para decomposição complexa
    'MAX_TOKENS_EVALUATION': 800,       # Tokens para avaliação de documentos
    'MAX_TOKENS_SYNTHESIS': 3000,       # Mais tokens para síntese coordenada
    'MAX_TOKENS_CONFLICT_RESOLUTION': 500,
    'MAX_TOKENS_QUALITY_ASSESSMENT': 300,
    
    # Por especialista
    'CONCEPTUAL_MAX_TOKENS': 1200,
    'COMPARATIVE_MAX_TOKENS': 1500,
    'TECHNICAL_MAX_TOKENS': 1800,
    'EXAMPLES_MAX_TOKENS': 1000,
    'GENERAL_MAX_TOKENS': 1000
}

# =============================================================================
# PESOS PARA MÉTRICAS DE QUALIDADE
# =============================================================================

QUALITY_WEIGHTS = {
    'query_relevance': 0.30,      # Importância alta - responder à pergunta
    'completeness': 0.25,         # Importante - cobrir todos os aspectos
    'coherence': 0.20,           # Importante - resposta coerente
    'source_utilization': 0.15,  # Moderado - usar fontes adequadamente
    'clarity': 0.10              # Menor - clareza da escrita
}

# =============================================================================
# CONFIGURAÇÕES DE FALLBACK ENHANCED
# =============================================================================

ENHANCED_FALLBACK = {
    'USE_SIMPLE_TASK_ON_FAILURE': True,
    'REDUCE_COMPLEXITY_ON_ERROR': True,
    'FALLBACK_TO_SINGLE_SPECIALIST': True,
    'EMERGENCY_THRESHOLD_REDUCTION': 0.20,  # Reduzir em 20%
    'MIN_EMERGENCY_CANDIDATES': 3,
    'MAX_FALLBACK_ATTEMPTS': 2
}

# =============================================================================
# MAPEAMENTO DINÂMICO POR ESPECIALISTA
# =============================================================================

SPECIALIST_OPTIMIZATIONS = {
    'CONCEPTUAL': {
        'similarity_threshold': 0.70,  # Muito restritivo - só conceitos precisos
        'preferred_sections': ['definitions', 'introductions', 'concepts']
    },
    'COMPARATIVE': {
        'similarity_threshold': 0.60,  # Moderado - comparações relevantes
        'preferred_sections': ['comparisons', 'analysis', 'versus']
    },
    'TECHNICAL': {
        'similarity_threshold': 0.65,  # Moderadamente restritivo - detalhes técnicos
        'preferred_sections': ['implementation', 'technical', 'methodology']
    },
    'EXAMPLES': {
        'similarity_threshold': 0.55,  # Permissivo - exemplos práticos
        'preferred_sections': ['examples', 'case_studies', 'applications']
    },
    'GENERAL': {
        'similarity_threshold': 0.50,  # Mais permissivo - informações gerais
        'preferred_sections': ['overview', 'summary', 'general']
    }
}

# =============================================================================
# TIMEOUTS OTIMIZADOS
# =============================================================================

ENHANCED_TIMEOUTS = {
    'DECOMPOSITION_TIMEOUT': 30.0,      # 30s para decomposição
    'SUBAGENT_TIMEOUT': 60.0,           # 60s por subagente
    'SYNTHESIS_TIMEOUT': 45.0,          # 45s para síntese
    'EVALUATION_TIMEOUT': 20.0,         # 20s para avaliação
    'CONFLICT_RESOLUTION_TIMEOUT': 15.0, # 15s para resolução
    'QUALITY_ASSESSMENT_TIMEOUT': 10.0   # 10s para qualidade
}

# =============================================================================
# FUNÇÃO PARA OBTER CONFIGURAÇÃO DINÂMICA
# =============================================================================

def get_optimized_config(complexity: str, specialist_type: str = None):
    """
    Retorna configuração otimizada baseada na complexidade e especialista
    
    Args:
        complexity: 'simple', 'moderate', 'complex', 'very_complex'
        specialist_type: 'conceptual', 'comparative', 'technical', 'examples', 'general'
    
    Returns:
        Dict com configurações otimizadas
    """
    config = {
        'similarity_threshold': SIMILARITY_THRESHOLDS.get(complexity.upper(), 0.65),
        'max_candidates': MAX_CANDIDATES.get(complexity.upper(), 3),  # Baseado na COMPLEXIDADE
        'max_iterations': ITERATION_LIMITS.get(complexity.upper(), 2),
        'sufficiency_criteria': SUFFICIENCY_CRITERIA.get(complexity.upper(), SUFFICIENCY_CRITERIA['MODERATE'])
    }
    
    # Aplicar otimizações específicas do especialista (apenas threshold e seções preferidas)
    if specialist_type:
        specialist_opts = SPECIALIST_OPTIMIZATIONS.get(specialist_type.upper(), {})
        # NÃO sobrescrever max_candidates - manter baseado na complexidade
        if 'similarity_threshold' in specialist_opts:
            config['similarity_threshold'] = specialist_opts['similarity_threshold']
        if 'preferred_sections' in specialist_opts:
            config['preferred_sections'] = specialist_opts['preferred_sections']
    
    return config


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'SIMILARITY_THRESHOLDS',
    'MAX_CANDIDATES', 
    'SUFFICIENCY_CRITERIA',
    'ITERATION_LIMITS',
    'TOKEN_LIMITS_ENHANCED',
    'QUALITY_WEIGHTS',
    'ENHANCED_FALLBACK',
    'SPECIALIST_OPTIMIZATIONS',
    'ENHANCED_TIMEOUTS',
    'get_optimized_config'
]