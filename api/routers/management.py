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

def safe_delete_documents(doc_prefix: str = None) -> dict:
    """
    Deleta documentos da collection de forma segura por prefixo ou todos
    
    Args:
        doc_prefix: Se fornecido, deleta apenas documentos cujo doc_source comece com este prefixo
                   Se None, deleta TODOS os documentos
    """
    try:
        from dotenv import load_dotenv
        from astrapy import DataAPIClient
        import os
        
        # Carregar env vars
        load_dotenv()
        
        # Usar env vars diretamente para evitar conflitos de config
        token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        collection_name = "pdf_documents"
        
        if not token or not endpoint:
            return {"success": False, "error": "Configuração AstraDB não encontrada"}
        
        # Conectar ao AstraDB
        client = DataAPIClient(token=token)
        database = client.get_database(endpoint)
        collection = database.get_collection(collection_name)
        
        # Determinar filtro de busca
        if doc_prefix:
            # AstraDB não suporta regex, vamos usar correspondência exata primeiro
            filter_query = {"doc_source": doc_prefix}
            logger.info(f"🗑️ Deletando documentos com doc_source: {doc_prefix}")
        else:
            filter_query = {}
            logger.info(f"🗑️ Deletando TODOS os documentos da collection")
        
        # Contar documentos antes
        count_before = collection.count_documents(filter_query, upper_bound=10000)
        logger.info(f"📊 Encontrados {count_before} documentos para deletar")
        
        if count_before == 0:
            return {"success": True, "deleted": 0, "message": "Nenhum documento encontrado"}
        
        # Deletar documentos
        result = collection.delete_many(filter_query)
        deleted_count = result.deleted_count
        
        # AstraDB pode retornar -1 quando deleta todos os documentos
        if deleted_count == -1:
            deleted_count = count_before
        
        logger.info(f"✅ Deletados {deleted_count} documentos com sucesso")
        
        return {
            "success": True,
            "deleted": deleted_count,
            "message": f"Deletados {deleted_count} documentos"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar documentos: {e}")
        return {"success": False, "error": str(e)}

def safe_delete_images(all_images: bool = False, doc_prefix: str = None) -> dict:
    """
    Deleta imagens da pasta correta (pdf_images na raiz) por prefixo ou todas
    
    Args:
        all_images: Se True, deleta TODAS as imagens
        doc_prefix: Se fornecido, deleta apenas imagens que começam com esse prefixo
    """
    try:
        import glob
        import os
        
        # Caminho correto das imagens (na raiz do projeto)
        images_dir = "/workspaces/rag/pdf_images"
        
        if not os.path.exists(images_dir):
            return {"success": True, "deleted": 0, "message": "Diretório de imagens não existe"}
        
        # Determinar padrão de busca
        if all_images:
            pattern = os.path.join(images_dir, "*")
            logger.info(f"🗑️ Deletando TODAS as imagens de: {images_dir}")
        elif doc_prefix:
            pattern = os.path.join(images_dir, f"{doc_prefix}*")
            logger.info(f"🗑️ Deletando imagens com prefixo: {doc_prefix}")
        else:
            return {"success": False, "error": "Deve especificar all_images=True ou fornecer doc_prefix"}
        
        # Encontrar arquivos correspondentes
        files_to_delete = glob.glob(pattern)
        
        # Filtrar apenas arquivos (não diretórios)
        files_to_delete = [f for f in files_to_delete if os.path.isfile(f)]
        
        logger.info(f"📊 Encontrados {len(files_to_delete)} arquivos para deletar")
        
        if len(files_to_delete) == 0:
            return {"success": True, "deleted": 0, "message": "Nenhum arquivo encontrado"}
        
        # Deletar arquivos
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_count += 1
                logger.debug(f"🗑️ Deletado: {os.path.basename(file_path)}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao deletar {file_path}: {e}")
        
        logger.info(f"✅ Deletados {deleted_count} arquivos de imagem")
        
        return {
            "success": True,
            "deleted": deleted_count,
            "message": f"Deletados {deleted_count} arquivos de imagem"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar imagens: {e}")
        return {"success": False, "error": str(e)}

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
    maintenance_path = workspace_root / "scripts" / "maintenance"
    if str(maintenance_path) not in sys.path:
        sys.path.append(str(maintenance_path))
    
    from delete_collection import delete_documents
    from delete_images import delete_images
    DELETE_AVAILABLE = True
    DELETE_IMAGES_AVAILABLE = True
    logger.info("✅ Funções de deleção disponíveis")
except ImportError as e:
    logger.warning(f"⚠️ Função de deleção não disponível: {e}")
    DELETE_AVAILABLE = False
    DELETE_IMAGES_AVAILABLE = False
    
    def delete_documents(all_docs: bool = False, doc_prefix: str = None):
        return {"error": "Função de deleção não disponível"}
    
    def delete_images(all_images: bool = False, doc_prefix: str = None):
        return {"error": "Função de deleção de imagens não disponível"}


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
    - Estatísticas de documentos indexados
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
            from src.core.indexer import index_pdf_native
            indexer_available = True
        except ImportError:
            indexer_available = False
        
        # Obter estatísticas de documentos
        total_documents = 0
        unique_doc_sources = 0
        
        try:
            # Importar configuração e conectar ao AstraDB
            from src.core.config import SystemConfig
            from astrapy import DataAPIClient
            from dotenv import load_dotenv
            
            load_dotenv()
            config = SystemConfig()
            
            # Verificar se configuração está válida
            validation = config.validate_all()
            if validation.get("rag_valid", False):
                # Conectar ao AstraDB
                client = DataAPIClient(token=config.rag.astra_db_application_token)
                database = client.get_database(config.rag.astra_db_api_endpoint)
                collection = database.get_collection(config.rag.collection_name)
                
                # Contar documentos
                total_documents = collection.count_documents({}, upper_bound=10000)
                
                # Contar fontes únicas
                pipeline = [
                    {"$group": {"_id": "$doc_source"}},
                    {"$count": "unique_sources"}
                ]
                
                try:
                    # AstraDB pode não suportar aggregation, usar fallback
                    distinct_sources = collection.distinct("doc_source")
                    unique_doc_sources = len(distinct_sources) if distinct_sources else 0
                except Exception:
                    # Fallback: estimar baseado em documentos únicos
                    if total_documents > 0:
                        sample_docs = list(collection.find({}, limit=100, projection={"doc_source": 1}))
                        sources_set = set(doc.get("doc_source") for doc in sample_docs if doc.get("doc_source"))
                        unique_doc_sources = len(sources_set)
                    
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível obter estatísticas de documentos: {e}")
            # Manter valores padrão (0, 0)
        
        stats = StatsResponse(
            uptime_seconds=state_manager.get_uptime(),
            total_requests=state_manager.metrics.total_requests,
            api_ready=state_manager.is_ready,
            multiagent_initialized=state_manager.lead_researcher is not None,
            indexer_available=indexer_available,
            rate_limiting_available=rate_limiting_available,
            production_mode=state_manager._components_initialized.get('production_mode', False),
            total_documents=total_documents,
            unique_doc_sources=unique_doc_sources,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise ProcessingError("obtenção de estatísticas", str(e))


@router.delete("/documents/{collection_name}", response_model=DeleteResponse, summary="Deletar Documentos")
async def delete_documents_endpoint(
    collection_name: str = PathParam(..., description="Nome da coleção para deletar"),
    doc_prefix: str = None,
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Deleta documentos de uma coleção específica.
    
    **Parâmetros:**
    - **collection_name**: Nome da coleção a ser deletada
    - **doc_prefix**: (Opcional) Prefixo do doc_source para deletar apenas documentos específicos
    
    **Comportamento:**
    - Sem `doc_prefix`: Deleta TODOS os documentos da coleção
    - Com `doc_prefix`: Deleta apenas documentos cujo `doc_source` começe com o prefixo
    
    **Exemplos:**
    - `/documents/pdf_documents` → Deleta todos os documentos
    - `/documents/pdf_documents?doc_prefix=2501.13956` → Deleta apenas docs do arXiv 2501.13956
    
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
        
        # Executar deleção (com ou sem prefixo)
        result = safe_delete_documents(doc_prefix=doc_prefix)
        
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


@router.delete("/images", response_model=DeleteResponse, summary="Deletar Imagens")
async def delete_images_endpoint(
    all_images: bool = False,
    doc_prefix: str = None,
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Deleta imagens extraídas dos PDFs.
    
    **Parâmetros:**
    - **all_images**: Se True, deleta TODAS as imagens (padrão: False)
    - **doc_prefix**: Se fornecido, deleta apenas imagens que começam com esse prefixo
    
    **Processo:**
    1. Localiza diretório de imagens (`data/pdf_images/`)
    2. Encontra arquivos correspondentes aos critérios
    3. Remove arquivos físicos do sistema
    4. Retorna estatísticas da operação
    
    **Retorna:**
    - Resultado da operação
    - Número de imagens deletadas
    - Detalhes da operação
    
    **Exemplo de uso:**
    ```bash
    # Deletar todas as imagens
    curl -X DELETE "http://localhost:8000/api/v1/images?all_images=true" \\
         -H "Authorization: Bearer YOUR_TOKEN"
    
    # Deletar imagens de um documento específico
    curl -X DELETE "http://localhost:8000/api/v1/images?doc_prefix=arxiv_2024" \\
         -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    try:
        if not DELETE_IMAGES_AVAILABLE:
            raise ProcessingError("deleção de imagens", "Função de deleção de imagens não disponível")
        
        logger.info(f"🖼️ Iniciando deleção de imagens - all: {all_images}, prefix: {doc_prefix}")
        
        # Validação básica
        if not all_images and not doc_prefix:
            raise ProcessingError("deleção de imagens", "Deve especificar 'all_images=true' ou fornecer 'doc_prefix'")
        
        # Executar deleção usando função segura
        result = safe_delete_images(all_images=all_images, doc_prefix=doc_prefix)
        
        if isinstance(result, dict) and "error" in result:
            raise ProcessingError("deleção de imagens", result["error"])
        
        response = DeleteResponse(
            success=True,
            message=f"Imagens deletadas com sucesso",
            details={
                "all_images": all_images,
                "doc_prefix": doc_prefix,
                "operation_result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"✅ Deleção de imagens concluída: {result.get('deleted', 0)} arquivos")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erro na deleção de imagens: {e}")
        raise ProcessingError("deleção de imagens", str(e))


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
        "api_version": "1.0",
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
                "cors_enabled": getattr(config.security, 'enable_cors', False),
                "rate_limiting": getattr(config.security, 'enable_rate_limiting', True),
                "production_mode": getattr(config.production, 'production_mode', True)
            },
            "features_enabled": {
                "metrics": getattr(config.production, 'enable_performance_metrics', False),
                "tracing": getattr(config.production, 'enable_debug_logs', False),
                "cors": getattr(config.security, 'enable_cors', False)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração: {e}")
        raise ProcessingError("obtenção de configuração", str(e))
