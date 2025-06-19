#!/usr/bin/env python3
"""
🔧 Core - Módulos centrais da API

Contém configurações, gerenciamento de estado e funcionalidades essenciais.
"""

from .config import config, APIConfig
from .state import get_state_manager, APIStateManager, lifespan_manager

__all__ = [
    "config",
    "APIConfig", 
    "get_state_manager",
    "APIStateManager",
    "lifespan_manager"
]
