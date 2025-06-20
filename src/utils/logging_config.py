"""
Configuração de logging para produção baseada em constants.py
"""

import logging
import logging.handlers
import os
import sys
from typing import Dict, Any
from datetime import datetime

# Importar configuração centralizada
from ..core.config import SystemConfig
from ..core.constants import LOGGING_CONFIG, DEV_CONFIG


def setup_production_logging() -> Dict[str, Any]:
    """
    Configura logging para produção baseado nas configurações em constants.py
    
    Returns:
        Dict com informações da configuração aplicada
    """
    config_info = {
        "configured": False,
        "log_level": LOGGING_CONFIG['DEFAULT_LEVEL'],
        "async_enabled": LOGGING_CONFIG.get('ASYNC_LOGGING', False),
        "structured_enabled": LOGGING_CONFIG.get('ENABLE_STRUCTURED_LOGGING', False)
    }
    
    try:
        # Configurar nível de log
        log_level = getattr(logging, LOGGING_CONFIG['DEFAULT_LEVEL'].upper())
        
        # Formato estruturado se habilitado
        if LOGGING_CONFIG.get('ENABLE_STRUCTURED_LOGGING', False):
            log_format = '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        else:
            log_format = LOGGING_CONFIG['LOG_FORMAT']
        
        # Configurar logger raiz
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configurar rotação de arquivos se não em debug
        if not DEV_CONFIG.get('DEBUG_MODE', False):
            config = SystemConfig()
            log_dir = config.rag.logs_dir
            os.makedirs(log_dir, exist_ok=True)
            
            # Handler com rotação
            handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(log_dir, 'rag_production.log'),
                maxBytes=LOGGING_CONFIG['MAX_LOG_FILE_SIZE'] * 1024 * 1024,  # MB para bytes
                backupCount=LOGGING_CONFIG['LOG_ROTATION_COUNT'],
                encoding='utf-8'
            )
            
            # Formatter
            formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            
            # Adicionar handler ao logger raiz
            logging.getLogger().addHandler(handler)
        
        # Configurar loggers específicos
        configure_module_loggers()
        
        config_info["configured"] = True
        logging.info("✅ Logging de produção configurado com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao configurar logging: {e}")
        config_info["error"] = str(e)
    
    return config_info


def configure_module_loggers():
    """Configura loggers específicos para diferentes módulos"""
    
    # Logger para FastAPI (menos verboso)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Logger para httpx/requests (menos verboso)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Logger para OpenAI (menos verboso)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # Loggers do sistema RAG (mais detalhados)
    logging.getLogger("researcher").setLevel(logging.INFO)
    logging.getLogger("search").setLevel(logging.INFO)
    logging.getLogger("multiagent").setLevel(logging.INFO)


def get_structured_logger(name: str) -> logging.Logger:
    """
    Retorna logger configurado para logging estruturado
    
    Args:
        name: Nome do logger (geralmente __name__)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Adicionar contexto estruturado se habilitado
    if LOGGING_CONFIG.get('LOG_CORRELATION_ID', False):
        # Pode ser estendido para adicionar correlation IDs
        pass
    
    return logger


def log_performance_metric(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """
    Log métricas de performance se estiver acima do threshold
    
    Args:
        logger: Logger a usar
        operation: Nome da operação
        duration: Duração em segundos
        **kwargs: Dados adicionais
    """
    threshold = LOGGING_CONFIG.get('PERFORMANCE_LOG_THRESHOLD', 5.0)
    
    if duration > threshold:
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.warning(
            f"🐌 PERFORMANCE: {operation} took {duration:.2f}s (threshold: {threshold}s) | {extra_info}"
        )
    elif DEV_CONFIG.get('ENABLE_PERFORMANCE_METRICS', False):
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.info(
            f"⚡ PERFORMANCE: {operation} completed in {duration:.2f}s | {extra_info}"
        )


def log_error_with_context(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """
    Log erro com contexto adicional
    
    Args:
        logger: Logger a usar
        error: Exceção ocorrida
        context: Contexto adicional
    """
    context = context or {}
    context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
    
    logger.error(
        f"❌ ERROR: {type(error).__name__}: {str(error)} | {context_str}",
        exc_info=True
    )


class ProductionLoggerAdapter(logging.LoggerAdapter):
    """Adapter para adicionar contexto consistente aos logs"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any] = None):
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        # Adicionar timestamp e contexto de produção
        if DEV_CONFIG.get('PRODUCTION_MODE', False):
            self.extra['env'] = 'production'
        
        return msg, kwargs


# Configuração automática se importado
if DEV_CONFIG.get('PRODUCTION_MODE', False):
    setup_production_logging()
