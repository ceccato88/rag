#!/usr/bin/env python3
"""
Sistema de Configuração Unificado Enhanced
Resolve conflitos entre enhanced_config.py e sistema principal
"""

import os
from typing import Dict, Any, Optional

# Import do sistema principal com fallback
try:
    from src.core.config import SystemConfig
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
    from src.core.config import SystemConfig

# Import das configurações centralizadas
try:
    # Usar configurações centralizadas
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
    from src.core.constants import (
        ENHANCED_SIMILARITY_THRESHOLDS as SIMILARITY_THRESHOLDS,
        DYNAMIC_MAX_CANDIDATES as ENHANCED_MAX_CANDIDATES,
        ENHANCED_SUFFICIENCY_CRITERIA as SUFFICIENCY_CRITERIA,
        ENHANCED_ITERATION_LIMITS as ITERATION_LIMITS,
        ENHANCED_SPECIALIST_OPTIMIZATIONS as SPECIALIST_OPTIMIZATIONS,
        get_enhanced_config as get_optimized_config
    )
    CENTRALIZED_CONFIG = True
except ImportError:
    # Fallback para enhanced_config local
    from .enhanced_config import (
        SIMILARITY_THRESHOLDS,
        MAX_CANDIDATES as ENHANCED_MAX_CANDIDATES,
        SUFFICIENCY_CRITERIA,
        ITERATION_LIMITS,
        SPECIALIST_OPTIMIZATIONS,
        get_optimized_config
    )
    CENTRALIZED_CONFIG = False


class UnifiedEnhancedConfig:
    """
    Configuração unificada que resolve conflitos entre sistemas
    Prioridade: ENV vars > enhanced_config.py > system_config.py
    """
    
    def __init__(self):
        self.system_config = SystemConfig()
        self._cached_configs = {}
    
    def get_max_candidates(self, complexity: str = "MODERATE") -> int:
        """
        Obtém número máximo de candidatos com prioridade:
        1. Variável de ambiente MAX_CANDIDATES_{COMPLEXITY}
        2. enhanced_config.MAX_CANDIDATES
        3. SystemConfig padrão
        """
        # Tentar ENV específica primeiro
        env_key = f"MAX_CANDIDATES_{complexity.upper()}"
        
        # Importar função de validação centralizada
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
        from src.utils.env_validation import get_env_var_safely
        
        env_value = get_env_var_safely(env_key)
        if env_value:
            try:
                return int(env_value)
            except ValueError:
                pass
        
        # Tentar enhanced_config
        enhanced_value = ENHANCED_MAX_CANDIDATES.get(complexity.upper())
        if enhanced_value:
            return enhanced_value
        
        # Fallback para ENV geral ou padrão
        general_env = get_env_var_safely('MAX_CANDIDATES')
        if general_env:
            try:
                return int(general_env)
            except ValueError:
                pass
        
        # Último fallback
        return ENHANCED_MAX_CANDIDATES.get('DEFAULT', 3)
    
    def get_similarity_threshold(
        self, 
        complexity: str = "MODERATE", 
        specialist_type: Optional[str] = None
    ) -> float:
        """
        Obtém threshold de similaridade com prioridade:
        1. Especialista específico
        2. Complexidade
        3. Padrão
        """
        # Priorizar configuração do especialista
        if specialist_type:
            specialist_config = SPECIALIST_OPTIMIZATIONS.get(specialist_type.upper(), {})
            if 'similarity_threshold' in specialist_config:
                return specialist_config['similarity_threshold']
        
        # Usar configuração por complexidade
        return SIMILARITY_THRESHOLDS.get(complexity.upper(), 0.65)
    
    def get_unified_config(
        self, 
        complexity: str = "MODERATE", 
        specialist_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna configuração unificada completa
        """
        cache_key = f"{complexity}_{specialist_type or 'none'}"
        
        if cache_key in self._cached_configs:
            return self._cached_configs[cache_key]
        
        config = {
            # Configurações enhanced com fallbacks
            'max_candidates': self.get_max_candidates(complexity),
            'similarity_threshold': self.get_similarity_threshold(complexity, specialist_type),
            'max_iterations': ITERATION_LIMITS.get(complexity.upper(), 2),
            'sufficiency_criteria': SUFFICIENCY_CRITERIA.get(
                complexity.upper(), 
                SUFFICIENCY_CRITERIA['MODERATE']
            ),
            
            # Configurações do sistema principal
            'llm_model': self.system_config.rag.llm_model,
            'max_tokens_answer': self.system_config.rag.max_tokens_answer,
            'timeout': getattr(self.system_config.multiagent, 'subagent_timeout', 60.0) if hasattr(self.system_config, 'multiagent') else 60.0,
            
            # Configurações específicas enhanced
            'complexity': complexity.lower(),
            'specialist_type': specialist_type.lower() if specialist_type else None,
            'enhanced_mode': True
        }
        
        # Adicionar preferências de seções se disponível
        if specialist_type:
            specialist_opts = SPECIALIST_OPTIMIZATIONS.get(specialist_type.upper(), {})
            if 'preferred_sections' in specialist_opts:
                config['preferred_sections'] = specialist_opts['preferred_sections']
        
        # Cache para reutilização
        self._cached_configs[cache_key] = config
        
        return config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida se a configuração está correta
        """
        required_fields = ['max_candidates', 'similarity_threshold', 'llm_model']
        
        for field in required_fields:
            if field not in config:
                return False
        
        # Validações de range
        if not (1 <= config['max_candidates'] <= 10):
            return False
        
        if not (0.1 <= config['similarity_threshold'] <= 1.0):
            return False
        
        return True
    
    def clear_cache(self):
        """Limpa cache de configurações"""
        self._cached_configs.clear()


# Instância global unificada
unified_config = UnifiedEnhancedConfig()


# Funções de conveniência
def get_config_for_task(complexity: str, specialist_type: str = None) -> Dict[str, Any]:
    """
    Função de conveniência para obter configuração de tarefa
    """
    return unified_config.get_unified_config(complexity, specialist_type)


def get_max_candidates_for_complexity(complexity: str) -> int:
    """
    Função de conveniência para obter max_candidates
    """
    return unified_config.get_max_candidates(complexity)


def get_threshold_for_specialist(specialist_type: str, complexity: str = "MODERATE") -> float:
    """
    Função de conveniência para obter threshold
    """
    return unified_config.get_similarity_threshold(complexity, specialist_type)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'UnifiedEnhancedConfig',
    'unified_config',
    'get_config_for_task',
    'get_max_candidates_for_complexity', 
    'get_threshold_for_specialist'
]