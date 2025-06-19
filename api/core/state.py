#!/usr/bin/env python3
"""
🧠 Gerenciamento de Estado - API Multi-Agente

Sistema thread-safe para gerenciar o estado da aplicação
incluindo instâncias de agentes, métricas e recursos.
"""

import time
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from .config import config
from ..utils.errors import APIError, ServiceUnavailableError

logger = logging.getLogger(__name__)


class RequestMetrics:
    """Métricas de requisições"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        self.response_times = []
        self._lock = asyncio.Lock()
    
    async def record_request(self, response_time: float, success: bool = True):
        """Registra uma requisição"""
        async with self._lock:
            self.total_requests += 1
            self.response_times.append(response_time)
            
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            
            # Manter apenas as últimas 1000 requisições para cálculo da média
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            self.average_response_time = sum(self.response_times) / len(self.response_times)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas atuais"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / max(self.total_requests, 1)) * 100,
            "average_response_time": self.average_response_time
        }


class APIStateManager:
    """Gerenciador thread-safe do estado da API"""
    
    def __init__(self):
        self._start_time = time.time()
        self._is_ready = False
        self._is_initializing = False
        self._lead_researcher: Optional[Any] = None
        self._research_memory: Optional[Any] = None
        self._simple_rag: Optional[Any] = None
        self._metrics = RequestMetrics()
        self._lock = asyncio.Lock()
        self._components_initialized = {}
        
        logger.info("🏗️ APIStateManager inicializado")
    
    @property
    def start_time(self) -> float:
        return self._start_time
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    @property
    def is_initializing(self) -> bool:
        return self._is_initializing
    
    @property
    def lead_researcher(self) -> Optional[Any]:
        return self._lead_researcher
    
    @property
    def research_memory(self) -> Optional[Any]:
        return self._research_memory
    
    @property
    def simple_rag(self) -> Optional[Any]:
        return self._simple_rag
    
    @property
    def metrics(self) -> RequestMetrics:
        return self._metrics
    
    def get_uptime(self) -> float:
        """Retorna tempo de atividade em segundos"""
        return time.time() - self._start_time
    
    async def initialize(self):
        """Inicializa todos os componentes do sistema"""
        async with self._lock:
            if self._is_ready or self._is_initializing:
                return
            
            self._is_initializing = True
            logger.info("🚀 Inicializando sistema multi-agente...")
        
        try:
            # Validar configuração
            validation = config.validate_all()
            if not validation["valid"]:
                raise APIError(f"Configuração inválida: {validation.get('error', 'Erro desconhecido')}")
            
            # Inicializar componentes em ordem de dependência
            await self._initialize_memory()
            await self._initialize_simple_rag()
            await self._initialize_lead_researcher()  # Depois do SimpleRAG
            
            async with self._lock:
                self._is_ready = True
                self._is_initializing = False
            
            logger.info("✅ Sistema multi-agente inicializado com sucesso")
            
        except Exception as e:
            async with self._lock:
                self._is_initializing = False
            logger.error(f"❌ Erro na inicialização: {e}")
            raise APIError(f"Falha na inicialização do sistema: {str(e)}")
    
    async def _initialize_memory(self):
        """Inicializa sistema de memória"""
        try:
            # Importação dinâmica para evitar problemas de path
            import sys
            import os
            
            # Garantir que estamos no diretório correto e adicionar paths
            original_cwd = os.getcwd()
            workspace_root = config.paths.workspace_root
            multiagent_src = workspace_root / "multi-agent-researcher" / "src"
            
            # Adicionar paths necessários
            if str(multiagent_src) not in sys.path:
                sys.path.insert(0, str(multiagent_src))
            if str(workspace_root) not in sys.path:
                sys.path.insert(0, str(workspace_root))
            
            # Mudar para o diretório correto
            os.chdir(workspace_root)
            
            from researcher.memory.base import InMemoryStorage, ResearchMemory
            
            memory_storage = InMemoryStorage()
            self._research_memory = ResearchMemory(memory_storage)
            self._components_initialized["memory"] = True
            
            # Voltar ao diretório original
            os.chdir(original_cwd)
            
            logger.info("✅ Sistema de memória inicializado")
            
        except ImportError as e:
            # Voltar ao diretório original em caso de erro
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            logger.error(f"❌ Erro ao importar módulos de memória: {e}")
            raise ServiceUnavailableError("Sistema de memória")
        except Exception as e:
            logger.error(f"❌ Erro na inicialização da memória: {e}")
            raise
    
    async def _initialize_lead_researcher(self):
        """Inicializa o lead researcher"""
        try:
            import sys
            import os
            
            # Garantir que estamos no diretório correto
            original_cwd = os.getcwd()
            workspace_root = config.paths.workspace_root
            multiagent_src = workspace_root / "multi-agent-researcher" / "src"
            
            # Adicionar paths necessários
            if str(multiagent_src) not in sys.path:
                sys.path.insert(0, str(multiagent_src))
            if str(workspace_root) not in sys.path:
                sys.path.insert(0, str(workspace_root))
            
            # Mudar para o diretório correto
            os.chdir(workspace_root)
            
            from researcher.agents.openai_lead_researcher import OpenAILeadResearcher, OpenAILeadConfig
            
            lead_config = OpenAILeadConfig.from_env()
            
            # Criar Lead Researcher
            self._lead_researcher = OpenAILeadResearcher(
                config=lead_config,
                agent_id=str(uuid.uuid4()),
                name="API-Lead-Researcher"
            )
            
            # Injetar o ProductionConversationalRAG (sistema completo) no Lead Researcher para dados multimodais
            if self._simple_rag:
                # Usar o sistema RAG interno do SimpleRAG que tem capacidades multimodais
                if hasattr(self._simple_rag, 'rag'):
                    production_rag = self._simple_rag.rag  # ProductionConversationalRAG
                    self._lead_researcher.rag_system = production_rag
                    logger.info("✅ ProductionConversationalRAG (multimodal) injetado no Lead Researcher")
                else:
                    # Fallback para SimpleRAG se não tiver acesso ao sistema interno
                    self._lead_researcher.rag_system = self._simple_rag
                    logger.warning("⚠️ Usando SimpleRAG (sem multimodal) como fallback")
                
                # Método para injetar RAG multimodal nos subagentes
                def inject_rag_to_subagent(subagent):
                    if hasattr(subagent, 'rag_tool'):
                        if hasattr(self._simple_rag, 'rag'):
                            # Injetar sistema completo multimodal
                            subagent.rag_tool.set_rag_system(self._simple_rag.rag)
                            logger.debug(f"RAG multimodal injetado no subagente {subagent.name}")
                        else:
                            # Fallback
                            subagent.rag_tool.set_rag_system(self._simple_rag)
                            logger.debug(f"RAG simples injetado no subagente {subagent.name}")
                
                self._lead_researcher.inject_rag_to_subagent = inject_rag_to_subagent
                
            else:
                logger.warning("⚠️ SimpleRAG não disponível para injeção no Lead Researcher")
            
            self._components_initialized["lead_researcher"] = True
            
            # Voltar ao diretório original
            os.chdir(original_cwd)
            
            logger.info("✅ Lead Researcher inicializado")
            
        except ImportError as e:
            # Voltar ao diretório original em caso de erro
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            logger.error(f"❌ Erro ao importar módulos do lead researcher: {e}")
            raise ServiceUnavailableError("Lead Researcher")
        except Exception as e:
            logger.error(f"❌ Erro na inicialização do lead researcher: {e}")
            raise
    
    async def _initialize_simple_rag(self):
        """Inicializa o sistema RAG simples"""
        try:
            import sys
            import os
            
            # Garantir que estamos no diretório correto
            original_cwd = os.getcwd()
            os.chdir(config.paths.workspace_root)
            
            sys.path.append(str(config.paths.workspace_root))
            
            from src.core.search import SimpleRAG
            
            self._simple_rag = SimpleRAG()
            self._components_initialized["simple_rag"] = True
            
            # Voltar ao diretório original
            os.chdir(original_cwd)
            
            logger.info("✅ SimpleRAG inicializado")
            
        except ImportError as e:
            logger.error(f"❌ Erro ao importar SimpleRAG: {e}")
            raise ServiceUnavailableError("Sistema RAG")
        except Exception as e:
            logger.error(f"❌ Erro na inicialização do SimpleRAG: {e}")
            raise
    
    async def shutdown(self):
        """Finaliza todos os recursos"""
        async with self._lock:
            if not self._is_ready:
                return
            
            logger.info("🛑 Finalizando sistema...")
            
            # Cleanup de recursos se necessário
            self._lead_researcher = None
            self._research_memory = None
            self._simple_rag = None
            self._is_ready = False
            self._components_initialized.clear()
            
            logger.info("✅ Sistema finalizado")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do sistema"""
        return {
            "status": "healthy" if self._is_ready else ("initializing" if self._is_initializing else "unhealthy"),
            "uptime_seconds": self.get_uptime(),
            "components": self._components_initialized.copy(),
            "metrics": self._metrics.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do sistema"""
        return {
            **self.get_health_status(),
            "configuration": config.get_environment_summary(),
            "memory_initialized": self._research_memory is not None,
            "lead_researcher_initialized": self._lead_researcher is not None,
            "simple_rag_initialized": self._simple_rag is not None
        }


# Singleton instance
_state_manager: Optional[APIStateManager] = None


def get_state_manager() -> APIStateManager:
    """Dependency injection para o state manager"""
    global _state_manager
    if _state_manager is None:
        _state_manager = APIStateManager()
    return _state_manager


@asynccontextmanager
async def lifespan_manager(app):
    """Context manager para lifecycle da aplicação"""
    state_manager = get_state_manager()
    
    try:
        # Startup
        logger.info("🚀 Iniciando API Multi-Agente...")
        await state_manager.initialize()
        logger.info("✅ API pronta para receber requisições")
        
        yield
        
    finally:
        # Shutdown
        logger.info("🛑 Finalizando API Multi-Agente...")
        await state_manager.shutdown()
        logger.info("✅ API finalizada")
