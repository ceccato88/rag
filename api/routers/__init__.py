#!/usr/bin/env python3
"""
🛣️ Routers - Endpoints da API

Definições de rotas organizadas por funcionalidade.
"""

from .research import router as research_router
from .indexing import router as indexing_router  
from .management import router as management_router

__all__ = [
    "research_router",
    "indexing_router",
    "management_router"
]
