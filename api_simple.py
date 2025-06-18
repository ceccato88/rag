#!/usr/bin/env python3
"""
🚀 API de Produção - Sistema RAG Simples

API REST para o sistema RAG simples com busca semântica direta.
Fornece endpoints para consultas diretas ao sistema de recuperação.
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
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importações do sistema RAG
from config import SystemConfig
from search import SimpleRAG
from utils.validation import validate_query
from utils.metrics import ProcessingMetrics

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
# MODELOS DE DADOS
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleRAGQuery(BaseModel):
    """Modelo para consultas ao sistema RAG simples"""
    query: str = Field(..., min_length=3, max_length=500, description="Consulta do usuário")
    max_results: Optional[int] = Field(default=None, ge=1, le=20, description="Número máximo de resultados")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Threshold de similaridade")
    include_metadata: bool = Field(default=True, description="Incluir metadados na resposta")

class SimpleRAGResponse(BaseModel):
    """Modelo de resposta do sistema RAG simples"""
    success: bool
    query: str
    response: str
    results_count: int
    processing_time: float
    timestamp: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class HealthResponse(BaseModel):
    """Modelo de resposta do health check"""
    status: str
    version: str
    system_config: Dict[str, Any]
    uptime: float
    timestamp: str

class ErrorResponse(BaseModel):
    """Modelo de resposta de erro"""
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL DA API
# ═══════════════════════════════════════════════════════════════════════════════

class APIState:
    """Estado global da API"""
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.metrics = ProcessingMetrics()
        self.is_ready = False
        
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    def increment_requests(self):
        self.request_count += 1

# Estado global
api_state = APIState()

# ═══════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO E LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle da aplicação"""
    # Startup
    logger.info("🚀 Iniciando API RAG Simples...")
    
    try:
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Validar configuração
        validation = system_config.validate_all()
        if not validation["rag_valid"]:
            raise RuntimeError("Configuração RAG inválida")
        
        # Verificar conexões essenciais
        await verify_connections()
        
        api_state.is_ready = True
        logger.info("✅ API RAG Simples iniciada com sucesso")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise
    
    # Shutdown
    logger.info("🛑 Finalizando API RAG Simples...")
    api_state.is_ready = False

async def verify_connections():
    """Verifica conexões essenciais do sistema"""
    try:
        # Teste básico de conectividade
        logger.info("🔍 Verificando conexões do sistema...")
        
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
        
        logger.info("✅ Todas as conexões verificadas")
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação de conexões: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO FASTAPI
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Sistema RAG Simples - API de Produção",
    description="API REST para consultas ao sistema RAG com busca semântica direta",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure conforme necessário em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDÊNCIAS
# ═══════════════════════════════════════════════════════════════════════════════

def get_api_state() -> APIState:
    """Dependency para obter estado da API"""
    return api_state

def check_api_ready(state: APIState = Depends(get_api_state)):
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

@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raiz com informações básicas"""
    return {
        "service": "Sistema RAG Simples - API de Produção",
        "version": "1.0.0",
        "status": "running" if api_state.is_ready else "starting",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(state: APIState = Depends(get_api_state)):
    """Health check detalhado do sistema"""
    
    config_info = {
        "llm_model": system_config.rag.llm_model,
        "embedding_model": system_config.rag.embedding_model,
        "max_candidates": system_config.rag.max_candidates,
        "collection_name": system_config.rag.collection_name
    }
    
    return HealthResponse(
        status="healthy" if state.is_ready else "starting",
        version="1.0.0",
        system_config=config_info,
        uptime=state.get_uptime(),
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/search", response_model=SimpleRAGResponse)
async def simple_rag_search(
    query_data: SimpleRAGQuery,
    background_tasks: BackgroundTasks,
    state: APIState = Depends(check_api_ready),
    token: str = Depends(verify_token)
):
    """
    Endpoint principal para consultas RAG simples
    
    Realiza busca semântica direta no sistema RAG e retorna resposta baseada
    nos documentos mais relevantes encontrados.
    """
    
    start_time = time.time()
    request_id = f"req_{int(time.time())}_{state.request_count}"
    
    try:
        # Incrementar contador de requests
        state.increment_requests()
        
        # Validar query
        if not validate_query(query_data.query):
            raise HTTPException(
                status_code=400,
                detail="Query inválida. Deve ter entre 3 e 500 caracteres."
            )
        
        logger.info(f"🔍 [{request_id}] Processando consulta RAG: {query_data.query[:100]}...")
        
        # Configurar parâmetros da busca
        max_results = query_data.max_results or system_config.rag.max_candidates
        similarity_threshold = query_data.similarity_threshold or system_config.multiagent.similarity_threshold
        
        # Executar busca RAG
        rag = SimpleRAG()
        response = await asyncio.to_thread(
            rag.search,
            query_data.query
        )
        
        if not response:
            logger.warning(f"⚠️ [{request_id}] Nenhum resultado encontrado")
            raise HTTPException(
                status_code=404,
                detail="Nenhum documento relevante encontrado para sua consulta."
            )
        
        # Processar resultados
        response_text = response
        
        # Preparar fontes (simplificado para o SimpleRAG)
        sources = []
        if query_data.include_metadata:
            sources.append({
                "message": "Resposta gerada pelo sistema RAG",
                "model": system_config.rag.llm_model
            })
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ [{request_id}] Consulta processada em {processing_time:.2f}s")
        
        # Adicionar tarefa em background para métricas
        background_tasks.add_task(
            record_usage_metrics,
            request_id, 
            query_data.query, 
            1, 
            processing_time
        )
        
        return SimpleRAGResponse(
            success=True,
            query=query_data.query,
            response=response_text,
            results_count=1,
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            sources=sources,
            metadata={
                "request_id": request_id,
                "max_results": max_results,
                "similarity_threshold": similarity_threshold,
                "model_used": system_config.rag.llm_model
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Erro interno no processamento: {str(e)}"
        
        logger.error(f"❌ [{request_id}] {error_msg}")
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="internal_server_error",
                message=error_msg,
                timestamp=datetime.utcnow().isoformat(),
                request_id=request_id
            ).dict()
        )

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE UTILIDADE
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/config", response_model=Dict[str, Any])
async def get_config(
    state: APIState = Depends(check_api_ready),
    token: str = Depends(verify_token)
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
            "max_tokens_per_input": system_config.rag.max_tokens_per_input,
            "similarity_threshold": system_config.multiagent.similarity_threshold
        },
        "database": {
            "collection_name": system_config.rag.collection_name,
            "embedding_dimension": system_config.rag.voyage_embedding_dim
        },
        "processing": {
            "batch_size": system_config.processing.batch_size,
            "concurrency": system_config.processing.processing_concurrency
        }
    }

@app.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    state: APIState = Depends(check_api_ready),
    token: str = Depends(verify_token)
):
    """Retorna métricas de uso da API"""
    
    return {
        "uptime_seconds": state.get_uptime(),
        "total_requests": state.request_count,
        "status": "healthy" if state.is_ready else "starting",
        "timestamp": datetime.utcnow().isoformat()
    }

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def record_usage_metrics(request_id: str, query: str, results_count: int, processing_time: float):
    """Registra métricas de uso (tarefa em background)"""
    try:
        logger.info(f"📊 [{request_id}] Métricas: {results_count} resultados em {processing_time:.2f}s")
        # Aqui você pode implementar logging para sistemas externos, bancos de dados, etc.
    except Exception as e:
        logger.error(f"❌ Erro ao registrar métricas: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Função principal para executar a API"""
    
    # Configuração do servidor
    config = {
        "app": "api_simple:app",
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "reload": os.getenv("API_RELOAD", "false").lower() == "true",
        "workers": int(os.getenv("API_WORKERS", "1")),
        "log_level": os.getenv("API_LOG_LEVEL", "info").lower()
    }
    
    logger.info(f"🚀 Iniciando API RAG Simples em {config['host']}:{config['port']}")
    logger.info(f"📋 Configuração: {config}")
    
    # Executar servidor
    uvicorn.run(**config)

if __name__ == "__main__":
    main()