#!/usr/bin/env python3
"""
🔍 Multi-Agent Logger - Sistema de Logging Centralizado

Logger especializado para todas as etapas do sistema multi-agente:
- Reasoning trace completo
- Planejamento e decomposição
- Execução de subagentes
- Síntese e coordenação
- Métricas e performance

Segue as boas práticas do sistema com configuração centralizada.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../../"))
from src.core.config import SystemConfig

class MultiAgentLogger:
    """Logger centralizado para o sistema multi-agente"""
    
    def __init__(self, agent_name: str = "MultiAgent"):
        self.config = SystemConfig()
        self.agent_name = agent_name
        self._logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura o logger seguindo as boas práticas do sistema"""
        
        # Só configura se logging multi-agente estiver habilitado
        if not self.config.production.enable_multiagent_logs:
            self._logger = logging.getLogger("disabled_multiagent")
            self._logger.disabled = True
            return
        
        # Nome único do logger
        logger_name = f"multiagent.{self.agent_name}"
        self._logger = logging.getLogger(logger_name)
        
        # Evitar duplicação de handlers
        if self._logger.handlers:
            return
        
        # Level baseado na configuração
        log_level = getattr(logging, self.config.production.multiagent_log_level.upper(), logging.INFO)
        self._logger.setLevel(log_level)
        
        # Formato estruturado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # Handler para arquivo específico do multi-agente
        # Garantir path absoluto
        if os.path.isabs(self.config.rag.logs_dir):
            log_dir = Path(self.config.rag.logs_dir)
        else:
            # Path relativo ao diretório raiz do projeto
            project_root = Path(__file__).parent.parent.parent.parent.parent
            log_dir = project_root / self.config.rag.logs_dir
            
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / self.config.production.multiagent_log_file
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.production.max_log_file_size * 1024 * 1024,  # MB para bytes
            backupCount=self.config.production.log_rotation_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # Força flush imediato para garantir que logs sejam escritos
        file_handler.flush = lambda: file_handler.stream.flush() if hasattr(file_handler, 'stream') else None
        
        # Handler para console (apenas se não estiver em produção)
        if not self.config.production.production_mode:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(log_level)
            self._logger.addHandler(console_handler)
        
        self._logger.addHandler(file_handler)
        
        # Log inicial
        self._logger.info(f"🤖 Multi-Agent Logger iniciado para '{self.agent_name}' - Level: {self.config.production.multiagent_log_level}")
        self._force_flush()
    
    def _force_flush(self):
        """Força flush de todos os handlers"""
        for handler in self._logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
    
    def reasoning_step(self, step_type: str, content: str, observations: str = None, next_action: str = None, **kwargs):
        """Log específico para steps de reasoning"""
        if not self.config.production.enable_reasoning_trace_logs:
            return
            
        step_info = {
            "step_type": step_type.upper(),
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if observations:
            step_info["observations"] = observations
        if next_action:
            step_info["next_action"] = next_action
            
        # Adicionar dados extras
        step_info.update(kwargs)
        
        self._logger.info(f"🧠 REASONING [{step_type.upper()}] {content}", extra={"reasoning_step": step_info})
        self._force_flush()
    
    def planning(self, message: str, plan_details: Dict[str, Any] = None):
        """Log para fase de planejamento"""
        extra_data = {"phase": "planning"}
        if plan_details:
            extra_data["plan_details"] = plan_details
            
        self._logger.info(f"📋 PLANNING: {message}", extra=extra_data)
        self._force_flush()
    
    def subagent_execution(self, subagent_id: str, action: str, result: str = None, duration: float = None):
        """Log para execução de subagentes"""
        if not self.config.production.enable_subagent_logs:
            return
            
        extra_data = {
            "phase": "subagent_execution",
            "subagent_id": subagent_id,
            "action": action
        }
        
        if result:
            extra_data["result"] = result[:200] + "..." if len(result) > 200 else result
        if duration:
            extra_data["duration_seconds"] = duration
            
        self._logger.info(f"🎭 SUBAGENT [{subagent_id}] {action}", extra=extra_data)
        self._force_flush()
    
    def synthesis(self, message: str, synthesis_details: Dict[str, Any] = None):
        """Log para fase de síntese"""
        extra_data = {"phase": "synthesis"}
        if synthesis_details:
            extra_data["synthesis_details"] = synthesis_details
            
        self._logger.info(f"🧬 SYNTHESIS: {message}", extra=extra_data)
    
    def coordination(self, message: str, coordination_data: Dict[str, Any] = None):
        """Log para coordenação entre agentes"""
        extra_data = {"phase": "coordination"}
        if coordination_data:
            extra_data["coordination_data"] = coordination_data
            
        self._logger.info(f"🎯 COORDINATION: {message}", extra=extra_data)
    
    def performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """Log para métricas de performance"""
        extra_data = {
            "phase": "performance",
            "operation": operation,
            "duration_seconds": duration
        }
        
        if details:
            extra_data["details"] = details
            
        # Log apenas se exceder threshold ou se for solicitado
        threshold = getattr(self.config.production, 'performance_log_threshold', 5.0)
        
        if duration > threshold:
            self._logger.warning(f"⚡ PERFORMANCE: {operation} took {duration:.2f}s (above threshold)", extra=extra_data)
        else:
            self._logger.debug(f"⚡ PERFORMANCE: {operation} completed in {duration:.2f}s", extra=extra_data)
    
    def error(self, message: str, exception: Exception = None, context: Dict[str, Any] = None):
        """Log para erros do sistema multi-agente"""
        extra_data = {"phase": "error"}
        if context:
            extra_data["context"] = context
            
        if exception:
            self._logger.error(f"❌ ERROR: {message}", exc_info=exception, extra=extra_data)
        else:
            self._logger.error(f"❌ ERROR: {message}", extra=extra_data)
    
    def debug(self, message: str, debug_data: Dict[str, Any] = None):
        """Log para debug detalhado"""
        extra_data = {"phase": "debug"}
        if debug_data:
            extra_data["debug_data"] = debug_data
            
        self._logger.debug(f"🔧 DEBUG: {message}", extra=extra_data)
    
    def info(self, message: str, extra_data: Dict[str, Any] = None):
        """Log info genérico"""
        if extra_data:
            self._logger.info(message, extra=extra_data)
        else:
            self._logger.info(message)
    
    def warning(self, message: str, extra_data: Dict[str, Any] = None):
        """Log warning genérico"""
        if extra_data:
            self._logger.warning(message, extra=extra_data)
        else:
            self._logger.warning(message)

# Factory function para facilitar o uso
def get_multiagent_logger(agent_name: str = "MultiAgent") -> MultiAgentLogger:
    """Factory function para obter um logger multi-agente"""
    return MultiAgentLogger(agent_name)

# Instância global para uso simples
default_logger = get_multiagent_logger()
