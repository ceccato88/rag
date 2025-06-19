#!/usr/bin/env python3
"""
🔌 Sistema de Injeção de Dependências - API Multi-Agente

Sistema para gerenciar dependências e validações comuns
utilizando o sistema de dependencies do FastAPI.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .core.config import config
from .core.state import get_state_manager, APIStateManager
from .utils.errors import (
    AuthenticationError,
    ServiceUnavailableError,
    RateLimitError,
    ErrorHandler,
    ValidationError
)

logger = logging.getLogger(__name__)

# Configurar esquema de segurança
security = HTTPBearer(auto_error=False)


def get_config():
    """Dependency para obter configuração global"""
    return config


def get_api_state() -> APIStateManager:
    """Dependency para obter o gerenciador de estado"""
    return get_state_manager()


def check_api_ready(state_manager: APIStateManager = Depends(get_api_state)) -> APIStateManager:
    """
    Verifica se a API está pronta para receber requisições
    
    Args:
        state_manager: Instância do gerenciador de estado
        
    Returns:
        APIStateManager: Gerenciador de estado se estiver pronto
        
    Raises:
        ServiceUnavailableError: Se a API não estiver pronta
    """
    if not state_manager.is_ready:
        if state_manager.is_initializing:
            raise ServiceUnavailableError(
                "API",
                "Sistema ainda está inicializando. Tente novamente em alguns segundos."
            )
        else:
            raise ServiceUnavailableError(
                "API",
                "Sistema não está disponível."
            )
    
    return state_manager


def verify_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Verifica autenticação via Bearer token
    
    Args:
        credentials: Credenciais HTTP Bearer
        
    Returns:
        str: Token validado
        
    Raises:
        AuthenticationError: Se o token for inválido ou ausente
    """
    # Em modo de desenvolvimento sem token configurado, permitir acesso
    if not config.production.production_mode and not config.security.bearer_token:
        logger.warning("⚠️ Executando sem autenticação (modo desenvolvimento)")
        return "dev-mode"
    
    if not credentials:
        raise AuthenticationError("Token de acesso é obrigatório")
    
    if not config.security.bearer_token:
        raise AuthenticationError("Autenticação não configurada no servidor")
    
    if credentials.credentials != config.security.bearer_token:
        raise AuthenticationError("Token de acesso inválido")
    
    return credentials.credentials


def get_authenticated_state(
    state_manager: APIStateManager = Depends(check_api_ready),
    token: str = Depends(verify_authentication)
) -> APIStateManager:
    """
    Dependency combinado que verifica se a API está pronta E o usuário está autenticado
    
    Args:
        state_manager: Gerenciador de estado validado
        token: Token de autenticação validado
        
    Returns:
        APIStateManager: Gerenciador de estado pronto e autenticado
    """
    return state_manager


def get_lead_researcher(
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Dependency para obter instância do Lead Researcher
    
    Args:
        state_manager: Gerenciador de estado autenticado
        
    Returns:
        OpenAILeadResearcher: Instância do pesquisador principal
        
    Raises:
        ServiceUnavailableError: Se o Lead Researcher não estiver disponível
    """
    if not state_manager.lead_researcher:
        raise ServiceUnavailableError("Lead Researcher", "Não inicializado")
    
    return state_manager.lead_researcher


def get_simple_rag(
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Dependency para obter instância do SimpleRAG
    
    Args:
        state_manager: Gerenciador de estado autenticado
        
    Returns:
        SimpleRAG: Instância do sistema RAG simples
        
    Raises:
        ServiceUnavailableError: Se o SimpleRAG não estiver disponível
    """
    if not state_manager.simple_rag:
        raise ServiceUnavailableError("SimpleRAG", "Não inicializado")
    
    return state_manager.simple_rag


def get_research_memory(
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Dependency para obter instância da memória de pesquisa
    
    Args:
        state_manager: Gerenciador de estado autenticado
        
    Returns:
        ResearchMemory: Instância da memória de pesquisa
        
    Raises:
        ServiceUnavailableError: Se a memória não estiver disponível
    """
    if not state_manager.research_memory:
        raise ServiceUnavailableError("Research Memory", "Não inicializado")
    
    return state_manager.research_memory


async def track_request_metrics(
    request: Request,
    state_manager: APIStateManager = Depends(get_api_state)
):
    """
    Dependency para tracking de métricas de requisição
    
    Args:
        request: Objeto de requisição do FastAPI
        state_manager: Gerenciador de estado
        
    Returns:
        Dict[str, Any]: Contexto da requisição para métricas
    """
    import time
    
    start_time = time.time()
    
    # Informações da requisição
    request_context = {
        "start_time": start_time,
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    
    logger.info(f"📥 {request.method} {request.url.path} - {request_context['client_ip']}")
    
    return request_context


class RequestValidator:
    """Validador de requisições com dependencies customizados"""
    
    @staticmethod
    def query_validator(query: str) -> str:
        """
        Valida query de pesquisa
        
        Args:
            query: String de consulta
            
        Returns:
            str: Query validada e limpa
            
        Raises:
            ValidationError: Se a query for inválida
        """
        ErrorHandler.validate_query(query)
        return query.strip()
    
    @staticmethod
    def url_validator(url: str) -> str:
        """
        Valida URL de documento
        
        Args:
            url: URL do documento
            
        Returns:
            str: URL validada
            
        Raises:
            ValidationError: Se a URL for inválida
        """
        ErrorHandler.validate_url(url)
        return url.strip()
    
    @staticmethod
    def collection_name_validator(collection_name: str) -> str:
        """
        Valida nome de coleção
        
        Args:
            collection_name: Nome da coleção
            
        Returns:
            str: Nome validado
            
        Raises:
            ValidationError: Se o nome for inválido
        """
        if not collection_name or not collection_name.strip():
            raise ValidationError("Nome da coleção não pode estar vazio", "collection_name")
        
        collection_name = collection_name.strip()
        
        if len(collection_name) > 100:
            raise ValidationError("Nome da coleção muito longo", "collection_name")
        
        # Verificar caracteres permitidos (alfanuméricos, underscore, hífen)
        if not collection_name.replace("_", "").replace("-", "").isalnum():
            raise ValidationError(
                "Nome da coleção deve conter apenas letras, números, _ e -",
                "collection_name"
            )
        
        return collection_name


# Instância global do validador
validator = RequestValidator()


def get_request_validator() -> RequestValidator:
    """Dependency para obter o validador de requisições"""
    return validator


# Rate limiting (se disponível)
rate_limiter = None

try:
    if config.security.enable_rate_limiting:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
        
        rate_limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[config.security.rate_limit]
        )
        
        logger.info(f"✅ Rate limiting habilitado: {config.security.rate_limit}")
        
except ImportError:
    logger.warning("⚠️ slowapi não disponível - rate limiting desabilitado")


def get_rate_limiter():
    """Dependency para obter o rate limiter (se disponível)"""
    return rate_limiter


# Health check dependencies
def basic_health_check(state_manager: APIStateManager = Depends(get_api_state)) -> Dict[str, Any]:
    """
    Health check básico sem autenticação
    
    Args:
        state_manager: Gerenciador de estado
        
    Returns:
        Dict[str, Any]: Status básico de saúde
    """
    return state_manager.get_health_status()


def detailed_health_check(
    state_manager: APIStateManager = Depends(check_api_ready)
) -> Dict[str, Any]:
    """
    Health check detalhado (requer API pronta)
    
    Args:
        state_manager: Gerenciador de estado validado
        
    Returns:
        Dict[str, Any]: Status detalhado de saúde
    """
    return state_manager.get_detailed_status()
