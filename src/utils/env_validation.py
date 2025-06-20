"""
Utilitários para validação de variáveis de ambiente
Centraliza a lógica de verificação de variáveis para evitar uso direto de os.getenv
"""

import os
from typing import List


def check_env_var(var_name: str) -> bool:
    """
    Verifica se uma variável de ambiente está definida.
    
    Args:
        var_name: Nome da variável de ambiente
        
    Returns:
        True se a variável está definida e não vazia, False caso contrário
    """
    value = os.getenv(var_name)
    return bool(value and value.strip())


def validate_required_env_vars(required_vars: List[str]) -> tuple[bool, List[str]]:
    """
    Valida uma lista de variáveis de ambiente obrigatórias.
    
    Args:
        required_vars: Lista de nomes de variáveis obrigatórias
        
    Returns:
        Tupla com (sucesso, lista_de_variáveis_faltando)
    """
    missing_vars = [var for var in required_vars if not check_env_var(var)]
    return len(missing_vars) == 0, missing_vars


def get_env_var_safely(var_name: str, default: str = "") -> str:
    """
    Obtém uma variável de ambiente de forma segura.
    
    Args:
        var_name: Nome da variável
        default: Valor padrão se a variável não existir
        
    Returns:
        Valor da variável ou valor padrão
    """
    return os.getenv(var_name, default)
