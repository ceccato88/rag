"""Utilitários de validação para o sistema RAG."""
import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def validate_document(doc: Dict) -> bool:
    """Valida se um documento tem todos os campos obrigatórios."""
    required_fields = ['id', 'page_num', 'markdown_text', 'image_path', 'doc_source']
    return all(field in doc for field in required_fields)

def validate_embedding(embedding: list, expected_dim: int) -> bool:
    """Valida se um embedding tem a dimensão esperada."""
    if not isinstance(embedding, list):
        logger.error(f"Embedding deve ser uma lista, recebido {type(embedding)}")
        return False
    if len(embedding) != expected_dim:
        logger.error(f"Dimensão incorreta: esperado {expected_dim}, recebido {len(embedding)}")
        return False
    
    # Valida se todos os valores são numéricos
    if not all(isinstance(x, (int, float)) for x in embedding):
        logger.error("Embedding contém valores não numéricos")
        return False
        
    return True

def validate_search_result(result: Dict) -> bool:
    """Valida estrutura de resultado de busca RAG."""
    required_fields = ['answer', 'candidates', 'selected_pages']
    return all(field in result for field in required_fields)

def validate_query(query: str) -> bool:
    """Valida se uma query é válida para busca."""
    if not query or not isinstance(query, str):
        return False
    
    # Remove espaços em branco
    query = query.strip()
    
    # Verifica se não está vazia após limpeza
    if len(query) == 0:
        return False
    
    # Verifica tamanho mínimo e máximo
    if len(query) < 3 or len(query) > 1000:
        logger.warning(f"Query muito curta/longa: {len(query)} caracteres")
        return False
    
    return True

def validate_environment_vars(required_vars: List[str]) -> Dict[str, Any]:
    """
    Valida se variáveis de ambiente obrigatórias estão definidas.
    
    Args:
        required_vars: Lista de nomes de variáveis obrigatórias
        
    Returns:
        Dict com status da validação e variáveis faltando
    """
    import os
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    return {
        "valid": len(missing_vars) == 0,
        "missing_vars": missing_vars,
        "total_required": len(required_vars),
        "total_found": len(required_vars) - len(missing_vars)
    }

# Função removida - não utilizada no projeto
# def sanitize_filename(filename: str) -> str:

# Função removida - não utilizada no projeto
# def validate_file_path(file_path: str) -> Dict[str, Any]:
