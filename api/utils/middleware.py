#!/usr/bin/env python3
"""
🛡️ Middlewares Customizados - API Multi-Agente

Middlewares para segurança, logging, métricas e tratamento de requisições.
"""

import time
import logging
import uuid
from typing import Callable, Dict, Any
from datetime import datetime

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.config import config
from .errors import ErrorHandler, RateLimitError

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar headers de segurança"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        if config.production.production_mode:
            # Headers de segurança essenciais
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            
            # Content Security Policy básico
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
        
        # Headers informativos
        response.headers["X-API-Version"] = "1.0"
        response.headers["X-Powered-By"] = "FastAPI Multi-Agent RAG"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging detalhado de requisições"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Gerar ID único para a requisição
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Informações da requisição
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        content_length = request.headers.get("content-length", "0")
        
        # Log da requisição entrante
        logger.info(
            f"📥 [{request_id}] {request.method} {request.url.path} "
            f"- IP: {client_ip} - UA: {user_agent[:50]}... - Size: {content_length}"
        )
        
        # Adicionar request_id aos headers para rastreamento
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Log da resposta
            logger.info(
                f"📤 [{request_id}] {response.status_code} "
                f"- {processing_time:.3f}s - {response.headers.get('content-length', '?')} bytes"
            )
            
            # Adicionar headers de rastreamento
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log de erro
            logger.error(
                f"💥 [{request_id}] ERROR - {processing_time:.3f}s - {str(e)}"
            )
            
            # Criar resposta de erro
            error_response = ErrorHandler.create_error_response(e, request)
            error_response.headers["X-Request-ID"] = request_id
            error_response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
            
            return error_response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para coleta de métricas"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            success = 200 <= response.status_code < 400
            
            # Registrar métricas (evita importação circular)
            if hasattr(request.app.state, 'api_state_manager'):
                state_manager = request.app.state.api_state_manager
                await state_manager.metrics.record_request(processing_time, success)
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Registrar métrica de falha
            if hasattr(request.app.state, 'api_state_manager'):
                state_manager = request.app.state.api_state_manager
                await state_manager.metrics.record_request(processing_time, False)
            
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting customizado"""
    
    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.request_counts: Dict[str, Dict[str, Any]] = {}
        
    def _get_client_key(self, request: Request) -> str:
        """Gera chave única para o cliente"""
        # Usar IP do cliente como chave
        client_ip = request.client.host if request.client else "unknown"
        
        # Se tiver token de autenticação, usar como identificador
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return f"token_{auth_header[7:15]}"  # Primeiros 8 chars do token
        
        return f"ip_{client_ip}"
    
    def _is_rate_limited(self, client_key: str) -> tuple[bool, int]:
        """Verifica se o cliente excedeu o rate limit"""
        now = time.time()
        window_start = now - 60  # Janela de 1 minuto
        
        if client_key not in self.request_counts:
            self.request_counts[client_key] = {
                "requests": [],
                "window_start": window_start
            }
        
        client_data = self.request_counts[client_key]
        
        # Remover requisições antigas (fora da janela)
        client_data["requests"] = [
            req_time for req_time in client_data["requests"]
            if req_time > window_start
        ]
        
        # Verificar se excedeu o limite
        if len(client_data["requests"]) >= self.calls_per_minute:
            # Calcular tempo para próxima requisição
            oldest_request = min(client_data["requests"])
            retry_after = int(oldest_request + 60 - now) + 1
            return True, retry_after
        
        # Registrar nova requisição
        client_data["requests"].append(now)
        return False, 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not getattr(config.security, 'enable_rate_limiting', True):
            return await call_next(request)
        
        # Endpoints que não são limitados
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_key = self._get_client_key(request)
        is_limited, retry_after = self._is_rate_limited(client_key)
        
        if is_limited:
            logger.warning(f"🚫 Rate limit exceeded for {client_key}")
            
            response = JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Muitas requisições. Tente novamente em alguns segundos.",
                    "retry_after": retry_after
                }
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
            response.headers["X-RateLimit-Remaining"] = "0"
            
            return response
        
        response = await call_next(request)
        
        # Adicionar headers informativos sobre rate limit
        remaining = self.calls_per_minute - len(self.request_counts.get(client_key, {}).get("requests", []))
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware para limitar tamanho de requisições"""
    
    def __init__(self, app, max_size: int = 16 * 1024 * 1024):  # 16MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar Content-Length header
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    logger.warning(f"🚫 Request too large: {size} bytes (max: {self.max_size})")
                    
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": True,
                            "error_code": "REQUEST_TOO_LARGE",
                            "message": f"Requisição muito grande. Máximo permitido: {self.max_size // (1024*1024)}MB",
                            "details": {
                                "size_received": size,
                                "max_size": self.max_size
                            }
                        }
                    )
            except ValueError:
                pass  # Content-Length inválido, deixar o FastAPI tratar
        
        return await call_next(request)


def setup_cors_middleware(app):
    """Configura middleware CORS se habilitado"""
    if config.security.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.security.cors_origins_list or ["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Processing-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
        )
        logger.info(f"✅ CORS habilitado para: {config.security.cors_origins_list}")


def setup_middlewares(app):
    """Configura todos os middlewares na ordem correta"""
    
    # 1. CORS (primeiro)
    setup_cors_middleware(app)
    
    # 2. Rate limiting (antes da validação de request)
    if getattr(config.security, 'enable_rate_limiting', True):
        # Extrair número do formato "100/minute"
        rate_limit = config.security.rate_limit
        if "/minute" in rate_limit:
            calls_per_minute = int(rate_limit.split("/")[0])
            app.add_middleware(RateLimitMiddleware, calls_per_minute=calls_per_minute)
            logger.info(f"✅ Rate limiting habilitado: {calls_per_minute}/minuto")
    
    # 3. Tamanho de requisição
    app.add_middleware(
        RequestSizeMiddleware,
        max_size=config.production.max_request_size
    )
    
    # 4. Métricas
    if config.production.enable_metrics:
        app.add_middleware(MetricsMiddleware)
        logger.info("✅ Middleware de métricas habilitado")
    
    # 5. Logging (antes dos headers de segurança)
    app.add_middleware(RequestLoggingMiddleware)
    
    # 6. Headers de segurança (último)
    app.add_middleware(SecurityHeadersMiddleware)
    
    logger.info("✅ Todos os middlewares configurados")
