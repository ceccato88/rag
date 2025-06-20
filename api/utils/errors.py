#!/usr/bin/env python3
"""
🚨 Sistema de Tratamento de Erros - API Multi-Agente

Sistema centralizado e estruturado para tratamento de erros
com logging adequado e respostas padronizadas.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Union
from datetime import datetime

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Erro base da API com estrutura padronizada"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.user_message = user_message or message
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)


class ValidationError(APIError):
    """Erro de validação de entrada"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {
            "field": field,
            "invalid_value": str(value) if value is not None else None
        }
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
            user_message="Os dados fornecidos são inválidos. Verifique e tente novamente."
        )


class AuthenticationError(APIError):
    """Erro de autenticação"""
    
    def __init__(self, message: str = "Token de acesso inválido ou ausente"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            user_message="Credenciais inválidas. Verifique seu token de acesso."
        )


class AuthorizationError(APIError):
    """Erro de autorização"""
    
    def __init__(self, message: str = "Acesso negado"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            user_message="Você não tem permissão para acessar este recurso."
        )


class ResourceNotFoundError(APIError):
    """Erro de recurso não encontrado"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} não encontrado"
        if identifier:
            message += f": {identifier}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            user_message=f"O {resource.lower()} solicitado não foi encontrado."
        )


class ServiceUnavailableError(APIError):
    """Erro de serviço indisponível"""
    
    def __init__(self, service: str, reason: Optional[str] = None):
        message = f"Serviço {service} indisponível"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service, "reason": reason},
            user_message=f"O serviço {service} está temporariamente indisponível. Tente novamente em alguns minutos."
        )


class RateLimitError(APIError):
    """Erro de limite de taxa excedido"""
    
    def __init__(self, limit: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"Limite de taxa excedido: {limit}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "retry_after": retry_after},
            user_message="Muitas requisições. Aguarde um momento antes de tentar novamente."
        )


class ProcessingError(APIError):
    """Erro durante processamento"""
    
    def __init__(self, operation: str, reason: Optional[str] = None):
        message = f"Erro no processamento de {operation}"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="PROCESSING_ERROR",
            details={"operation": operation, "reason": reason},
            user_message=f"Não foi possível processar a operação {operation}. Verifique os dados e tente novamente."
        )


class ExternalServiceError(APIError):
    """Erro em serviço externo"""
    
    def __init__(self, service: str, status_code: int, response: Optional[str] = None):
        super().__init__(
            message=f"Erro no serviço externo {service}: HTTP {status_code}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "external_status": status_code, "response": response},
            user_message=f"Erro de comunicação com serviço externo. Tente novamente em alguns minutos."
        )


class ErrorHandler:
    """Handler centralizado de erros da API"""
    
    @staticmethod
    def create_error_response(error: Exception, request: Optional[Request] = None) -> JSONResponse:
        """Cria resposta de erro padronizada"""
        
        # Extrair informações da requisição
        request_info = {}
        if request:
            request_info = {
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None
            }
        
        # Tratar erros da API
        if isinstance(error, APIError):
            response_data = {
                "error": True,
                "error_code": error.error_code,
                "message": error.user_message,
                "details": error.details,
                "timestamp": error.timestamp.isoformat(),
                **request_info
            }
            
            # Log baseado na severidade
            if error.status_code >= 500:
                logger.error(f"API Error: {error.message}", extra={"error_details": error.details})
            else:
                logger.warning(f"API Error: {error.message}", extra={"error_details": error.details})
            
            return JSONResponse(
                status_code=error.status_code,
                content=response_data
            )
        
        # Tratar erros de validação do Pydantic
        if isinstance(error, PydanticValidationError):
            validation_errors = []
            for err in error.errors():
                validation_errors.append({
                    "field": ".".join(str(x) for x in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                })
            
            response_data = {
                "error": True,
                "error_code": "VALIDATION_ERROR",
                "message": "Dados de entrada inválidos",
                "details": {"validation_errors": validation_errors},
                "timestamp": datetime.utcnow().isoformat(),
                **request_info
            }
            
            logger.warning(f"Validation error: {validation_errors}")
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=response_data
            )
        
        # Tratar HTTPException do FastAPI
        if isinstance(error, HTTPException):
            response_data = {
                "error": True,
                "error_code": "HTTP_EXCEPTION",
                "message": error.detail,
                "timestamp": datetime.utcnow().isoformat(),
                **request_info
            }
            
            logger.warning(f"HTTP Exception: {error.detail}")
            
            return JSONResponse(
                status_code=error.status_code,
                content=response_data
            )
        
        # Erro não tratado - log completo e resposta genérica
        error_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        logger.error(
            f"Unhandled error [{error_id}]: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "traceback": traceback.format_exc(),
                "request_info": request_info
            }
        )
        
        response_data = {
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Erro interno do servidor",
            "details": {"error_id": error_id},
            "timestamp": datetime.utcnow().isoformat(),
            **request_info
        }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_data
        )
    
    @staticmethod
    def validate_query(query: str) -> None:
        """Valida consulta de pesquisa"""
        if not query or not query.strip():
            raise ValidationError("Consulta não pode estar vazia", "query", query)
        
        query = query.strip()
        
        if len(query) < 3:
            raise ValidationError("Consulta deve ter pelo menos 3 caracteres", "query", query)
        
        if len(query) > 1000:
            raise ValidationError("Consulta não pode exceder 1000 caracteres", "query", query)
        
        # Verificar caracteres perigosos
        dangerous_chars = ["<", ">", "&", "\"", "'"]
        if any(char in query for char in dangerous_chars):
            raise ValidationError("Consulta contém caracteres não permitidos", "query", query)
    
    @staticmethod
    def validate_url(url: str) -> None:
        """Valida URL de documento"""
        if not url or not url.strip():
            raise ValidationError("URL não pode estar vazia", "url", url)
        
        url = url.strip()
        
        if not url.startswith(("http://", "https://")):
            raise ValidationError("URL deve começar com http:// ou https://", "url", url)
        
        # Permitir URLs do arXiv ou URLs que terminam com .pdf
        is_arxiv_url = "arxiv.org/pdf/" in url.lower()
        is_pdf_url = url.lower().endswith(".pdf")
        
        if not (is_arxiv_url or is_pdf_url):
            raise ValidationError("URL deve apontar para um arquivo PDF ou ser uma URL do arXiv", "url", url)
    
    @staticmethod
    def validate_token(token: Optional[str]) -> None:
        """Valida token de acesso"""
        if not token:
            raise AuthenticationError("Token de acesso é obrigatório")
        
        if len(token) < 10:
            raise AuthenticationError("Token de acesso inválido")


# Context manager para captura automática de erros
class ErrorCapture:
    """Context manager para captura e tratamento automático de erros"""
    
    def __init__(self, operation: str, reraise: bool = True):
        self.operation = operation
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and not isinstance(exc_val, APIError):
            logger.error(f"Error in {self.operation}: {exc_val}", exc_info=True)
            
            if self.reraise:
                # Converter para APIError
                raise ProcessingError(self.operation, str(exc_val))
        
        return False  # Não suprimir a exceção
