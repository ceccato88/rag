#!/usr/bin/env python3
"""
📄 Router de Indexação - API Multi-Agente

Endpoints relacionados à indexação de documentos PDF.
"""

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..models.schemas import IndexRequest, IndexResponse
from ..core.state import APIStateManager
from ..dependencies import (
    get_authenticated_state,
    track_request_metrics
)
from ..utils.errors import ErrorHandler, ValidationError, ProcessingError, ServiceUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/index",
    tags=["Indexação"],
    responses={
        401: {"description": "Token de acesso inválido"},
        503: {"description": "Serviço indisponível"},
        422: {"description": "Dados de entrada inválidos"}
    }
)

# Verificar disponibilidade do indexer
try:
    import sys
    import os
    from pathlib import Path
    
    # Adicionar path do workspace (no início da lista para prioridade)
    workspace_root = Path("/workspaces/rag")
    workspace_path = str(workspace_root)
    if workspace_path not in sys.path:
        sys.path.insert(0, workspace_path)
    
    # Alterar diretório temporariamente para resolver imports relativos
    original_cwd = os.getcwd()
    os.chdir(workspace_root)
    
    from src.core.indexer import index_pdf_native, create_doc_source_name, IndexingResult
    INDEXER_AVAILABLE = True
    logger.info("✅ Indexer disponível")
    
    # Voltar ao diretório original
    os.chdir(original_cwd)
    
except ImportError as e:
    logger.warning(f"⚠️ Indexer não disponível: {e}")
    INDEXER_AVAILABLE = False
    
    # Funções de fallback
    def index_pdf_native(url: str, doc_source: str = None):
        return None
    
    def create_doc_source_name(url: str) -> str:
        return url.split("/")[-1]


@router.post("", response_model=IndexResponse, summary="Indexar Documento PDF")
async def index_document(
    request: IndexRequest,
    state_manager: APIStateManager = Depends(get_authenticated_state),
    request_context = Depends(track_request_metrics)
):
    """
    Indexa um documento PDF por URL no sistema RAG.
    
    **Parâmetros:**
    - **url**: URL válida do arquivo PDF (deve começar com http/https e terminar com .pdf)
    - **doc_source**: Nome identificador do documento (opcional, será gerado se não fornecido)
    
    **Processo de Indexação:**
    1. Download do PDF da URL fornecida
    2. Extração de texto e imagens
    3. Criação de chunks semânticos
    4. Geração de embeddings
    5. Armazenamento no banco vetorial
    
    **Retorna:**
    - Status da indexação
    - Estatísticas do processamento
    - Metadados do documento
    
    **Exemplo de uso:**
    ```json
    {
        "url": "https://arxiv.org/pdf/2301.00001.pdf",
        "doc_source": "paper-transformers-2023"
    }
    ```
    """
    if not INDEXER_AVAILABLE:
        raise ServiceUnavailableError("Indexer", "Sistema de indexação não disponível")
    
    try:
        logger.info(f"📄 Iniciando indexação: {request.url}")
        
        # Validação adicional da URL
        ErrorHandler.validate_url(request.url)
        
        # Criar nome do documento se não fornecido
        doc_source = request.doc_source or create_doc_source_name(request.url)
        
        # Verificar se doc_source é válido
        if not doc_source or not doc_source.strip():
            doc_source = f"document_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"📋 Documento será indexado como: {doc_source}")
        
        # Executar indexação em thread separada para não bloquear
        logger.info("🔄 Executando indexação...")
        indexing_result = await asyncio.to_thread(index_pdf_native, request.url, doc_source)
        
        if indexing_result and indexing_result.success:
            response = IndexResponse(
                success=True,
                message="Documento indexado com sucesso usando indexer",
                doc_source=indexing_result.doc_source,
                pages_processed=indexing_result.pages_processed,
                chunks_created=indexing_result.chunks_created,
                images_extracted=indexing_result.images_extracted,
                processing_time=indexing_result.processing_time,
                metadata=indexing_result.metadata or {}
            )
            
            logger.info(
                f"✅ Indexação concluída: {doc_source} - "
                f"{indexing_result.pages_processed} páginas, "
                f"{indexing_result.chunks_created} chunks em "
                f"{indexing_result.processing_time:.2f}s"
            )
            
            return response
            
        else:
            error_detail = indexing_result.error if indexing_result else "Erro desconhecido na indexação"
            logger.error(f"❌ Falha na indexação: {error_detail}")
            raise ProcessingError("indexação", error_detail)
            
    except ValidationError:
        # Erro de validação - re-raise
        raise
        
    except Exception as e:
        logger.error(f"❌ Erro na indexação: {e}", exc_info=True)
        raise ProcessingError("indexação", str(e))


@router.get("/status", summary="Status do Sistema de Indexação")
async def indexing_status():
    """
    Retorna o status do sistema de indexação.
    
    **Retorna:**
    - Disponibilidade do indexer
    - Versão do sistema
    - Capacidades disponíveis
    """
    return {
        "indexer_available": INDEXER_AVAILABLE,
        "indexer_version": "1.0" if INDEXER_AVAILABLE else None,
        "capabilities": {
            "pdf_processing": INDEXER_AVAILABLE,
            "image_extraction": INDEXER_AVAILABLE,
            "semantic_chunking": INDEXER_AVAILABLE,
            "vector_storage": INDEXER_AVAILABLE
        } if INDEXER_AVAILABLE else {},
        "supported_formats": ["PDF"] if INDEXER_AVAILABLE else [],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/validate-url", summary="Validar URL de Documento")
async def validate_document_url(request: IndexRequest):
    """
    Valida uma URL de documento sem realizar a indexação.
    
    **Parâmetros:**
    - **url**: URL para validar
    
    **Retorna:**
    - Status da validação
    - Informações sobre a URL
    """
    try:
        # Validar URL
        ErrorHandler.validate_url(request.url)
        
        # Gerar nome do documento
        doc_source = request.doc_source or create_doc_source_name(request.url)
        
        return {
            "valid": True,
            "url": request.url,
            "generated_doc_source": doc_source,
            "ready_for_indexing": INDEXER_AVAILABLE,
            "message": "URL válida e pronta para indexação" if INDEXER_AVAILABLE else "URL válida, mas indexer não disponível"
        }
        
    except ValidationError as e:
        return {
            "valid": False,
            "url": request.url,
            "error": e.user_message,
            "details": e.details
        }
