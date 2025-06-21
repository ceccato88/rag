#!/usr/bin/env python3
"""
CONFIGURAÇÕES ENHANCED - CENTRALIZADO
Todas as configurações foram movidas para src/core/constants.py
Este arquivo serve apenas como ponte para compatibilidade
"""

# Import centralizado das configurações
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
    from src.core.constants import (
        # Configurações principais
        ENHANCED_SIMILARITY_THRESHOLDS as SIMILARITY_THRESHOLDS,
        DYNAMIC_MAX_CANDIDATES as MAX_CANDIDATES,
        ENHANCED_SUFFICIENCY_CRITERIA as SUFFICIENCY_CRITERIA,
        ENHANCED_ITERATION_LIMITS as ITERATION_LIMITS,
        ENHANCED_TOKEN_LIMITS as TOKEN_LIMITS_ENHANCED,
        ENHANCED_QUALITY_WEIGHTS as QUALITY_WEIGHTS,
        ENHANCED_FALLBACK,
        ENHANCED_SPECIALIST_OPTIMIZATIONS as SPECIALIST_OPTIMIZATIONS,
        ENHANCED_TIMEOUTS,
        
        # Função centralizada
        get_enhanced_config as get_optimized_config
    )
    
    # Alias para compatibilidade total
    def get_config_for_task(complexity: str, specialist_type: str) -> dict:
        """Alias para compatibilidade com enhanced_unified_config.py"""
        return get_optimized_config(complexity, specialist_type)
    
    # Status de importação
    ENHANCED_CONFIG_CENTRALIZED = True
    
except ImportError as e:
    # Fallback para evitar quebras
    print(f"⚠️ WARNING: Não foi possível importar configurações centralizadas: {e}")
    print("📍 Usando configurações de fallback básicas")
    
    # Configurações básicas de fallback
    SIMILARITY_THRESHOLDS = {'DEFAULT': 0.65}
    MAX_CANDIDATES = {'DEFAULT': 3}
    SUFFICIENCY_CRITERIA = {'DEFAULT': {'relevance_threshold': 0.65}}
    ITERATION_LIMITS = {'DEFAULT': 2}
    TOKEN_LIMITS_ENHANCED = {}
    QUALITY_WEIGHTS = {}
    ENHANCED_FALLBACK = {}
    SPECIALIST_OPTIMIZATIONS = {}
    ENHANCED_TIMEOUTS = {}
    
    def get_optimized_config(complexity: str, specialist_type: str = None) -> dict:
        """Função de fallback básica"""
        return {
            'similarity_threshold': 0.65,
            'max_candidates': 3,
            'max_iterations': 2,
            'sufficiency_criteria': {'relevance_threshold': 0.65}
        }
    
    def get_config_for_task(complexity: str, specialist_type: str) -> dict:
        """Alias de fallback"""
        return get_optimized_config(complexity, specialist_type)
    
    ENHANCED_CONFIG_CENTRALIZED = False


# =============================================================================
# EXPORT PARA COMPATIBILIDADE
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
    'get_optimized_config',
    'get_config_for_task',
    'ENHANCED_CONFIG_CENTRALIZED'
]

# =============================================================================
# INFORMAÇÕES DE MIGRAÇÃO
# =============================================================================

if __name__ == "__main__":
    print("🔄 CONFIGURAÇÕES ENHANCED CENTRALIZADAS")
    print("=" * 50)
    print(f"✅ Centralização: {'Sucesso' if ENHANCED_CONFIG_CENTRALIZED else 'Falha'}")
    print(f"📍 Fonte: {'src/core/constants.py' if ENHANCED_CONFIG_CENTRALIZED else 'Fallback local'}")
    print("🎯 Todas as configurações enhanced estão agora em:")
    print("   /workspaces/rag/src/core/constants.py")
    print("")
    print("📋 Configurações disponíveis:")
    print(f"   - MAX_CANDIDATES: {MAX_CANDIDATES}")
    print(f"   - SIMILARITY_THRESHOLDS: {SIMILARITY_THRESHOLDS}")
    print("   - SUFFICIENCY_CRITERIA, ITERATION_LIMITS, etc.")
    print("")
    print("🚀 Função principal: get_enhanced_config(complexity, specialist_type)")