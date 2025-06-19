#!/usr/bin/env python3
"""
🛠️ Utils - Utilitários da API

Contém middlewares, tratamento de erros e funcionalidades auxiliares.
"""

from .errors import (
    APIError,
    ValidationError,
    AuthenticationError,
    ServiceUnavailableError,
    ProcessingError,
    ErrorHandler,
    ErrorCapture
)
from .middleware import setup_middlewares

__all__ = [
    "APIError",
    "ValidationError", 
    "AuthenticationError",
    "ServiceUnavailableError",
    "ProcessingError",
    "ErrorHandler",
    "ErrorCapture",
    "setup_middlewares"
]
