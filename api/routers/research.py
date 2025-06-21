#!/usr/bin/env python3
"""
🔍 Router de Pesquisa - API Multi-Agente

Endpoints relacionados à pesquisa e consultas RAG.
"""

import time
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..models.schemas import ResearchQuery, ResearchResponse
from ..core.state import APIStateManager
from ..dependencies import (
    get_authenticated_state,
    get_lead_researcher,
    track_request_metrics
)
from ..utils.errors import ErrorHandler, ValidationError, ProcessingError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/research",
    tags=["Pesquisa"],
    responses={
        401: {"description": "Token de acesso inválido"},
        503: {"description": "Serviço indisponível"},
        422: {"description": "Dados de entrada inválidos"}
    }
)


@router.post("", response_model=ResearchResponse, summary="Realizar Pesquisa")
async def research_query(
    query: ResearchQuery,
    state_manager: APIStateManager = Depends(get_authenticated_state),
    lead_researcher = Depends(get_lead_researcher),
    request_context = Depends(track_request_metrics)
):
    """
    Realiza uma consulta de pesquisa usando o sistema RAG multi-agente.
    
    **Parâmetros:**
    - **query**: Texto da consulta (3-1000 caracteres)
    - **objective**: Objetivo específico da pesquisa (opcional)
    
    **Retorna:**
    - Resultado da pesquisa com análise do agente
    - Informações sobre fontes e raciocínio
    - Métricas de processamento
    
    **Exemplo de uso:**
    ```json
    {
        "query": "Como funciona machine learning?",
        "objective": "Entender conceitos básicos para iniciantes"
    }
    ```
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Nova consulta de pesquisa: {query.query[:100]}...")
        
        # Validação adicional da query
        ErrorHandler.validate_query(query.query)
        
        # Importar modelos nativos do multi-agent-researcher
        try:
            import sys
            import os
            
            # Garantir paths corretos
            workspace_root = Path("/workspaces/rag")
            multiagent_src = workspace_root / "multi-agent-researcher" / "src"
            
            if str(multiagent_src) not in sys.path:
                sys.path.insert(0, str(multiagent_src))
            if str(workspace_root) not in sys.path:
                sys.path.insert(0, str(workspace_root))
            
            # Mudar temporariamente o diretório
            original_cwd = os.getcwd()
            os.chdir(workspace_root)
            
            from researcher.agents.base import AgentContext
            
            # Voltar ao diretório original
            os.chdir(original_cwd)
            
        except ImportError as e:
            logger.error(f"❌ Erro ao importar AgentContext: {e}")
            raise ProcessingError("pesquisa", "Módulos do sistema multi-agente não disponíveis")
        
        # Criar contexto usando modelo nativo
        context = AgentContext(
            query=query.query,
            objective=query.objective or f"Pesquisar informações sobre: {query.query}",
            metadata={
                "api_request": True,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request_context, 'get', lambda x, y: 'unknown')('request_id', 'unknown')
            }
        )
        
        # Executar pesquisa usando o lead researcher nativo
        logger.info(f"🤖 Executando pesquisa com Lead Researcher...")
        agent_result = await lead_researcher.run(context)
        
        # Calcular tempo de processamento
        processing_time = time.time() - start_time
        
        # Extrair informações do resultado
        confidence_score = None
        sources = []
        
        if hasattr(agent_result, 'metadata') and agent_result.metadata:
            confidence_score = agent_result.metadata.get('confidence_score')
            sources = agent_result.metadata.get('sources', [])
        
        # Criar resposta estruturada
        response = ResearchResponse(
            success=agent_result.status.name == "COMPLETED",
            query=query.query,
            result=agent_result.output or agent_result.error or "Nenhum resultado disponível",
            agent_id=agent_result.agent_id,
            status=agent_result.status.name,
            processing_time=processing_time,
            timestamp=agent_result.end_time.isoformat() if agent_result.end_time else datetime.utcnow().isoformat(),
            confidence_score=confidence_score,
            sources=sources,
            reasoning_trace=agent_result.reasoning_trace,  # Sempre presente no sistema enhanced
            error=agent_result.error if agent_result.status.name == "FAILED" else None
        )
        
        # Registrar métrica de sucesso
        await state_manager.metrics.record_request(processing_time, response.success)
        
        logger.info(f"✅ Pesquisa concluída em {processing_time:.2f}s - Status: {agent_result.status.name}")
        
        return response
        
    except ValidationError:
        # Erro de validação - re-raise para tratamento pelo handler
        await state_manager.metrics.record_request(time.time() - start_time, False)
        raise
        
    except Exception as e:
        # Erro não esperado
        processing_time = time.time() - start_time
        await state_manager.metrics.record_request(processing_time, False)
        
        logger.error(f"❌ Erro na pesquisa: {e}", exc_info=True)
        raise ProcessingError("pesquisa", str(e))


@router.get("/status", summary="Status do Sistema de Pesquisa")
async def research_status(
    state_manager: APIStateManager = Depends(get_authenticated_state),
    lead_researcher = Depends(get_lead_researcher)
):
    """
    Retorna o status do sistema de pesquisa e seus componentes.
    
    **Retorna:**
    - Status do Lead Researcher
    - Informações sobre disponibilidade
    - Estatísticas básicas
    """
    try:
        # Verificar se o lead researcher está funcional
        researcher_info = {
            "available": lead_researcher is not None,
            "agent_id": getattr(lead_researcher, 'agent_id', None),
            "name": getattr(lead_researcher, 'name', None),
            "config_model": getattr(lead_researcher, 'config', {}).model if hasattr(lead_researcher, 'config') else None
        }
        
        return {
            "research_system_ready": True,
            "lead_researcher": researcher_info,
            "system_metrics": state_manager.metrics.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status de pesquisa: {e}")
        raise ProcessingError("verificação de status", str(e))


@router.post("/simple", summary="Busca RAG Simples (Teste)")
async def simple_search(
    query: ResearchQuery,
    state_manager: APIStateManager = Depends(get_authenticated_state),
    request_context = Depends(track_request_metrics)
):
    """
    Teste direto do sistema SimpleRAG para diagnóstico.
    
    **Parâmetros:**
    - **query**: Texto da consulta para busca direta
    
    **Retorna:**
    - Resultado direto do SimpleRAG
    - Informações de diagnóstico
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Teste SimpleRAG: {query.query[:100]}...")
        
        # Verificar se SimpleRAG está disponível
        simple_rag = state_manager.simple_rag
        if not simple_rag:
            raise ProcessingError("simple_rag", "SimpleRAG não inicializado")
        
        # Executar busca direta usando o método RAG completo para obter sources
        logger.info("🔍 Executando busca direta com SimpleRAG...")
        
        # Usar o método search_and_answer do RAG interno para obter sources
        rag_result = simple_rag.rag.search_and_answer(query.query)
        
        # Calcular tempo de processamento
        processing_time = time.time() - start_time
        
        # Verificar se houve resultado
        if "error" in rag_result:
            success = False
            result = f"Erro: {rag_result['error']}"
            sources = []
        else:
            success = bool(rag_result.get("answer") and rag_result["answer"].strip())
            result = rag_result.get("answer", "")
            # Extrair sources dos detalhes das páginas selecionadas
            sources = []
            for page_detail in rag_result.get("selected_pages_details", []):
                sources.append({
                    "document": page_detail.get("document", ""),
                    "page": page_detail.get("page_number", 0),
                    "score": page_detail.get("similarity_score", 0.0)
                })
        
        return {
            "success": success,
            "query": query.query,
            "result": result[:500] + "..." if len(result) > 500 else result,
            "result_length": len(result) if result else 0,
            "sources": sources,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat(),
            "simple_rag_available": simple_rag is not None,
            "diagnostic": {
                "has_result": bool(result),
                "result_not_empty": bool(result and result.strip()),
                "no_error_message": "No results" not in (result or ""),
                "sources_count": len(sources)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na busca SimpleRAG: {e}")
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "query": query.query,
            "result": f"Erro: {str(e)}",
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/debug", summary="Diagnóstico do Sistema Multi-Agente")
async def debug_research_system(
    state_manager: APIStateManager = Depends(get_authenticated_state)
):
    """
    Endpoint de diagnóstico para verificar o estado do sistema multi-agente.
    """
    try:
        debug_info = {
            "api_state": {
                "ready": state_manager.is_ready,
                "initializing": state_manager.is_initializing,
                "uptime": state_manager.get_uptime()
            },
            "components": {
                "lead_researcher_available": state_manager.lead_researcher is not None,
                "research_memory_available": state_manager.research_memory is not None,
                "simple_rag_available": state_manager.simple_rag is not None
            },
            "lead_researcher_info": {},
            "simple_rag_info": {}
        }
        
        # Informações detalhadas do Lead Researcher
        if state_manager.lead_researcher:
            lead_researcher = state_manager.lead_researcher
            debug_info["lead_researcher_info"] = {
                "agent_id": getattr(lead_researcher, 'agent_id', 'N/A'),
                "name": getattr(lead_researcher, 'name', 'N/A'),
                "config_available": hasattr(lead_researcher, 'config'),
                "type": type(lead_researcher).__name__
            }
            
            # Verificar se tem acesso ao RAG
            if hasattr(lead_researcher, 'rag_system'):
                debug_info["lead_researcher_info"]["has_rag_system"] = True
                debug_info["lead_researcher_info"]["rag_type"] = type(lead_researcher.rag_system).__name__
            else:
                debug_info["lead_researcher_info"]["has_rag_system"] = False
        
        # Informações do SimpleRAG
        if state_manager.simple_rag:
            simple_rag = state_manager.simple_rag
            debug_info["simple_rag_info"] = {
                "type": type(simple_rag).__name__,
                "has_collection": hasattr(simple_rag, 'collection'),
                "collection_name": getattr(simple_rag.collection, 'name', 'N/A') if hasattr(simple_rag, 'collection') else 'N/A'
            }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ Erro no diagnóstico: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/direct", summary="Pesquisa RAG Direta via Lead Researcher")
async def direct_research(
    query: ResearchQuery,
    state_manager: APIStateManager = Depends(get_authenticated_state),
    request_context = Depends(track_request_metrics)
):
    """
    Pesquisa direta usando o SimpleRAG via Lead Researcher sem subagentes.
    
    **Parâmetros:**
    - **query**: Texto da consulta para pesquisa direta
    
    **Retorna:**
    - Resultado da pesquisa processado pelo Lead Researcher
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Pesquisa RAG direta: {query.query[:100]}...")
        
        # Verificar se Lead Researcher e RAG estão disponíveis
        lead_researcher = state_manager.lead_researcher
        if not lead_researcher:
            raise ProcessingError("lead_researcher", "Lead Researcher não inicializado")
        
        if not hasattr(lead_researcher, 'rag_system') or not lead_researcher.rag_system:
            raise ProcessingError("rag_system", "Sistema RAG não disponível no Lead Researcher")
        
        # Executar busca direta no RAG
        logger.info("🔍 Executando busca direta com SimpleRAG...")
        rag_result = lead_researcher.rag_system.search(query.query)
        
        # Calcular tempo de processamento
        processing_time = time.time() - start_time
        
        # Verificar se houve resultado
        success = bool(rag_result and rag_result.strip() and "No results" not in rag_result)
        
        # Criar resposta estruturada no formato ResearchResponse
        response = {
            "success": success,
            "query": query.query,
            "result": rag_result[:1000] + "..." if len(rag_result) > 1000 else rag_result,
            "agent_id": getattr(lead_researcher, 'agent_id', 'direct-search'),
            "status": "COMPLETED" if success else "NO_RESULTS",
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence_score": 0.8 if success else 0.0,
            "sources": ["SimpleRAG"] if success else [],
            "reasoning_trace": "Direct RAG search without subagents",
            "error": None if success else "No relevant documents found"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Erro na pesquisa direta: {e}")
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "query": query.query,
            "result": f"Erro na pesquisa: {str(e)}",
            "agent_id": "error",
            "status": "FAILED",
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence_score": 0.0,
            "sources": [],
            "reasoning_trace": None,
            "error": str(e)
        }


@router.post("/test-reasoning", summary="Teste do Reasoning Multi-Agente")
async def test_reasoning(
    query: ResearchQuery,
    state_manager: APIStateManager = Depends(get_authenticated_state),
    lead_researcher = Depends(get_lead_researcher)
):
    """
    Teste do sistema de reasoning do Lead Researcher para diagnóstico.
    """
    try:
        logger.info(f"🧠 Testando reasoning para: {query.query}")
        
        # Importar modelos necessários
        import sys
        import os
        from pathlib import Path
        
        workspace_root = Path("/workspaces/rag")
        multiagent_src = workspace_root / "multi-agent-researcher" / "src"
        
        if str(multiagent_src) not in sys.path:
            sys.path.insert(0, str(multiagent_src))
        
        original_cwd = os.getcwd()
        os.chdir(workspace_root)
        
        from researcher.agents.base import AgentContext
        
        os.chdir(original_cwd)
        
        # Criar contexto
        context = AgentContext(
            query=query.query,
            objective=query.objective or f"Pesquisar informações sobre: {query.query}",
            metadata={
                "api_request": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Testar apenas o planning
        logger.info("🧠 Executando fase de planning...")
        plan = await lead_researcher.plan(context)
        
        # Verificar se o RAG está disponível nos subagentes
        rag_info = {
            "lead_researcher_has_rag": hasattr(lead_researcher, 'rag_system'),
            "rag_system_type": type(lead_researcher.rag_system).__name__ if hasattr(lead_researcher, 'rag_system') else None
        }
        
        return {
            "success": True,
            "query": query.query,
            "plan_created": plan is not None,
            "plan_tasks": len(plan) if plan else 0,
            "plan_details": plan if plan else [],
            "rag_info": rag_info,
            "reasoning_available": hasattr(lead_researcher, 'reasoner'),
            "reasoning_type": type(lead_researcher.reasoner).__name__ if hasattr(lead_researcher, 'reasoner') else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de reasoning: {e}")
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.utcnow().isoformat()
        }
