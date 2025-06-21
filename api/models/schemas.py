#!/usr/bin/env python3
"""
📋 Modelos de Dados - API Multi-Agente

Definições dos modelos Pydantic para requisições e respostas da API.
Atualizado para Pydantic V2 com field_validator.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from src.core.constants import VALIDATION_CONFIG, TOKEN_LIMITS


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
        min_length=VALIDATION_CONFIG['MIN_QUERY_LENGTH'],
        max_length=VALIDATION_CONFIG['MAX_QUERY_LENGTH'],
        description="Consulta do usuário para pesquisa"
    )
    objective: Optional[str] = Field(
        default=None,
        max_length=VALIDATION_CONFIG['MAX_OBJECTIVE_LENGTH'],
        description="Objetivo específico da pesquisa"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query_content(cls, v):
        """Valida o conteúdo da query"""
        if not v or not v.strip():
            raise ValueError("Query não pode estar vazia")
        
        # Remover espaços extras
        v = v.strip()
        
        # Verificar caracteres perigosos
        dangerous_chars = VALIDATION_CONFIG['DANGEROUS_PATTERNS']
        v_lower = v.lower()
        if any(char in v_lower for char in dangerous_chars):
            raise ValueError("Query contém conteúdo potencialmente perigoso")
        
        return v


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
                "reasoning_trace": "=== Trace de Raciocínio - OpenAI Lead Researcher (agent-123) ===\n\n🔍 Passo 1: FACT_GATHERING\n⏰ 10:30:01\n💭 Coletando fatos para: Research planning for inteligência artificial\n👁️ Observações: Query complexity: moderate, Technical depth: moderate\n➡️ Próxima ação: Analisar fatos dados e relembrar conhecimento relevante\n\n──────────────────────────────────────────────────\n\n🔍 Passo 2: PLANNING\n⏰ 10:30:02\n💭 Criando plano para: Create comprehensive research plan for IA\n👁️ Observações: Recursos disponíveis: ['OpenAI gpt-4.1-mini', 'RAG subagents']\n➡️ Próxima ação: Desenvolver plano estruturado em etapas"
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
    reasoning_trace: str = Field(description="Trace completo do ReAct reasoning (sempre presente no sistema enhanced)")
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
        min_length=VALIDATION_CONFIG['MIN_URL_LENGTH'],
        max_length=VALIDATION_CONFIG['MAX_URL_LENGTH']
    )
    doc_source: Optional[str] = Field(
        default=None,
        max_length=VALIDATION_CONFIG['MAX_DOC_SOURCE_LENGTH'],
        description="Nome/identificador do documento"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v):
        """Valida formato da URL"""
        if not v or not v.strip():
            raise ValueError("URL não pode estar vazia")
        
        v = v.strip()
        
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        
        # Permitir URLs do arXiv ou URLs que terminam com .pdf
        is_arxiv_url = "arxiv.org/pdf/" in v.lower()
        is_pdf_url = v.lower().endswith(".pdf")
        
        if not (is_arxiv_url or is_pdf_url):
            raise ValueError("URL deve apontar para um arquivo PDF ou ser uma URL do arXiv")
        
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
                    "server": "0.0.0.0:8001",
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
                "total_documents": 125,
                "unique_doc_sources": 5,
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
    total_documents: int = Field(default=0, description="Total de documentos indexados")
    unique_doc_sources: int = Field(default=0, description="Número de fontes únicas de documentos")
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
