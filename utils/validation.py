"""Utilitários de validação para o indexador."""
import logging
from typing import Dict

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
    return True
