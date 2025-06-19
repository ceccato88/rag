#!/usr/bin/env python3
"""
⚙️ Router de Gerenciamento - API Multi-Agente

Endpoints para administração, health checks e operações de gerenciamento.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Path as PathParam

from ..models.schemas import (
    HealthResponse, 
    DetailedHealthResponse, 
    StatsResponse, 
    DeleteResponse
)
from ..core.state import APIStateManager
from ..dependencies import (
    get_api_state,
    get_authenticated_state,
    basic_health_check,
    detailed_health_check
)
from ..utils.errors import ProcessingError

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Gerenciamento"],
    responses={
        401: {"description": "Token de acesso inválido"},
        503: {"description": "Serviço indisponível"}
    }
)

# Importar função de deleção
try:
    import sys
    from pathlib import Path
    
    # Adicionar path do workspace
    workspace_root = Path("/workspaces/rag")
    maintenance_path = workspace_root / "maintenance"
    if str(maintenance_path) not in sys.path:
        sys.path.append(str(maintenance_path))
    
    from delete_collection import delete_documents
    DELETE_AVAILABLE = True
    logger.info("✅ Função de deleção disponível")
except ImportError as e:
    logger.warning(f"⚠️ Função de deleção não disponível: {e}")
    DELETE_AVAILABLE = False
    
    def delete_documents(collection_name: str):
        return {"error": "Função de deleção não disponível"}


@router.get("/health", response_model=HealthResponse, summary="Health Check Básico")
async def health_check(health_data = Depends(basic_health_check)):
    """
    Endpoint de health check básico que não requer autenticação.
    
    **Retorna:**
    - Status geral do sistema
    - Tempo de atividade
    - Status dos componentes principais
    - Métricas básicas de requisições
    
    **Status possíveis:**
    - `healthy`: Sistema funcionando normalmente
    - `initializing`: Sistema ainda está inicializando
    - `unhealthy`: Sistema com problemas
    """
    return HealthResponse(**health_data)


@router.get("/health/detailed", response_model=DetailedHealthResponse, summary="Health Check Detalhado")
async def detailed_health_check_endpoint(
    health_data = Depends(detailed_health_check)
):
    """
    Endpoint de health check detalhado que requer API inicializada.
    
    **Requer:** API pronta (mas não autenticação)
    
    **Retorna:**
    - Todas as informações do health check básico
    - Configurações do ambiente
    - Status detalhado de cada componente
    - Informações de inicialização
    """
    return DetailedHealthResponse(**health_data)


@router.get("/stats", response_model=StatsResponse, summary="Estatísticas do Sistema")
async def get_system_stats(
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Retorna estatísticas detalhadas do sistema.
    
    **Requer:** Autenticação
    
    **Retorna:**
    - Métricas de performance
    - Status de componentes
    - Informações de disponibilidade
    - Configurações ativas
    """
    try:
        # Verificar disponibilidade de componentes opcionais
        try:
            from slowapi import Limiter
            rate_limiting_available = True
        except ImportError:
            rate_limiting_available = False
        
        # Verificar indexer
        try:
            from indexer import index_pdf_native
            indexer_available = True
        except ImportError:
            indexer_available = False
        
        stats = StatsResponse(
            uptime_seconds=state_manager.get_uptime(),
            total_requests=state_manager.metrics.total_requests,
            api_ready=state_manager.is_ready,
            multiagent_initialized=state_manager.lead_researcher is not None,
            indexer_available=indexer_available,
            rate_limiting_available=rate_limiting_available,
            production_mode=state_manager._components_initialized.get('production_mode', False),
            timestamp=datetime.utcnow().isoformat()
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise ProcessingError("obtenção de estatísticas", str(e))


@router.delete("/documents/{collection_name}", response_model=DeleteResponse, summary="Deletar Documentos")
async def delete_documents_endpoint(
    collection_name: str = PathParam(..., description="Nome da coleção para deletar"),
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Deleta todos os documentos de uma coleção específica.
    
    **Parâmetros:**
    - **collection_name**: Nome da coleção a ser deletada
    
    **Requer:** Autenticação
    
    **⚠️ Atenção:** Esta operação é irreversível!
    
    **Retorna:**
    - Status da operação
    - Detalhes sobre documentos deletados
    """
    if not DELETE_AVAILABLE:
        raise ProcessingError("deleção", "Função de deleção não disponível")
    
    try:
        logger.info(f"🗑️ Iniciando deleção da coleção: {collection_name}")
        
        # Validar nome da coleção
        if not collection_name or not collection_name.strip():
            raise ProcessingError("deleção", "Nome da coleção não pode estar vazio")
        
        collection_name = collection_name.strip()
        
        # Executar deleção
        result = delete_documents(collection_name)
        
        if isinstance(result, dict) and "error" in result:
            raise ProcessingError("deleção", result["error"])
        
        response = DeleteResponse(
            success=True,
            message=f"Documentos deletados da coleção '{collection_name}' com sucesso",
            details={
                "collection": collection_name,
                "operation_result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"✅ Deleção concluída: {collection_name}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erro na deleção: {e}")
        raise ProcessingError("deleção", str(e))


@router.get("/version", summary="Versão da API")
async def get_api_version():
    """
    Retorna informações sobre a versão da API.
    
    **Retorna:**
    - Versão da API
    - Informações de build
    - Componentes disponíveis
    """
    return {
        "api_version": "2.0.0",
        "api_name": "Sistema RAG Multi-Agente",
        "build_date": "2025-06-19",
        "python_version": "3.12+",
        "framework": "FastAPI",
        "architecture": "Multi-Agent RAG",
        "components": {
            "multi_agent_researcher": "available",
            "simple_rag": "available", 
            "indexer": "available" if DELETE_AVAILABLE else "unavailable",
            "rate_limiting": "optional",
            "metrics": "enabled"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/config", summary="Configuração Atual")
async def get_current_config(
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Retorna a configuração atual do sistema (informações não sensíveis).
    
    **Requer:** Autenticação
    
    **Retorna:**
    - Configurações de servidor
    - Status de recursos
    - Informações de ambiente (sem dados sensíveis)
    """
    try:
        from ..core.config import config
        
        return {
            "environment_summary": config.get_environment_summary(),
            "server_config": {
                "host": config.server.host,
                "port": config.server.port,
                "workers": config.server.workers,
                "log_level": config.server.log_level
            },
            "security_config": {
                "cors_enabled": config.security.enable_cors,
                "rate_limiting": config.security.enable_rate_limiting,
                "production_mode": config.production.production_mode
            },
            "features_enabled": {
                "metrics": config.production.enable_metrics,
                "tracing": config.production.enable_tracing,
                "cors": config.security.enable_cors
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração: {e}")
        raise ProcessingError("obtenção de configuração", str(e))
