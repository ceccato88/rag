#!/usr/bin/env python3
"""
📋 Modelos de Dados - API Multi-Agente

Definições dos modelos Pydantic para requisições e respostas da API.
Atualizado para Pydantic V2 com field_validator.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import html
from pydantic import BaseModel, Field, field_validator, ConfigDict


def sanitize_and_validate_text(text: str, field_name: str = "text") -> str:
    """Sanitiza e valida texto contra XSS e outras injeções"""
    if not text or not text.strip():
        raise ValueError(f"{field_name} não pode estar vazio")
    
    # Primeiro, decodificar entidades HTML para detectar ataques codificados
    decoded_text = html.unescape(text.strip())
    
    # Padrões perigosos mais abrangentes
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Tags script
        r'javascript:',                # URLs javascript
        r'data:text/html',            # Data URLs com HTML
        r'vbscript:',                 # VBScript
        r'on\w+\s*=',                 # Event handlers (onclick, onload, etc.)
        r'<iframe[^>]*>',             # iframes
        r'<object[^>]*>',             # Objects
        r'<embed[^>]*>',              # Embeds
        r'<form[^>]*>',               # Forms
        r'<input[^>]*>',              # Inputs
        r'expression\s*\(',           # CSS expressions
        r'@import',                   # CSS imports
        r'url\s*\(',                  # CSS URLs
        r'<meta[^>]*>',               # Meta tags
        r'<link[^>]*>',               # Link tags
    ]
    
    # Verificar padrões perigosos (case insensitive)
    text_lower = decoded_text.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
            raise ValueError(f"{field_name} contém conteúdo potencialmente perigoso")
    
    # Verificar caracteres suspeitos
    suspicious_chars = ['<', '>', '{', '}', '$', '`']
    if any(char in decoded_text for char in suspicious_chars):
        # Permitir apenas se for texto científico legítimo
        if not _is_legitimate_scientific_text(decoded_text):
            raise ValueError(f"{field_name} contém caracteres suspeitos")
    
    return text.strip()


def _is_legitimate_scientific_text(text: str) -> bool:
    """Verifica se o texto contém apenas uso legítimo de caracteres especiais"""
    # Permitir < e > em contextos matemáticos/científicos
    math_patterns = [
        r'\d+\s*[<>]\s*\d+',          # Comparações numéricas
        r'[a-zA-Z]+\s*[<>]\s*[a-zA-Z]+',  # Comparações alfabéticas
        r'<\s*\d+',                    # Menor que número
        r'>\s*\d+',                    # Maior que número
    ]
    
    text_without_math = text
    for pattern in math_patterns:
        text_without_math = re.sub(pattern, '', text_without_math, flags=re.IGNORECASE)
    
    # Se após remover padrões matemáticos ainda há < ou >, é suspeito
    return '<' not in text_without_math and '>' not in text_without_math


class ResearchQuery(BaseModel):
    """Modelo para consulta de pesquisa"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Como funciona a inteligência artificial?",
                "objective": "Entender os conceitos básicos de IA"
            }
        }
    )
    
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Consulta do usuário para pesquisa"
    )
    objective: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Objetivo específico da pesquisa"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query_content(cls, v):
        """Valida o conteúdo da query com proteção XSS avançada"""
        return sanitize_and_validate_text(v, "Query")
    
    @field_validator('objective')
    @classmethod
    def validate_objective_content(cls, v):
        """Valida o conteúdo do objetivo com proteção XSS"""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
            
        return sanitize_and_validate_text(v, "Objective")


class ResearchResponse(BaseModel):
    """Modelo para resposta de pesquisa"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "query": "Como funciona a inteligência artificial?",
                "result": "A inteligência artificial é...",
                "agent_id": "agent-123",
                "status": "COMPLETED",
                "processing_time": 2.45,
                "timestamp": "2025-06-19T10:30:00Z",
                "confidence_score": 0.85,
                "sources": [{"title": "AI Basics", "url": "https://example.com"}],
                "reasoning_trace": "1. Analisou query... 2. Buscou informações..."
            }
        }
    )
    
    success: bool = Field(description="Se a operação foi bem-sucedida")
    query: str = Field(description="Query original processada")
    result: str = Field(description="Resultado da pesquisa")
    agent_id: str = Field(description="ID do agente que processou")
    status: str = Field(description="Status do processamento")
    processing_time: float = Field(description="Tempo de processamento em segundos")
    timestamp: str = Field(description="Timestamp ISO da resposta")
    confidence_score: Optional[float] = Field(default=None, description="Score de confiança (0-1)")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Fontes utilizadas")
    reasoning_trace: Optional[str] = Field(default=None, description="Trace do raciocínio")
    error: Optional[str] = Field(default=None, description="Mensagem de erro se aplicável")


class IndexRequest(BaseModel):
    """Modelo para requisição de indexação"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/document.pdf",
                "doc_source": "manual-usuario-v1"
            }
        }
    )
    
    url: str = Field(
        ...,
        description="URL do PDF para indexar",
        min_length=10,
        max_length=2000
    )
    doc_source: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Nome/identificador do documento"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v):
        """Valida formato da URL e verifica se é um PDF com proteção SSRF"""
        import requests
        import socket
        import ipaddress
        from urllib.parse import urlparse
        
        if not v or not v.strip():
            raise ValueError("URL não pode estar vazia")
        
        v = v.strip()
        
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        
        # Verificar se a URL é válida
        try:
            parsed = urlparse(v)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("URL inválida")
        except Exception:
            raise ValueError("Formato de URL inválido")
        
        # PROTEÇÃO SSRF: Verificar se o hostname resolve para IP privado
        try:
            hostname = parsed.hostname
            if hostname:
                # Resolver hostname para IP
                ip = socket.gethostbyname(hostname)
                ip_obj = ipaddress.ip_address(ip)
                
                # Bloquear IPs privados, localhost e reservados
                if (ip_obj.is_private or ip_obj.is_loopback or 
                    ip_obj.is_link_local or ip_obj.is_reserved or
                    ip_obj.is_multicast):
                    raise ValueError("Não é permitido acessar endereços IP privados ou localhost")
        except socket.gaierror:
            raise ValueError("Não foi possível resolver o hostname")
        except ValueError as e:
            if "private" in str(e) or "localhost" in str(e):
                raise e
            # Para outros erros de valor, continuar
        
        # Se termina com .pdf, aceitar diretamente (validação rápida)
        if v.lower().endswith(".pdf"):
            return v
        
        # Caso contrário, verificar Content-Type via HEAD request com proteção SSRF
        try:
            # Configurar sessão com proteções adicionais
            session = requests.Session()
            session.max_redirects = 3  # Limitar redirecionamentos
            
            response = session.head(v, timeout=10, allow_redirects=True)
            content_type = response.headers.get('content-type', '').lower()
            
            # Verificar se é PDF pelo Content-Type
            if 'application/pdf' in content_type:
                return v
            
            # Verificar se é uma URL conhecida que serve PDFs (arXiv, etc.)
            known_pdf_domains = ['arxiv.org', 'biorxiv.org', 'medrxiv.org']
            if any(domain in parsed.netloc.lower() for domain in known_pdf_domains):
                return v
                
            raise ValueError("URL não aponta para um arquivo PDF válido")
            
        except requests.exceptions.RequestException:
            # Se não conseguir verificar, aceitar se for de domínios conhecidos
            known_pdf_domains = ['arxiv.org', 'biorxiv.org', 'medrxiv.org']
            if any(domain in parsed.netloc.lower() for domain in known_pdf_domains):
                return v
            raise ValueError("Não foi possível verificar se a URL aponta para um PDF")
        
        return v
    
    @field_validator('doc_source')
    @classmethod
    def validate_doc_source(cls, v):
        """Valida o nome do documento"""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Verificar caracteres permitidos
        if not all(c.isalnum() or c in "._-" for c in v):
            raise ValueError("doc_source deve conter apenas letras, números, pontos, underscores e hífens")
        
        return v


class IndexResponse(BaseModel):
    """Modelo para resposta de indexação"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Documento indexado com sucesso",
                "doc_source": "manual-usuario-v1",
                "pages_processed": 25,
                "chunks_created": 150,
                "images_extracted": 10,
                "processing_time": 45.2,
                "metadata": {
                    "file_size": 2048576,
                    "creation_date": "2025-06-19T10:30:00Z"
                }
            }
        }
    )
    
    success: bool = Field(description="Se a indexação foi bem-sucedida")
    message: str = Field(description="Mensagem sobre o resultado")
    doc_source: str = Field(description="Nome do documento indexado")
    pages_processed: int = Field(default=0, ge=0, description="Número de páginas processadas")
    chunks_created: int = Field(default=0, ge=0, description="Número de chunks criados")
    images_extracted: int = Field(default=0, ge=0, description="Número de imagens extraídas")
    processing_time: float = Field(default=0.0, ge=0, description="Tempo de processamento")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")


class HealthResponse(BaseModel):
    """Modelo para resposta de health check"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "uptime_seconds": 3600.5,
                "components": {
                    "memory": True,
                    "lead_researcher": True,
                    "simple_rag": True
                },
                "metrics": {
                    "total_requests": 150,
                    "successful_requests": 145,
                    "failed_requests": 5,
                    "success_rate": 96.67,
                    "average_response_time": 1.23
                },
                "timestamp": "2025-06-19T10:30:00Z"
            }
        }
    )
    
    status: str = Field(description="Status geral do sistema")
    uptime_seconds: float = Field(description="Tempo de atividade em segundos")
    components: Dict[str, bool] = Field(description="Status dos componentes")
    metrics: Dict[str, Any] = Field(description="Métricas de requisições")
    timestamp: str = Field(description="Timestamp da verificação")


class DetailedHealthResponse(HealthResponse):
    """Modelo estendido para health check detalhado"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "uptime_seconds": 3600.5,
                "components": {"memory": True},
                "metrics": {"total_requests": 150},
                "timestamp": "2025-06-19T10:30:00Z",
                "configuration": {
                    "production_mode": True,
                    "server": "0.0.0.0:8000",
                    "log_level": "INFO"
                },
                "memory_initialized": True,
                "lead_researcher_initialized": True,
                "simple_rag_initialized": True
            }
        }
    )
    
    configuration: Dict[str, Any] = Field(description="Resumo da configuração")
    memory_initialized: bool = Field(description="Se a memória está inicializada")
    lead_researcher_initialized: bool = Field(description="Se o lead researcher está inicializado")
    simple_rag_initialized: bool = Field(description="Se o SimpleRAG está inicializado")


class StatsResponse(BaseModel):
    """Modelo para resposta de estatísticas"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uptime_seconds": 3600.5,
                "total_requests": 150,
                "api_ready": True,
                "multiagent_initialized": True,
                "indexer_available": True,
                "rate_limiting_available": True,
                "production_mode": False,
                "timestamp": "2025-06-19T10:30:00Z"
            }
        }
    )
    
    uptime_seconds: float = Field(description="Tempo de atividade")
    total_requests: int = Field(description="Total de requisições processadas")
    api_ready: bool = Field(description="Se a API está pronta")
    multiagent_initialized: bool = Field(description="Se o sistema multi-agente está inicializado")
    indexer_available: bool = Field(description="Se o indexer está disponível")
    rate_limiting_available: bool = Field(description="Se rate limiting está disponível")
    production_mode: bool = Field(description="Se está em modo de produção")
    timestamp: str = Field(description="Timestamp das estatísticas")


class DeleteResponse(BaseModel):
    """Modelo para resposta de deleção"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Documentos deletados da coleção test-collection",
                "details": {
                    "documents_deleted": 25,
                    "collection": "test-collection"
                }
            }
        }
    )
    
    success: bool = Field(description="Se a operação foi bem-sucedida")
    message: str = Field(description="Mensagem sobre o resultado")
    details: Dict[str, Any] = Field(description="Detalhes da operação")


class ErrorResponse(BaseModel):
    """Modelo para respostas de erro"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "error_code": "VALIDATION_ERROR",
                "message": "Os dados fornecidos são inválidos",
                "details": {
                    "field": "query",
                    "invalid_value": "a"
                },
                "timestamp": "2025-06-19T10:30:00Z"
            }
        }
    )
    
    error: bool = Field(default=True, description="Sempre True para erros")
    error_code: str = Field(description="Código do erro")
    message: str = Field(description="Mensagem de erro para o usuário")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detalhes adicionais do erro")
    timestamp: str = Field(description="Timestamp do erro")
