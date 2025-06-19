#!/usr/bin/env python3
"""
🚀 API Multi-Agente - Módulo Principal

Sistema RAG (Retrieval-Augmented Generation) multi-agente para pesquisa
e indexação de documentos, construído com FastAPI e arquitetura modular.

Versão: 2.0.0
Atualizada: 2025-06-19
"""

__version__ = "2.0.0"
__author__ = "Sistema RAG Multi-Agente"
__description__ = "API REST para sistema RAG multi-agente"

# Importações principais
from .core.config import config
from .utils.errors import APIError, ErrorHandler
from .models.schemas import (
    ResearchQuery,
    ResearchResponse,
    IndexRequest,
    IndexResponse,
    HealthResponse,
    StatsResponse
)

__all__ = [
    "config",
    "APIError",
    "ErrorHandler",
    "ResearchQuery",
    "ResearchResponse", 
    "IndexRequest",
    "IndexResponse",
    "HealthResponse",
    "StatsResponse"
]
