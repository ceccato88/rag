#!/usr/bin/env python3
"""
🚀 API de Produção - Sistema RAG Multi-Agente Refatorado

API REST simplificada usando modelos nativos do multi-agent-researcher.
Utiliza AgentResult diretamente sem conversões manuais desnecessárias.
"""

import os
import sys
import time
import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importações de produção (opcionais)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False

# Importações do sistema multi-agente (PATH)
sys.path.append('/workspaces/rag/multi-agent-researcher/src')

from config import SystemConfig
from search import SimpleRAG
from utils.validation import validate_query
from utils.metrics import ProcessingMetrics

# Modelos nativos do multi-agent-researcher
from researcher.agents.openai_lead_researcher import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext, AgentResult, AgentState
from researcher.memory.base import InMemoryStorage, ResearchMemory

# Import de funções de manutenção
sys.path.append(os.path.join(os.path.dirname(__file__), 'maintenance'))
from delete_collection import delete_documents

# Import do indexer (condicional)
try:
    from indexer_simple import process_pdf_from_url, create_doc_source_name
    INDEXER_AVAILABLE = True
except ImportError:
    try:
        from indexer import process_pdf_from_url, create_doc_source_name
        INDEXER_AVAILABLE = True
    except ImportError:
        INDEXER_AVAILABLE = False
        def process_pdf_from_url(url: str, doc_source: str = None) -> bool:
            return False
        def create_doc_source_name(url: str) -> str:
            return url.split("/")[-1]

# Configuração de logging
log_level = os.getenv("API_LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/logs/api_multiagent.log")
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

class ResearchQuery(BaseModel):
    """Consulta de pesquisa simplificada"""
    query: str = Field(..., min_length=3, max_length=1000, description="Consulta do usuário")
    objective: Optional[str] = Field(default=None, max_length=500, description="Objetivo específico da pesquisa")

class ResearchResponse(BaseModel):
    """Resposta de pesquisa que encapsula AgentResult nativo"""
    success: bool
    query: str
    result: str
    agent_id: str
    status: str
    processing_time: float
    timestamp: str
    confidence_score: Optional[float] = None
    sources: List[Dict[str, Any]] = []
    reasoning_trace: Optional[str] = None
    error: Optional[str] = None

class IndexRequest(BaseModel):
    """Requisição para indexação de documento"""
    url: str = Field(..., description="URL do PDF para indexar")
    doc_source: Optional[str] = Field(None, description="Nome/identificador do documento")

class IndexResponse(BaseModel):
    """Resposta da indexação"""
    success: bool
    message: str
    doc_source: str

# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY PARA RESPOSTAS
# ═══════════════════════════════════════════════════════════════════════════════

class ResponseFactory:
    """Factory para criar respostas a partir de AgentResult nativo"""
    
    @staticmethod
    def create_research_response(query: str, agent_result: AgentResult) -> ResearchResponse:
        """Cria ResearchResponse a partir de AgentResult nativo"""
        processing_time = 0.0
        if agent_result.start_time and agent_result.end_time:
            processing_time = (agent_result.end_time - agent_result.start_time).total_seconds()
        
        # Extrair informações da saída se disponível
        confidence_score = None
        sources = []
        
        # Se o resultado tem metadata, extrair informações
        if hasattr(agent_result, 'metadata') and agent_result.metadata:
            confidence_score = agent_result.metadata.get('confidence_score')
            sources = agent_result.metadata.get('sources', [])
        
        return ResearchResponse(
            success=agent_result.status == AgentState.COMPLETED,
            query=query,
            result=agent_result.output or agent_result.error or "Nenhum resultado disponível",
            agent_id=agent_result.agent_id,
            status=agent_result.status.name,
            processing_time=processing_time,
            timestamp=agent_result.end_time.isoformat() if agent_result.end_time else datetime.utcnow().isoformat(),
            confidence_score=confidence_score,
            sources=sources,
            reasoning_trace=getattr(agent_result, 'reasoning_trace', None),
            error=agent_result.error if agent_result.status == AgentState.FAILED else None
        )

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL SIMPLIFICADO
# ═══════════════════════════════════════════════════════════════════════════════

class APIState:
    """Estado global simplificado da API"""
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.is_ready = False
        self.lead_researcher: Optional[OpenAILeadResearcher] = None
        self.research_memory: Optional[ResearchMemory] = None
        
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
    logger.info("🚀 Iniciando API Multi-Agente Refatorada...")
    
    try:
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Validar configuração
        validation = system_config.validate_all()
        if not validation["multiagent_valid"]:
            raise RuntimeError("Configuração Multi-Agente inválida")
        
        # Inicializar sistema multi-agente
        await initialize_multiagent_system()
        
        api_state.is_ready = True
        logger.info("✅ API Multi-Agente iniciada com sucesso")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise
    
    # Shutdown
    logger.info("🛑 Finalizando API Multi-Agente...")
    api_state.is_ready = False

async def initialize_multiagent_system():
    """Inicializa o sistema multi-agente"""
    try:
        logger.info("🤖 Inicializando sistema multi-agente...")
        
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
        
        # Inicializar memória de pesquisa
        memory_storage = InMemoryStorage()
        api_state.research_memory = ResearchMemory(memory_storage)
        
        # Configurar lead researcher
        lead_config = OpenAILeadConfig.from_env()
        api_state.lead_researcher = OpenAILeadResearcher(
            config=lead_config,
            agent_id=str(uuid.uuid4()),
            name="API-Lead-Researcher"
        )
        
        logger.info("✅ Sistema multi-agente inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do sistema multi-agente: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO FASTAPI
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Sistema RAG Multi-Agente - API Refatorada",
    description="API REST simplificada usando modelos nativos do multi-agent-researcher",
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

# Aplicar configurações de produção
if system_config.production.production_mode:
    
    # Rate Limiting se habilitado e disponível
    if system_config.production.enable_rate_limiting and SLOWAPI_AVAILABLE:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Headers de segurança
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        if system_config.production.production_mode:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDÊNCIAS E UTILITÁRIOS
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

@app.get("/health")
async def health_check(state: APIState = Depends(get_api_state)):
    """Endpoint de health check"""
    return {
        "status": "healthy" if state.is_ready else "starting",
        "uptime": state.get_uptime(),
        "requests_processed": state.request_count,
        "multiagent_ready": state.lead_researcher is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/research", response_model=ResearchResponse)
async def research_query(
    query: ResearchQuery,
    state: APIState = Depends(check_api_ready),
    _: str = Depends(verify_token)
):
    """
    Endpoint principal para consultas de pesquisa.
    Usa diretamente o OpenAILeadResearcher e modelos nativos AgentResult.
    """
    start_time = time.time()
    state.increment_requests()
    
    try:
        logger.info(f"🔍 Nova consulta: {query.query}")
        
        # Validar consulta
        validation_result = validate_query(query.query)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Consulta inválida: {validation_result.error_message}"
            )
        
        # Criar contexto usando modelo nativo
        context = AgentContext(
            query=query.query,
            objective=query.objective or f"Pesquisar informações sobre: {query.query}",
            metadata={"api_request": True, "timestamp": datetime.utcnow().isoformat()}
        )
        
        # Executar pesquisa usando o lead researcher nativo
        agent_result = await state.lead_researcher.run(context)
        
        # Usar factory para criar resposta
        response = ResponseFactory.create_research_response(query.query, agent_result)
        
        logger.info(f"✅ Consulta processada em {time.time() - start_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no processamento: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@app.post("/index", response_model=IndexResponse)
async def index_document(
    request: IndexRequest,
    state: APIState = Depends(check_api_ready),
    _: str = Depends(verify_token)
):
    """Indexa documento PDF por URL"""
    if not INDEXER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Serviço de indexação não disponível"
        )
    
    try:
        logger.info(f"📄 Indexando documento: {request.url}")
        
        # Criar nome do documento se não fornecido
        doc_source = request.doc_source or create_doc_source_name(request.url)
        
        # Processar PDF
        success = process_pdf_from_url(request.url, doc_source)
        
        if success:
            return IndexResponse(
                success=True,
                message="Documento indexado com sucesso",
                doc_source=doc_source
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Falha na indexação do documento"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na indexação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na indexação: {str(e)}"
        )

@app.delete("/documents/{collection_name}")
async def delete_documents_endpoint(
    collection_name: str,
    state: APIState = Depends(check_api_ready),
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

@app.get("/stats")
async def get_stats(
    state: APIState = Depends(check_api_ready),
    _: str = Depends(verify_token)
):
    """Estatísticas da API"""
    return {
        "uptime_seconds": state.get_uptime(),
        "total_requests": state.request_count,
        "api_ready": state.is_ready,
        "multiagent_initialized": state.lead_researcher is not None,
        "indexer_available": INDEXER_AVAILABLE,
        "rate_limiting_available": SLOWAPI_AVAILABLE,
        "production_mode": system_config.production.production_mode,
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
    
    logger.info(f"🚀 Iniciando servidor API em {host}:{port}")
    
    uvicorn.run(
        "api_multiagent:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level=log_level.lower(),
        access_log=True
    )