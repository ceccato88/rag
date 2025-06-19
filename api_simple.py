#!/usr/bin/env python3
"""
🚀 API de Produção - Sistema RAG Simples Refatorado

API REST simplificada usando modelos nativos do sistema RAG.
Utiliza SimpleRAG diretamente com padrões de resposta padronizados.
"""

import os
import sys
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importações do sistema RAG
from config import SystemConfig
from search import SimpleRAG
from utils.validation import validate_query
from utils.metrics import ProcessingMetrics

# Import de funções de manutenção
sys.path.append(os.path.join(os.path.dirname(__file__), 'maintenance'))
from delete_collection import delete_documents

# Configuração de logging
log_level = os.getenv("API_LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/logs/api_simple.log")
    ] if os.path.exists("/app/logs") else [logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuração centralizada
system_config = SystemConfig()

# Configuração de segurança
security = HTTPBearer()
API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica se o token Bearer é válido"""
    if not API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token de API não configurado no servidor"
        )
    
    if credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# ═══════════════════════════════════════════════════════════════════════════════
# MODELOS DE DADOS SIMPLIFICADOS
# ═══════════════════════════════════════════════════════════════════════════════

class SearchQuery(BaseModel):
    """Consulta de busca simplificada"""
    query: str = Field(..., min_length=3, max_length=500, description="Consulta do usuário")
    max_results: Optional[int] = Field(default=None, ge=1, le=20, description="Número máximo de resultados")

class SearchResponse(BaseModel):
    """Resposta de busca que encapsula resultado do SimpleRAG"""
    success: bool
    query: str
    result: str
    processing_time: float
    timestamp: str
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY PARA RESPOSTAS
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleResponseFactory:
    """Factory para criar respostas a partir do resultado do SimpleRAG"""
    
    @staticmethod
    def create_search_response(
        query: str, 
        result: str, 
        processing_time: float,
        max_results: Optional[int] = None
    ) -> SearchResponse:
        """Cria SearchResponse a partir do resultado do SimpleRAG"""
        
        # Preparar fontes baseadas na configuração
        sources = [{
            "type": "rag_search",
            "model": system_config.rag.llm_model,
            "embedding_model": system_config.rag.embedding_model,
            "collection": system_config.rag.collection_name
        }]
        
        # Preparar metadata
        metadata = {
            "max_results": max_results or system_config.rag.max_candidates,
            "model_used": system_config.rag.llm_model,
            "embedding_model": system_config.rag.embedding_model,
            "processing_method": "simple_rag"
        }
        
        return SearchResponse(
            success=bool(result),
            query=query,
            result=result or "Nenhum resultado encontrado",
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            sources=sources,
            metadata=metadata,
            error=None if result else "Nenhum documento relevante encontrado"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL SIMPLIFICADO
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleAPIState:
    """Estado global simplificado da API"""
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.is_ready = False
        self.rag: Optional[SimpleRAG] = None
        
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    def increment_requests(self):
        self.request_count += 1

# Estado global
api_state = SimpleAPIState()

# ═══════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO E LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle da aplicação"""
    # Startup
    logger.info("🚀 Iniciando API RAG Simples Refatorada...")
    
    try:
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Validar configuração
        validation = system_config.validate_all()
        if not validation["rag_valid"]:
            raise RuntimeError("Configuração RAG inválida")
        
        # Inicializar sistema RAG
        await initialize_rag_system()
        
        api_state.is_ready = True
        logger.info("✅ API RAG Simples iniciada com sucesso")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise
    
    # Shutdown
    logger.info("🛑 Finalizando API RAG Simples...")
    api_state.is_ready = False

async def initialize_rag_system():
    """Inicializa o sistema RAG"""
    try:
        logger.info("🔍 Inicializando sistema RAG...")
        
        # Verificar variáveis de ambiente essenciais
        required_vars = [
            "VOYAGE_API_KEY",
            "ASTRA_DB_API_ENDPOINT", 
            "ASTRA_DB_APPLICATION_TOKEN",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise RuntimeError(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
        
        # Inicializar SimpleRAG
        api_state.rag = SimpleRAG()
        
        logger.info("✅ Sistema RAG inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do sistema RAG: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO FASTAPI
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Sistema RAG Simples - API Refatorada",
    description="API REST simplificada usando modelos nativos do sistema RAG",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS para produção
if os.getenv("ENABLE_CORS", "false").lower() == "true":
    cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDÊNCIAS E UTILITÁRIOS
# ═══════════════════════════════════════════════════════════════════════════════

def get_api_state() -> SimpleAPIState:
    """Dependency para obter estado da API"""
    return api_state

def check_api_ready(state: SimpleAPIState = Depends(get_api_state)):
    """Verifica se a API está pronta"""
    if not state.is_ready:
        raise HTTPException(
            status_code=503,
            detail="API ainda não está pronta. Tente novamente em alguns segundos."
        )
    return state

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS PRINCIPAIS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check(state: SimpleAPIState = Depends(get_api_state)):
    """Endpoint de health check"""
    return {
        "status": "healthy" if state.is_ready else "starting",
        "uptime": state.get_uptime(),
        "requests_processed": state.request_count,
        "rag_ready": state.rag is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/search", response_model=SearchResponse)
async def search_documents(
    query: SearchQuery,
    state: SimpleAPIState = Depends(check_api_ready),
    _: str = Depends(verify_token)
):
    """
    Endpoint principal para busca RAG simples.
    Usa diretamente o SimpleRAG com modelos nativos.
    """
    start_time = time.time()
    state.increment_requests()
    
    try:
        logger.info(f"🔍 Nova busca: {query.query}")
        
        # Validar consulta
        validation_result = validate_query(query.query)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Consulta inválida: {validation_result.error_message}"
            )
        
        # Executar busca usando SimpleRAG nativo
        result = await asyncio.to_thread(state.rag.search, query.query)
        
        # Usar factory para criar resposta
        processing_time = time.time() - start_time
        response = SimpleResponseFactory.create_search_response(
            query.query, 
            result, 
            processing_time,
            query.max_results
        )
        
        logger.info(f"✅ Busca processada em {processing_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no processamento: {e}")
        processing_time = time.time() - start_time
        
        # Retornar resposta de erro usando factory
        return SimpleResponseFactory.create_search_response(
            query.query,
            "",
            processing_time,
            query.max_results
        )

@app.delete("/documents/{collection_name}")
async def delete_documents_endpoint(
    collection_name: str,
    state: SimpleAPIState = Depends(check_api_ready),
    _: str = Depends(verify_token)
):
    """Deleta documentos de uma coleção"""
    try:
        logger.info(f"🗑️ Deletando documentos da coleção: {collection_name}")
        
        result = delete_documents(collection_name)
        
        return {
            "success": True,
            "message": f"Documentos deletados da coleção {collection_name}",
            "details": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar documentos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar documentos: {str(e)}"
        )

@app.get("/config")
async def get_config(
    state: SimpleAPIState = Depends(check_api_ready),
    _: str = Depends(verify_token)
):
    """Retorna configuração atual do sistema (informações não-sensíveis)"""
    return {
        "models": {
            "llm": system_config.rag.llm_model,
            "embedding": system_config.rag.embedding_model,
            "multimodal": system_config.rag.multimodal_model
        },
        "limits": {
            "max_candidates": system_config.rag.max_candidates,
            "max_tokens_per_input": system_config.rag.max_tokens_per_input
        },
        "database": {
            "collection_name": system_config.rag.collection_name,
            "embedding_dimension": system_config.rag.voyage_embedding_dim
        }
    }

@app.get("/stats")
async def get_stats(
    state: SimpleAPIState = Depends(check_api_ready),
    _: str = Depends(verify_token)
):
    """Estatísticas da API"""
    return {
        "uptime_seconds": state.get_uptime(),
        "total_requests": state.request_count,
        "api_ready": state.is_ready,
        "rag_initialized": state.rag is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configuração do servidor
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    workers = int(os.getenv("API_WORKERS", 1))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Iniciando servidor API RAG Simples em {host}:{port}")
    
    uvicorn.run(
        "api_simple:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level=log_level.lower(),
        access_log=True
    )