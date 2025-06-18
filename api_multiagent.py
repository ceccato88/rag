#!/usr/bin/env python3
"""
🚀 API de Produção - Sistema RAG Multi-Agente Completo

API REST para o sistema RAG multi-agente com reasoning avançado e especialização.
Fornece endpoints para consultas complexas processadas por agentes especializados.
"""

import os
import sys
import time
import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importações do sistema multi-agente
sys.path.append('/workspaces/rag/multi-agent-researcher/src')

from config import SystemConfig
from search import SimpleRAG
from utils.validation import validate_query
from utils.metrics import ProcessingMetrics

# Importações do sistema multi-agente
from researcher.agents.openai_lead_researcher import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.enhanced_rag_subagent import (
    EnhancedRAGSubagent, 
    SpecialistSelector,
    SpecialistType,
    EnhancedRAGSubagentConfig
)
from researcher.agents.base import AgentContext, AgentResult, AgentState
# from researcher.memory.memory_manager import InMemoryManager  # Import removido - arquivo não existe
from researcher.memory.base import ResearchMemory

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

class QueryComplexity(str, Enum):
    """Níveis de complexidade da consulta"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

class ProcessingMode(str, Enum):
    """Modos de processamento"""
    SYNC = "sync"          # Síncrono - retorna resultado final
    ASYNC = "async"        # Assíncrono - retorna job_id
    STREAM = "stream"      # Streaming - resultados em tempo real

class MultiAgentQuery(BaseModel):
    """Modelo para consultas ao sistema multi-agente"""
    query: str = Field(..., min_length=3, max_length=1000, description="Consulta do usuário")
    objective: Optional[str] = Field(default=None, max_length=500, description="Objetivo específico da pesquisa")
    complexity: Optional[QueryComplexity] = Field(default=None, description="Complexidade estimada da consulta")
    processing_mode: ProcessingMode = Field(default=ProcessingMode.SYNC, description="Modo de processamento")
    max_agents: Optional[int] = Field(default=None, ge=1, le=10, description="Número máximo de agentes")
    timeout_seconds: Optional[int] = Field(default=None, ge=30, le=600, description="Timeout em segundos")
    include_reasoning: bool = Field(default=True, description="Incluir processo de reasoning na resposta")
    specialist_types: Optional[List[SpecialistType]] = Field(default=None, description="Tipos específicos de especialistas")

class AgentExecutionStep(BaseModel):
    """Modelo para etapas de execução dos agentes"""
    step_id: str
    agent_id: str
    agent_type: str
    status: AgentState
    start_time: str
    end_time: Optional[str] = None
    thinking: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

class MultiAgentResponse(BaseModel):
    """Modelo de resposta do sistema multi-agente"""
    success: bool
    job_id: str
    query: str
    objective: str
    final_answer: str
    confidence_score: float
    processing_time: float
    complexity_detected: QueryComplexity
    agents_used: List[Dict[str, Any]]
    execution_steps: List[AgentExecutionStep]
    reasoning_trace: Optional[List[str]] = None
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: str

class JobStatus(BaseModel):
    """Status de job assíncrono"""
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0 to 1.0
    current_step: Optional[str] = None
    estimated_completion: Optional[str] = None
    result: Optional[MultiAgentResponse] = None
    error: Optional[str] = None

class ComplexityAnalysis(BaseModel):
    """Análise de complexidade da consulta"""
    detected_complexity: QueryComplexity
    reasoning: str
    recommended_agents: List[SpecialistType]
    estimated_time: int
    confidence: float

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL DA API
# ═══════════════════════════════════════════════════════════════════════════════

class MultiAgentAPIState:
    """Estado global da API multi-agente"""
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.active_jobs: Dict[str, JobStatus] = {}
        self.metrics = ProcessingMetrics()
        self.is_ready = False
        
        # Sistema multi-agente
        self.lead_researcher: Optional[OpenAILeadResearcher] = None
        self.specialist_selector = SpecialistSelector()
        # self.memory_manager = InMemoryManager()  # Comentado - classe não disponível
        self.research_memory: Optional[ResearchMemory] = None
        
        # WebSocket connections para streaming
        self.active_connections: Dict[str, WebSocket] = {}
        
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    def increment_requests(self):
        self.request_count += 1
    
    def add_job(self, job_id: str, job_status: JobStatus):
        self.active_jobs[job_id] = job_status
    
    def update_job(self, job_id: str, **updates):
        if job_id in self.active_jobs:
            for key, value in updates.items():
                setattr(self.active_jobs[job_id], key, value)
    
    def get_job(self, job_id: str) -> Optional[JobStatus]:
        return self.active_jobs.get(job_id)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove jobs antigos"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        to_remove = [
            job_id for job_id, job in self.active_jobs.items()
            if job.status in ["completed", "failed"] and 
               datetime.fromisoformat(job.result.timestamp if job.result else datetime.utcnow().isoformat()).timestamp() < cutoff_time
        ]
        for job_id in to_remove:
            del self.active_jobs[job_id]

# Estado global
api_state = MultiAgentAPIState()

# ═══════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO E LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle da aplicação"""
    # Startup
    logger.info("🚀 Iniciando API Multi-Agente...")
    
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
    
    # Fechar conexões ativas
    for connection in api_state.active_connections.values():
        try:
            await connection.close()
        except:
            pass

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
        # api_state.research_memory = ResearchMemory(api_state.memory_manager)  # Temporariamente comentado
        api_state.research_memory = None  # Placeholder até corrigir memory_manager
        
        # Configurar lead researcher
        lead_config = OpenAILeadConfig.from_env()
        api_state.lead_researcher = OpenAILeadResearcher(
            config=lead_config
        )
        
        logger.info("✅ Sistema multi-agente inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do sistema multi-agente: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO FASTAPI
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Sistema RAG Multi-Agente - API de Produção",
    description="API REST para consultas complexas com reasoning multi-agente especializado",
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

def get_api_state() -> MultiAgentAPIState:
    """Dependency para obter estado da API"""
    return api_state

def check_api_ready(state: MultiAgentAPIState = Depends(get_api_state)):
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

@app.get("/")
async def root():
    """Endpoint raiz com informações básicas"""
    return {
        "service": "Sistema RAG Multi-Agente - API de Produção",
        "version": "1.0.0",
        "status": "running" if api_state.is_ready else "starting",
        "capabilities": [
            "Multi-agent reasoning",
            "Specialized agent selection",
            "ReAct pattern processing",
            "Async and streaming processing",
            "Complex query decomposition"
        ],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check(state: MultiAgentAPIState = Depends(get_api_state)):
    """Health check detalhado do sistema"""
    
    return {
        "status": "healthy" if state.is_ready else "starting",
        "version": "1.0.0",
        "uptime_seconds": state.get_uptime(),
        "total_requests": state.request_count,
        "active_jobs": len(state.active_jobs),
        "active_connections": len(state.active_connections),
        "system_config": {
            "max_subagents": system_config.multiagent.max_subagents,
            "model": system_config.multiagent.model,
            "timeout": system_config.multiagent.subagent_timeout
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/analyze-complexity", response_model=ComplexityAnalysis)
async def analyze_query_complexity(
    query_data: Dict[str, str],
    state: MultiAgentAPIState = Depends(check_api_ready),
    token: str = Depends(verify_token)
):
    """
    Analisa a complexidade de uma consulta e recomenda estratégia de processamento
    """
    
    query = query_data.get("query", "")
    if not query or len(query) < 3:
        raise HTTPException(status_code=400, detail="Query muito curta")
    
    try:
        # Análise de complexidade baseada em heurísticas
        complexity = analyze_complexity(query)
        recommended_agents = state.specialist_selector.select_specialists(
            query, 
            query_data.get("objective", ""), 
            max_specialists=5
        )
        
        return ComplexityAnalysis(
            detected_complexity=complexity,
            reasoning=get_complexity_reasoning(query, complexity),
            recommended_agents=[get_specialist_type(agent) for agent in recommended_agents],
            estimated_time=estimate_processing_time(complexity),
            confidence=0.8  # Placeholder - poderia ser calculado com ML
        )
    
    except Exception as e:
        logger.error(f"❌ Erro na análise de complexidade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research", response_model=Union[MultiAgentResponse, Dict[str, str]])
async def multi_agent_research(
    query_data: MultiAgentQuery,
    background_tasks: BackgroundTasks,
    state: MultiAgentAPIState = Depends(check_api_ready),
    token: str = Depends(verify_token)
):
    """
    Endpoint principal para pesquisa multi-agente
    
    Suporta processamento síncrono, assíncrono e streaming baseado no processing_mode.
    """
    
    job_id = f"job_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    try:
        state.increment_requests()
        
        # Validar query
        if not validate_query(query_data.query):
            raise HTTPException(
                status_code=400,
                detail="Query inválida. Deve ter entre 3 e 1000 caracteres."
            )
        
        logger.info(f"🧠 [{job_id}] Iniciando pesquisa multi-agente: {query_data.query[:100]}...")
        
        # Determinar complexidade se não fornecida
        if query_data.complexity is None:
            query_data.complexity = analyze_complexity(query_data.query)
        
        # Configurar objetivo padrão
        if not query_data.objective:
            query_data.objective = f"Fornecer resposta abrangente sobre: {query_data.query}"
        
        # Processamento baseado no modo
        if query_data.processing_mode == ProcessingMode.ASYNC:
            # Criar job assíncrono
            job_status = JobStatus(
                job_id=job_id,
                status="pending",
                progress=0.0
            )
            state.add_job(job_id, job_status)
            
            # Executar em background
            background_tasks.add_task(
                execute_multiagent_research_async,
                job_id,
                query_data,
                state
            )
            
            return {"job_id": job_id, "status": "accepted", "estimated_time": estimate_processing_time(query_data.complexity)}
        
        elif query_data.processing_mode == ProcessingMode.SYNC:
            # Execução síncrona
            return await execute_multiagent_research_sync(job_id, query_data, state)
        
        else:  # STREAM
            raise HTTPException(
                status_code=501,
                detail="Modo streaming deve usar o endpoint WebSocket /research/stream"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [{job_id}] Erro na pesquisa multi-agente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/research/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    state: MultiAgentAPIState = Depends(check_api_ready),
    token: str = Depends(verify_token)
):
    """Consulta status de job assíncrono"""
    
    job = state.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    return job

@app.websocket("/research/stream")
async def stream_research(websocket: WebSocket, state: MultiAgentAPIState = Depends(get_api_state)):
    """WebSocket endpoint para pesquisa com streaming em tempo real"""
    
    await websocket.accept()
    connection_id = f"conn_{uuid.uuid4().hex[:8]}"
    state.active_connections[connection_id] = websocket
    
    try:
        # Receber query inicial
        data = await websocket.receive_json()
        query_data = MultiAgentQuery(**data)
        
        job_id = f"stream_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        logger.info(f"🌊 [{job_id}] Iniciando pesquisa streaming: {query_data.query[:100]}...")
        
        # Executar com streaming
        await execute_multiagent_research_stream(job_id, query_data, websocket)
        
    except WebSocketDisconnect:
        logger.info(f"🔌 Conexão WebSocket {connection_id} desconectada")
    except Exception as e:
        logger.error(f"❌ Erro no WebSocket {connection_id}: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        state.active_connections.pop(connection_id, None)

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTORES DE PESQUISA
# ═══════════════════════════════════════════════════════════════════════════════

async def execute_multiagent_research_sync(
    job_id: str, 
    query_data: MultiAgentQuery,
    state: MultiAgentAPIState
) -> MultiAgentResponse:
    """Execução síncrona da pesquisa multi-agente"""
    
    start_time = time.time()
    execution_steps: List[AgentExecutionStep] = []
    
    try:
        # Criar contexto da consulta
        context = AgentContext(
            query=query_data.query,
            objective=query_data.objective,
            constraints=[]
        )
        
        # Configurar timeout
        timeout = query_data.timeout_seconds or system_config.multiagent.subagent_timeout
        
        # Executar lead researcher
        logger.info(f"🎯 [{job_id}] Executando lead researcher...")
        
        result = await asyncio.wait_for(
            state.lead_researcher.run(context),
            timeout=timeout
        )
        
        # Processar resultado
        processing_time = time.time() - start_time
        
        # Extrair informações dos agentes utilizados
        agents_used = []
        if hasattr(result, 'subagent_results') and result.subagent_results:
            for subresult in result.subagent_results:
                agents_used.append({
                    "agent_id": subresult.agent_id,
                    "agent_type": subresult.__class__.__name__,
                    "status": subresult.status.value,
                    "execution_time": getattr(subresult, 'execution_time', 0.0)
                })
        
        # Calcular confidence score
        confidence_score = calculate_confidence_score(result, len(agents_used))
        
        logger.info(f"✅ [{job_id}] Pesquisa concluída em {processing_time:.2f}s")
        
        return MultiAgentResponse(
            success=result.status == AgentState.COMPLETED,
            job_id=job_id,
            query=query_data.query,
            objective=query_data.objective,
            final_answer=result.output,
            confidence_score=confidence_score,
            processing_time=processing_time,
            complexity_detected=query_data.complexity,
            agents_used=agents_used,
            execution_steps=execution_steps,
            reasoning_trace=result.thinking.split('\n') if query_data.include_reasoning and result.thinking else None,
            sources=extract_sources_from_result(result),
            metadata={
                "job_id": job_id,
                "lead_agent": state.lead_researcher.__class__.__name__,
                "timeout_used": timeout,
                "model": system_config.multiagent.model
            },
            timestamp=datetime.utcnow().isoformat()
        )
    
    except asyncio.TimeoutError:
        logger.error(f"⏰ [{job_id}] Timeout após {timeout}s")
        raise HTTPException(status_code=408, detail=f"Pesquisa excedeu timeout de {timeout}s")
    
    except Exception as e:
        logger.error(f"❌ [{job_id}] Erro na execução: {e}")
        raise

async def execute_multiagent_research_async(
    job_id: str,
    query_data: MultiAgentQuery,
    state: MultiAgentAPIState
):
    """Execução assíncrona da pesquisa multi-agente"""
    
    try:
        state.update_job(job_id, status="running", progress=0.1)
        
        # Executar pesquisa
        result = await execute_multiagent_research_sync(job_id, query_data, state)
        
        # Atualizar job com resultado
        state.update_job(
            job_id,
            status="completed",
            progress=1.0,
            result=result
        )
        
    except Exception as e:
        logger.error(f"❌ [{job_id}] Erro na execução assíncrona: {e}")
        state.update_job(
            job_id,
            status="failed",
            error=str(e)
        )

async def execute_multiagent_research_stream(
    job_id: str,
    query_data: MultiAgentQuery,
    websocket: WebSocket
):
    """Execução com streaming em tempo real"""
    
    try:
        # Enviar status inicial
        await websocket.send_json({
            "type": "status",
            "job_id": job_id,
            "status": "started",
            "message": "Iniciando pesquisa multi-agente..."
        })
        
        # Executar com updates em tempo real
        # Por simplicidade, aqui fazemos a execução normal e enviamos resultado final
        # Em uma implementação completa, integraria com callbacks dos agentes
        
        context = AgentContext(
            query=query_data.query,
            objective=query_data.objective,
            constraints=[]
        )
        
        result = await api_state.lead_researcher.run(context)
        
        # Enviar resultado final
        response = MultiAgentResponse(
            success=result.status == AgentState.COMPLETED,
            job_id=job_id,
            query=query_data.query,
            objective=query_data.objective,
            final_answer=result.output,
            confidence_score=calculate_confidence_score(result, 1),
            processing_time=0.0,  # Calculado em tempo real
            complexity_detected=query_data.complexity,
            agents_used=[],
            execution_steps=[],
            reasoning_trace=result.thinking.split('\n') if result.thinking else None,
            sources=[],
            metadata={"job_id": job_id},
            timestamp=datetime.utcnow().isoformat()
        )
        
        await websocket.send_json({
            "type": "result",
            "data": response.dict()
        })
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_complexity(query: str) -> QueryComplexity:
    """Analisa complexidade da query baseado em heurísticas"""
    
    query_lower = query.lower()
    
    # Palavras que indicam complexidade
    complex_indicators = [
        "compare", "analyze", "evaluate", "pros and cons", "advantages", "disadvantages",
        "methodology", "implementation", "architecture", "detailed", "comprehensive"
    ]
    
    expert_indicators = [
        "research paper", "academic", "technical specification", "algorithm",
        "mathematical", "statistical", "optimization", "performance analysis"
    ]
    
    # Contadores
    complex_count = sum(1 for indicator in complex_indicators if indicator in query_lower)
    expert_count = sum(1 for indicator in expert_indicators if indicator in query_lower)
    word_count = len(query.split())
    
    # Determinar complexidade
    if expert_count >= 2 or word_count > 50:
        return QueryComplexity.EXPERT
    elif complex_count >= 2 or word_count > 30:
        return QueryComplexity.COMPLEX
    elif complex_count >= 1 or word_count > 15:
        return QueryComplexity.MODERATE
    else:
        return QueryComplexity.SIMPLE

def get_complexity_reasoning(query: str, complexity: QueryComplexity) -> str:
    """Gera explicação da complexidade detectada"""
    
    reasoning_map = {
        QueryComplexity.SIMPLE: "Query simples com conceitos diretos",
        QueryComplexity.MODERATE: "Query moderada que requer alguma análise",
        QueryComplexity.COMPLEX: "Query complexa com múltiplos aspectos para análise",
        QueryComplexity.EXPERT: "Query especializada que requer conhecimento técnico profundo"
    }
    
    return reasoning_map.get(complexity, "Complexidade não determinada")

def estimate_processing_time(complexity: QueryComplexity) -> int:
    """Estima tempo de processamento baseado na complexidade"""
    
    time_estimates = {
        QueryComplexity.SIMPLE: 30,
        QueryComplexity.MODERATE: 60,
        QueryComplexity.COMPLEX: 120,
        QueryComplexity.EXPERT: 300
    }
    
    return time_estimates.get(complexity, 60)

def get_specialist_type(agent_class) -> SpecialistType:
    """Mapeia classe de agente para tipo de especialista"""
    
    name = agent_class.__name__.lower()
    
    if "concept" in name or "extraction" in name:
        return SpecialistType.CONCEPTUAL
    elif "comparative" in name or "comparison" in name:
        return SpecialistType.COMPARATIVE
    elif "technical" in name or "detail" in name:
        return SpecialistType.TECHNICAL
    elif "example" in name or "finder" in name:
        return SpecialistType.EXAMPLES
    else:
        return SpecialistType.GENERAL

def calculate_confidence_score(result: AgentResult, agents_count: int) -> float:
    """Calcula score de confiança baseado no resultado"""
    
    base_score = 0.7 if result.status == AgentState.COMPLETED else 0.3
    
    # Ajuste baseado no número de agentes
    agent_bonus = min(0.2, agents_count * 0.05)
    
    # Ajuste baseado no tamanho da resposta
    length_bonus = min(0.1, len(result.output) / 10000)
    
    return min(1.0, base_score + agent_bonus + length_bonus)

def extract_sources_from_result(result: AgentResult) -> List[Dict[str, Any]]:
    """Extrai fontes do resultado"""
    
    # Por simplicidade, retorna lista vazia
    # Em implementação completa, extrairia fontes dos subagentes
    return []

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE UTILIDADE
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/specialists", response_model=Dict[str, List[str]])
async def list_available_specialists(token: str = Depends(verify_token)):
    """Lista tipos de especialistas disponíveis"""
    
    return {
        "available_specialists": [spec.value for spec in SpecialistType],
        "descriptions": {
            "general": "Pesquisa geral e abrangente",
            "conceptual": "Foco em definições e conceitos fundamentais",
            "comparative": "Análises comparativas e alternativas",
            "technical": "Detalhes técnicos e implementação",
            "examples": "Exemplos práticos e casos de uso",
            "historical": "Contexto histórico e evolução"
        }
    }

@app.get("/jobs", response_model=Dict[str, Any])
async def list_active_jobs(
    state: MultiAgentAPIState = Depends(check_api_ready),
    token: str = Depends(verify_token)
):
    """Lista jobs ativos"""
    
    # Limpar jobs antigos
    state.cleanup_old_jobs()
    
    jobs_summary = {}
    for job_id, job in state.active_jobs.items():
        jobs_summary[job_id] = {
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step
        }
    
    return {
        "active_jobs": len(state.active_jobs),
        "jobs": jobs_summary,
        "total_processed": state.request_count
    }

# ═══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Função principal para executar a API"""
    
    # Configuração do servidor
    config = {
        "app": "api_multiagent:app",
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8001")),
        "reload": os.getenv("API_RELOAD", "false").lower() == "true",
        "workers": int(os.getenv("API_WORKERS", "1")),
        "log_level": os.getenv("API_LOG_LEVEL", "info").lower()
    }
    
    logger.info(f"🚀 Iniciando API Multi-Agente em {config['host']}:{config['port']}")
    logger.info(f"📋 Configuração: {config}")
    
    # Executar servidor
    uvicorn.run(**config)

if __name__ == "__main__":
    main()