#!/usr/bin/env python3
"""
🚀 API Principal - Sistema RAG Multi-Agente

API REST modular e bem estruturada para sistema RAG multi-agente.
Atualizada para Pydantic V2 com arquitetura limpa e organizada.

Características:
- Arquitetura modular com separação clara de responsabilidades
- Pydantic V2 com field_validators
- Sistema robusto de tratamento de erros
- Middlewares customizados para segurança e monitoramento
- Injeção de dependências bem definida
- Health checks detalhados
- Métricas e observabilidade

Estrutura:
├── core/          # Configurações e estado central
├── utils/         # Utilitários e middlewares
├── models/        # Schemas Pydantic
├── routers/       # Endpoints organizados por funcionalidade
└── dependencies.py # Injeção de dependências
"""

import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Importações da nova estrutura modular
from .core.config import config
from .core.state import lifespan_manager
from .utils.middleware import setup_middlewares
from .utils.errors import ErrorHandler
from .routers import research_router, indexing_router, management_router
from .dependencies import get_rate_limiter

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, config.server.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.paths.log_dir / "api_multiagent.log")
    ]
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO FASTAPI
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="🚀 Sistema RAG Multi-Agente",
    description="""
    **API REST moderna para sistema RAG (Retrieval-Augmented Generation) multi-agente**
    
    ## Características Principais
    
    ### 🤖 Sistema Multi-Agente
    - **Lead Researcher**: Agente principal para pesquisas complexas
    - **Memória de Pesquisa**: Sistema de contexto persistente
    - **RAG Simples**: Sistema de busca vetorial rápido
    
    ### 📄 Indexação Inteligente
    - **Processamento de PDF**: Extração de texto e imagens
    - **Chunking Semântico**: Divisão inteligente de conteúdo
    - **Embeddings Vetoriais**: Busca por similaridade
    
    ### 🛡️ Recursos de Produção
    - **Autenticação Bearer Token**: Segurança robusta
    - **Rate Limiting**: Proteção contra abuso
    - **Métricas Detalhadas**: Monitoramento completo
    - **Health Checks**: Verificação de saúde do sistema
    
    ### 🔧 Arquitetura
    - **Modular**: Código bem organizado e manutenível
    - **Async/Await**: Performance otimizada
    - **Pydantic V2**: Validação moderna de dados
    - **Error Handling**: Tratamento estruturado de erros
    
    ## Autenticação
    
    Todos os endpoints (exceto `/health`) requerem autenticação via Bearer Token:
    
    ```
    Authorization: Bearer YOUR_API_TOKEN
    ```
    
    ## Rate Limiting
    
    - **Limite padrão**: 100 requisições por minuto por cliente
    - **Headers de resposta**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`
    - **Retry-After**: Informado quando limite é excedido
    
    ## Exemplos de Uso
    
    ### Pesquisa
    ```bash
    curl -X POST "http://localhost:8000/api/v1/research" \\
         -H "Authorization: Bearer YOUR_TOKEN" \\
         -H "Content-Type: application/json" \\
         -d '{"query": "Como funciona machine learning?"}'
    ```
    
    ### Indexação
    ```bash
    curl -X POST "http://localhost:8000/api/v1/index" \\
         -H "Authorization: Bearer YOUR_TOKEN" \\
         -H "Content-Type: application/json" \\
         -d '{"url": "https://example.com/document.pdf"}'
    ```
    """,
    version="1.0",
    lifespan=lifespan_manager,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE MIDDLEWARES E RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════════

# Configurar rate limiting se disponível
rate_limiter = get_rate_limiter()
if rate_limiter:
    app.state.limiter = rate_limiter
    
    # Adicionar handler de exceção para rate limiting
    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar todos os middlewares
setup_middlewares(app)

# ═══════════════════════════════════════════════════════════════════════════════
# HANDLER GLOBAL DE ERROS
# ═══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para todas as exceções não tratadas"""
    return ErrorHandler.create_error_response(exc, request)

# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRO DE ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

# Incluir routers com prefixos organizados
app.include_router(
    research_router,
    prefix="/api/v1"
)

app.include_router(
    indexing_router, 
    prefix="/api/v1"
)

app.include_router(
    management_router,
    prefix="/api/v1"
)

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT ROOT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", include_in_schema=False)
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "🚀 Sistema RAG Multi-Agente",
        "status": "online",
        "documentation": "/docs",
        "alternative_docs": "/redoc",
        "health_check": "/api/v1/health",
        "version": "1.0",
        "architecture": "Multi-Agent RAG",
        "features": [
            "🤖 Sistema Multi-Agente",
            "📄 Indexação Inteligente", 
            "🔍 Busca Semântica",
            "🛡️ Segurança Robusta",
            "📊 Métricas Detalhadas"
        ]
    }

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("🚀 Iniciando Sistema RAG Multi-Agente")
    logger.info(f"📋 Configuração: {config.get_environment_summary()}")
    
    # Executar servidor
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        workers=config.server.workers if not config.server.reload else 1,
        reload=config.server.reload,
        log_level=config.server.log_level.lower(),
        access_log=True,
        server_header=False,  # Remove header "Server: uvicorn"
        date_header=False     # Remove header "Date"
    )
