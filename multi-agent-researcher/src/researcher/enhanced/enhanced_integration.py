#!/usr/bin/env python3
"""
Integração do Sistema Enhanced com a Arquitetura RAG Atual
Conecta os componentes enhanced com o sistema multi-agente existente
"""

import logging
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI

from .enhanced_models import (
    RAGDecomposition, EnhancedRAGResult, SpecialistType, QueryComplexity
)
from .enhanced_decomposition import RAGDecomposer
from .enhanced_evaluation import SubagentExecutor
from .enhanced_synthesis import EnhancedSynthesizer

# Import config do sistema principal
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
from src.core.config import SystemConfig

# Import para AgentResult
from ..agents.base import AgentResult, AgentState

# Configuração
config = SystemConfig()

# Import multiagent logger
from ..utils.multiagent_logger import get_multiagent_logger
logger = get_multiagent_logger("EnhancedIntegration")


class EnhancedRAGSystem:
    """Sistema RAG Enhanced integrado com a arquitetura atual"""
    
    def __init__(self, rag_system, openai_client: Optional[OpenAI] = None):
        """
        Inicializa sistema enhanced integrado
        
        Args:
            rag_system: Sistema RAG atual (SimpleRAG ou similar)
            openai_client: Cliente OpenAI (se None, cria um novo)
        """
        self.rag_system = rag_system
        self.openai_client = openai_client or OpenAI()
        
        # Componentes enhanced
        self.decomposer = RAGDecomposer(self.openai_client)
        self.synthesizer = EnhancedSynthesizer(self.openai_client)
        self.executor = SubagentExecutor(self.openai_client, rag_system)
        
        logger.info("🚀 Enhanced RAG System inicializado")
    
    async def enhanced_search(self, query: str) -> EnhancedRAGResult:
        """
        Executa busca enhanced completa
        
        Args:
            query: Query do usuário
            
        Returns:
            EnhancedRAGResult: Resultado enhanced completo
        """
        logger.info(f"🔍 Iniciando busca enhanced para: '{query[:50]}...'")
        logger.planning(f"Query recebida: {query}", {"query_length": len(query), "truncated": len(query) > 50})
        start_time = time.time()
        
        try:
            # 1. Decomposição da query
            logger.info("📋 Executando decomposição...")
            logger.planning("Iniciando decomposição da query")
            decompose_start = time.time()
            
            decomposition = self.decomposer.decompose(query)
            decompose_time = time.time() - decompose_start
            
            logger.planning(f"Decomposição concluída", {
                "complexity": decomposition.approach.complexity.value,
                "strategy": decomposition.approach.strategy.value,
                "subagents_count": len(decomposition.subagent_tasks),
                "refined_query": decomposition.refined_query,
                "duration": decompose_time
            })
            
            # 2. Executar tarefas dos subagentes
            logger.info(f"🤖 Executando {len(decomposition.subagent_tasks)} subagentes...")
            logger.coordination(f"Iniciando execução de {len(decomposition.subagent_tasks)} subagentes")
            subagent_results = []
            
            for i, task_spec in enumerate(decomposition.subagent_tasks):
                logger.info(f"Executando subagente {i+1}/{len(decomposition.subagent_tasks)}: {task_spec.specialist_type.value}")
                
                subagent_start = time.time()
                result = self.executor.execute_task(task_spec, decomposition.refined_query)
                subagent_time = time.time() - subagent_start
                
                logger.subagent_execution(
                    subagent_id=task_spec.specialist_type.value,
                    action=f"Processando: {task_spec.semantic_context[:100]}...",
                    result=f"Resultado obtido com {len(str(result))} caracteres",
                    duration=subagent_time
                )
                
                subagent_results.append(result)
            
            # 3. Síntese coordenada
            logger.info("🧩 Executando síntese coordenada...")
            synthesis_start = time.time()
            
            enhanced_result = self.synthesizer.synthesize_results(
                decomposition, subagent_results
            )
            synthesis_time = time.time() - synthesis_start
            
            logger.synthesis(f"Síntese concluída", {
                "subagents_processed": len(subagent_results),
                "final_answer_length": len(enhanced_result.final_answer),
                "confidence_score": enhanced_result.confidence_score,
                "sources_count": len(enhanced_result.sources_cited),
                "duration": synthesis_time
            })
            
            total_time = time.time() - start_time
            enhanced_result.total_processing_time = total_time
            
            logger.performance("enhanced_search_complete", total_time, {
                "query": query[:100],
                "decompose_time": decompose_time,
                "synthesis_time": synthesis_time,
                "subagents_used": len(decomposition.subagent_tasks),
                "confidence_score": enhanced_result.confidence_score
            })
            
            logger.info(f"✅ Busca enhanced concluída em {total_time:.2f}s")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Erro na busca enhanced: {e}", e, {"query": query, "duration": time.time() - start_time})
            raise
    
    def fallback_to_simple(self, query: str) -> Dict[str, Any]:
        """
        Fallback para busca simples em caso de erro
        
        Args:
            query: Query do usuário
            
        Returns:
            Dict: Resultado simples formatado
        """
        logger.info(f"⚠️ Executando fallback simples para: '{query[:50]}...'")
        logger.coordination("Fallback para sistema RAG simples ativado", {"query": query[:100]})
        
        fallback_start = time.time()
        
        try:
            # Usar sistema RAG atual
            result = self.rag_system.search_and_answer(query)
            fallback_time = time.time() - fallback_start
            
            logger.performance("fallback_simple_complete", fallback_time, {
                "query": query[:100],
                "sources_found": len(result.get("selected_pages_details", [])),
                "answer_length": len(result.get("answer", ""))
            })
            
            return {
                "success": True,
                "query": query,
                "result": result.get("answer", "Nenhum resultado encontrado"),
                "enhanced": False,
                "fallback_reason": "Sistema enhanced indisponível",
                "sources": result.get("selected_pages_details", []),
                "processing_time": fallback_time
            }
            
        except Exception as e:
            fallback_time = time.time() - fallback_start
            logger.error(f"Erro no fallback simples: {e}", e, {"query": query, "duration": fallback_time})
            return {
                "success": False,
                "query": query,
                "result": f"Erro: {str(e)}",
                "enhanced": False,
                "error": str(e)
            }


class EnhancedAPIAdapter:
    """Adaptador para integrar Enhanced System com API atual"""
    
    def __init__(self, enhanced_system: EnhancedRAGSystem):
        self.enhanced_system = enhanced_system
    
    async def process_research_query(
        self, 
        query: str, 
        objective: Optional[str] = None,
        use_enhanced: bool = True
    ) -> Dict[str, Any]:
        """
        Processa query de pesquisa usando sistema enhanced
        
        Args:
            query: Query do usuário
            objective: Objetivo específico (opcional)
            use_enhanced: Se deve usar sistema enhanced
            
        Returns:
            Dict: Resultado formatado para API
        """
        start_time = time.time()
        
        try:
            if use_enhanced:
                # Usar sistema enhanced
                enhanced_result = await self.enhanced_system.enhanced_search(query)
                
                return {
                    "success": enhanced_result.confidence_score > SystemConfig().rag.confidence_threshold,
                    "query": query,
                    "result": enhanced_result.final_answer,
                    "agent_id": "enhanced-rag",
                    "status": "COMPLETED",
                    "processing_time": enhanced_result.total_processing_time,
                    "confidence_score": enhanced_result.confidence_score,
                    "sources": enhanced_result.sources_cited,
                    "reasoning_trace": enhanced_result.reasoning_trace,
                    "quality_metrics": enhanced_result.quality_metrics,
                    "enhanced": True,
                    "specialists_used": [
                        result.specialist_type.value for result in enhanced_result.subagent_results
                    ],
                    "decomposition": {
                        "complexity": enhanced_result.decomposition_used.approach.complexity.value,
                        "strategy": enhanced_result.decomposition_used.approach.strategy.value,
                        "subagents": enhanced_result.decomposition_used.approach.estimated_subagents
                    },
                    "error": None
                }
            else:
                # Fallback simples
                result = self.enhanced_system.fallback_to_simple(query)
                result["processing_time"] = time.time() - start_time
                return result
                
        except Exception as e:
            logger.error(f"❌ Erro no processamento da query: {e}")
            
            # Tentar fallback
            try:
                fallback_result = self.enhanced_system.fallback_to_simple(query)
                fallback_result["processing_time"] = time.time() - start_time
                fallback_result["fallback_reason"] = f"Erro no enhanced: {str(e)}"
                return fallback_result
            except Exception as fallback_error:
                logger.error(f"❌ Erro no fallback: {fallback_error}")
                
                return {
                    "success": False,
                    "query": query,
                    "result": f"Erro: {str(e)}",
                    "agent_id": "error",
                    "status": "FAILED",
                    "processing_time": time.time() - start_time,
                    "enhanced": False,
                    "error": str(e)
                }


class EnhancedLeadResearcher:
    """Lead Researcher enhanced que substitui o atual"""
    
    def __init__(self, rag_system, openai_client: Optional[OpenAI] = None):
        self.enhanced_system = EnhancedRAGSystem(rag_system, openai_client)
        self.api_adapter = EnhancedAPIAdapter(self.enhanced_system)
        
        # Propriedades compatíveis com o sistema atual
        self.agent_id = "enhanced-lead-researcher"
        self.name = "Enhanced Lead Researcher"
        self.rag_system = rag_system
        
        logger.info("🎯 Enhanced Lead Researcher inicializado")
    
    async def run(self, context) -> "AgentResult":
        """
        Executa pesquisa usando sistema enhanced
        Mantém compatibilidade com a interface atual
        
        Args:
            context: AgentContext do sistema atual
            
        Returns:
            AgentResult: Resultado compatível com sistema atual
        """
        from datetime import datetime
        
        # Importar classes base com fallback robusto
        try:
            from ..agents.base import AgentResult, AgentState as AgentStatus
        except ImportError:
            try:
                from researcher.agents.base import AgentResult, AgentState as AgentStatus
            except ImportError:
                # Criar classes compatíveis se não conseguir importar
                class AgentStatus:
                    COMPLETED = "completed"
                    FAILED = "failed"
                
                class AgentResult:
                    def __init__(self, agent_id, status, output, error=None, metadata=None):
                        self.agent_id = agent_id
                        self.status = status
                        self.output = output
                        self.error = error
                        self.metadata = metadata or {}
                        self.start_time = datetime.utcnow()  # Campo obrigatório adicionado
                        self.end_time = datetime.utcnow()
                        self.reasoning_trace = []
        
        try:
            logger.info(f"Enhanced Lead Researcher iniciando processamento da query: {context.query[:100]}...")
            logger.reasoning_step("INIT", f"Processando query: {context.query}", 
                                observations="Query recebida pelo Enhanced Lead Researcher",
                                next_action="Executar sistema enhanced multi-agente")
            
            # Processar query usando enhanced system
            result = await self.api_adapter.process_research_query(
                query=context.query,
                objective=getattr(context, 'objective', None),
                use_enhanced=True
            )
            
            if result["success"]:
                status = AgentState.COMPLETED
                output = result["result"]
                error = None
                
                logger.reasoning_step("SUCCESS", "Query processada com sucesso",
                                    observations=f"Resultado obtido com {len(output)} caracteres",
                                    confidence_score=result.get("confidence_score"),
                                    sources_count=len(result.get("sources", [])))
            else:
                status = AgentStatus.FAILED
                output = None
                error = result.get("error", "Falha na pesquisa")
                
                logger.reasoning_step("FAILURE", "Falha no processamento da query",
                                    observations=f"Erro: {error}",
                                    next_action="Retornar resultado de erro")
            
            # Criar AgentResult compatível
            agent_result = AgentResult(
                agent_id=self.agent_id,
                status=status,
                output=output,
                error=error,
                start_time=datetime.utcnow(),  # Campo obrigatório
                metadata={
                    "confidence_score": result.get("confidence_score"),
                    "sources": result.get("sources", []),
                    "enhanced": result.get("enhanced", True),
                    "processing_time": result.get("processing_time"),
                    "quality_metrics": result.get("quality_metrics", {}),
                    "specialists_used": result.get("specialists_used", [])
                }
            )
            
            # Adicionar reasoning trace se disponível
            if "reasoning_trace" in result and result["reasoning_trace"]:
                # Converter lista para string se necessário
                reasoning_trace = result["reasoning_trace"]
                if isinstance(reasoning_trace, list):
                    agent_result.reasoning_trace = "\n".join(reasoning_trace)
                else:
                    agent_result.reasoning_trace = str(reasoning_trace)
            else:
                # Garantir que sempre há um reasoning_trace (string vazia se não houver)
                agent_result.reasoning_trace = "Reasoning trace não disponível"
            
            return agent_result
            
        except Exception as e:
            logger.error(f"Erro no Enhanced Lead Researcher: {e}", e, {"query": context.query})
            logger.reasoning_step("ERROR", "Erro crítico no Enhanced Lead Researcher",
                                observations=f"Exception: {str(e)}",
                                next_action="Retornar resultado de erro")
            
            # Retornar resultado de erro
            error_result = AgentResult(
                agent_id=self.agent_id,
                status=AgentState.FAILED,
                output=None,
                error=str(e),
                start_time=datetime.utcnow(),  # Campo obrigatório
                metadata={"enhanced": False, "fallback_attempted": True}
            )
            error_result.reasoning_trace = f"Erro durante execução: {str(e)}"
            return error_result
    
    async def plan(self, context) -> List[str]:
        """
        Cria plano de pesquisa usando decomposição enhanced
        Compatível com interface atual
        """
        try:
            decomposition = self.enhanced_system.decomposer.decompose(context.query)
            
            # Converter para formato de plano simples
            plan = []
            for task in decomposition.subagent_tasks:
                plan.append(f"{task.specialist_type.value}: {task.semantic_context}")
            
            return plan
            
        except Exception as e:
            logger.error(f"❌ Erro no planning enhanced: {e}")
            return [f"Pesquisar informações sobre: {context.query}"]


# =============================================================================
# FACTORY PARA CRIAÇÃO DO SISTEMA ENHANCED
# =============================================================================

def create_enhanced_lead_researcher(rag_system, openai_client: Optional[OpenAI] = None) -> EnhancedLeadResearcher:
    """
    Factory para criar Enhanced Lead Researcher
    
    Args:
        rag_system: Sistema RAG atual
        openai_client: Cliente OpenAI (opcional)
        
    Returns:
        EnhancedLeadResearcher: Lead researcher enhanced
    """
    logger.info("🏭 Criando Enhanced Lead Researcher...")
    
    try:
        enhanced_researcher = EnhancedLeadResearcher(rag_system, openai_client)
        logger.info("✅ Enhanced Lead Researcher criado com sucesso")
        return enhanced_researcher
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar Enhanced Lead Researcher: {e}")
        raise


def integrate_enhanced_system(current_state_manager) -> bool:
    """
    Integra sistema enhanced com o state manager atual
    
    Args:
        current_state_manager: APIStateManager atual
        
    Returns:
        bool: True se integração foi bem-sucedida
    """
    logger.info("🔗 Iniciando integração do sistema enhanced...")
    
    try:
        # Verificar se SimpleRAG está disponível
        if not current_state_manager.simple_rag:
            logger.error("❌ SimpleRAG não disponível para integração")
            return False
        
        # Criar Enhanced Lead Researcher
        enhanced_researcher = create_enhanced_lead_researcher(
            current_state_manager.simple_rag.rag
        )
        
        # Substituir Lead Researcher atual
        current_state_manager.lead_researcher = enhanced_researcher
        
        logger.info("✅ Sistema enhanced integrado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na integração enhanced: {e}")
        return False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'EnhancedRAGSystem',
    'EnhancedAPIAdapter', 
    'EnhancedLeadResearcher',
    'create_enhanced_lead_researcher',
    'integrate_enhanced_system'
]