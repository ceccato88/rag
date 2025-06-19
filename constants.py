"""
Constantes e valores padrão para o sistema RAG Multi-Agente Refatorado v2.0.0

Este arquivo centraliza todas as constantes utilizadas no sistema refatorado,
fornecendo valores padrão otimizados para as APIs que usam modelos nativos.
"""

# =============================================================================
# MODELOS DE IA - VALORES PADRÃO
# =============================================================================

DEFAULT_MODELS = {
    'LLM': 'gpt-4.1-mini',
    'EMBEDDING': 'voyage-multimodal-3', 
    'MULTIAGENT': 'gpt-4.1-mini',
    'MULTIMODAL': 'voyage-multimodal-3'
}

# =============================================================================
# LIMITES DE TOKENS
# =============================================================================

TOKEN_LIMITS = {
    'MAX_CANDIDATES': 5,
    'MAX_TOKENS_RERANK': 512,
    'MAX_TOKENS_ANSWER': 2048,
    'MAX_TOKENS_QUERY_TRANSFORM': 150,
    'MAX_TOKENS_DECOMPOSITION': 1000,
    'VOYAGE_EMBEDDING_DIM': 1024,
    'MAX_TOKENS_PER_INPUT': 32000
}

# =============================================================================
# CONFIGURAÇÕES DE CACHE
# =============================================================================

CACHE_CONFIG = {
    'EMBEDDING_CACHE_SIZE': 1000,     
    'EMBEDDING_CACHE_TTL': 3600,     
    'RESPONSE_CACHE_SIZE': 200,      
    'RESPONSE_CACHE_TTL': 1800,       
    'GLOBAL_CACHE_SIZE': 2000,       
    'GLOBAL_CACHE_TTL': 3600,       
    'L1_CACHE_MAX_SIZE': 1000,
    'L2_CACHE_MAX_SIZE': 5000
}

# =============================================================================
# TIMEOUTS E RETRIES
# =============================================================================

TIMEOUT_CONFIG = {
    'SUBAGENT_TIMEOUT': 300.0,       
    'DOWNLOAD_TIMEOUT': 30,          
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 1.0,             
    'CIRCUIT_BREAKER_THRESHOLD': 5,
    'CIRCUIT_BREAKER_TIMEOUT': 60,   
    'EXPONENTIAL_BACKOFF_MAX': 60.0,  
    'LINEAR_BACKOFF_MAX': 30.0,       
    'IMMEDIATE_RETRY_DELAY': 1.0      
}

# =============================================================================
# CONFIGURAÇÕES DE PROCESSAMENTO
# =============================================================================

PROCESSING_CONFIG = {
    'BATCH_SIZE': 100,
    'DOWNLOAD_CHUNK_SIZE': 8192,  
    'PIXMAP_SCALE': 2,
    'TOKENS_PER_PIXEL': 1 / 560,  
    'TOKEN_CHARS_RATIO': 4,
    'PROCESSING_CONCURRENCY': 5,
    'CLEANUP_MAX_AGE': 24        
}

# =============================================================================
# SISTEMA MULTI-AGENTE
# =============================================================================

MULTIAGENT_CONFIG = {
    'MAX_SUBAGENTS': 3,
    'PARALLEL_EXECUTION': True,
    'USE_LLM_DECOMPOSITION': True,
    'CONCURRENCY_LIMIT': 3,
    'SIMILARITY_THRESHOLD': 0.7 
}

# =============================================================================
# CONFIGURAÇÕES DE MEMÓRIA
# =============================================================================

MEMORY_CONFIG = {
    'MEMORY_SHARDS': 4,
    'SHARD_STRATEGY': 'agent_hash'
}

# =============================================================================
# CONFIGURAÇÕES PADRÃO DE SISTEMA
# =============================================================================

SYSTEM_DEFAULTS = {
    'COLLECTION_NAME': 'pdf_documents',
    'IMAGE_DIR': 'pdf_images',
    'DEFAULT_PDF_URL': 'https://arxiv.org/pdf/2501.13956'
}

# =============================================================================
# LIMITES DE SISTEMA
# =============================================================================

SYSTEM_LIMITS = {
    'MAX_CHAT_HISTORY': 20,
    'MAX_REASONING_STEPS': 50,
    'MAX_SUBAGENTS_ABSOLUTE': 10,
    'MIN_SIMILARITY_THRESHOLD': 0.7,
    'MAX_FILE_SIZE_MB': 100,
    'MAX_PAGES_PER_PDF': 1000
}

# =============================================================================
# CONFIGURAÇÕES DE FALLBACK
# =============================================================================

FALLBACK_CONFIG = {
    'USE_MOCK_DATA': False,                         # Nunca usar dados mock em produção
    'MOCK_RESULTS_COUNT': 0,                        # Zero para produção
    'DEFAULT_ERROR_MESSAGE': "Desculpe, não consegui encontrar informações sobre isso.",
    'FALLBACK_TO_SIMPLE_SEARCH': True,              # Fallback importante para produção
    'ENABLE_GRACEFUL_DEGRADATION': True,            # Degradação graciosa essencial
    'MAX_FALLBACK_ATTEMPTS': 3,                     # Máximo 3 tentativas de fallback
    'CIRCUIT_BREAKER_ENABLED': True,                # Circuit breaker para estabilidade
    'HEALTH_CHECK_ON_FALLBACK': True,               # Verificar saúde do sistema
    'LOG_FALLBACK_EVENTS': True,                    # Log para monitoramento
    'FALLBACK_TIMEOUT_MULTIPLIER': 0.5              # Timeouts reduzidos no fallback
}

# =============================================================================
# TIPOS DE ESPECIALISTAS
# =============================================================================

SPECIALIST_TYPES = {
    'CONCEPT': 'ConceptExtractionSubagent',
    'COMPARATIVE': 'ComparativeAnalysisSubagent', 
    'TECHNICAL': 'TechnicalDetailSubagent',
    'EXAMPLES': 'ExampleFinderSubagent'
}

# =============================================================================
# PADRÕES DE QUERY PARA ESPECIALISTAS
# =============================================================================

SPECIALIST_PATTERNS = {
    'CONCEPT': [
        'what is', 'define', 'definition', 'concept', 'meaning',
        'o que é', 'definição', 'conceito', 'significado'
    ],
    'COMPARATIVE': [
        'compare', 'versus', 'vs', 'difference', 'similar',
        'comparar', 'diferença', 'similar', 'parecido'
    ],
    'TECHNICAL': [
        'how to', 'implement', 'technical', 'architecture', 'algorithm',
        'como implementar', 'técnico', 'arquitetura', 'algoritmo'
    ],
    'EXAMPLES': [
        'example', 'case study', 'use case', 'application',
        'exemplo', 'caso de uso', 'aplicação', 'demonstração'
    ]
}

# =============================================================================
# CONFIGURAÇÕES DE LOGGING
# =============================================================================

LOGGING_CONFIG = {
    'DEFAULT_LEVEL': 'INFO',                        # INFO para produção (não DEBUG)
    'MAX_LOG_FILE_SIZE': 50,                        # Aumentado para 50MB
    'LOG_ROTATION_COUNT': 10,                       # Mais arquivos para histórico
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'ENABLE_STRUCTURED_LOGGING': True,              # Logs estruturados para análise
    'LOG_CORRELATION_ID': True,                     # IDs para rastreamento
    'COMPRESS_ROTATED_LOGS': True,                  # Compressão para economizar espaço
    'ASYNC_LOGGING': True,                          # Logging assíncrono para performance
    'ERROR_NOTIFICATION_THRESHOLD': 10,             # Notificar após 10 erros/minuto
    'PERFORMANCE_LOG_THRESHOLD': 5.0                # Log operações > 5 segundos
}

# =============================================================================
# CONFIGURAÇÕES DE VALIDAÇÃO
# =============================================================================

VALIDATION_CONFIG = {
    'MIN_QUERY_LENGTH': 3,
    'MAX_QUERY_LENGTH': 1000,
    'REQUIRED_ENV_VARS': [
        'OPENAI_API_KEY',
        'VOYAGE_API_KEY', 
        'ASTRA_DB_API_ENDPOINT',
        'ASTRA_DB_APPLICATION_TOKEN'
    ]
}

# =============================================================================
# MENSAGENS DE SISTEMA
# =============================================================================

SYSTEM_MESSAGES = {
    'STARTUP_SUCCESS': "✅ Sistema RAG Multi-Agente inicializado com sucesso",
    'STARTUP_ERROR': "❌ Erro na inicialização do sistema RAG Multi-Agente",
    'QUERY_PROCESSING': "🔍 Processando query com sistema multi-agente...",
    'QUERY_SUCCESS': "✅ Query processada com sucesso",
    'QUERY_ERROR': "❌ Erro no processamento da query",
    'SUBAGENT_TIMEOUT': "⏰ Timeout na execução de subagente",
    'CACHE_HIT': "⚡ Cache hit - resposta rápida",
    'CACHE_MISS': "💾 Cache miss - processando nova query"
}

# =============================================================================
# CONFIGURAÇÕES DE PRODUÇÃO
# =============================================================================

DEV_CONFIG = {
    'DEBUG_MODE': False,                    # Desabilitado para produção
    'VERBOSE_LOGGING': False,               # Logs concisos para produção
    'ENABLE_PERFORMANCE_METRICS': True,     # Monitoramento essencial
    'SAVE_INTERMEDIATE_RESULTS': False,     # Economiza espaço em disco
    'MOCK_API_CALLS': False,                # APIs reais apenas
    'PRODUCTION_MODE': True,                # Flag explícita de produção
    'LOG_SENSITIVE_DATA': False,            # Segurança: não logar dados sensíveis
    'ENABLE_PROFILING': False,              # Profiling desabilitado por performance
    'CACHE_WARMING': True,                  # Pre-carrega caches importantes
    'HEALTH_CHECK_INTERVAL': 60,            # Health checks a cada minuto
    'MEMORY_OPTIMIZATION': True,            # Otimizações de memória ativas
    'ASYNC_CLEANUP': True                   # Limpeza assíncrona de recursos
}

# =============================================================================
# CONFIGURAÇÕES ESPECÍFICAS DE PRODUÇÃO
# =============================================================================

PRODUCTION_CONFIG = {
    'ENABLE_RATE_LIMITING': True,                   # Rate limiting para proteger APIs
    'MAX_REQUESTS_PER_MINUTE': 100,                 # Limite de requests por minuto
    'MAX_CONCURRENT_REQUESTS': 20,                  # Requests simultâneas
    'ENABLE_REQUEST_VALIDATION': True,              # Validação rigorosa de requests
    'SECURITY_HEADERS_ENABLED': True,               # Headers de segurança
    'CORS_STRICT_MODE': True,                       # CORS restritivo
    'API_KEY_ROTATION_DAYS': 30,                    # Rotação de chaves API
    'MONITORING_ENABLED': True,                     # Monitoramento ativo
    'ALERTING_ENABLED': True,                       # Alertas para problemas
    'BACKUP_INTERVAL_HOURS': 6,                     # Backup a cada 6 horas
    'CLEANUP_TEMP_FILES': True,                     # Limpeza automática
    'RESOURCE_LIMITS_ENABLED': True,                # Limites de recursos
    'GRACEFUL_SHUTDOWN_TIMEOUT': 30,                # Shutdown gracioso em 30s
    'PRELOAD_CRITICAL_DATA': True,                  # Pre-carrega dados críticos
    'CONNECTION_POOLING': True,                     # Pool de conexões
    'DATABASE_TIMEOUT': 10,                         # Timeout de DB
    'REDIS_TIMEOUT': 5,                            # Timeout de cache
    'EXTERNAL_API_TIMEOUT': 15                      # Timeout APIs externas
}

# =============================================================================
# CONFIGURAÇÕES DAS APIs REFATORADAS v2.0.0
# =============================================================================

API_REFACTORED_CONFIG = {
    # API Multi-Agente
    'MULTIAGENT_API_PORT': 8000,
    'MULTIAGENT_API_WORKERS': 4,
    'MULTIAGENT_API_TIMEOUT': 300,
    'MULTIAGENT_MEMORY_LIMIT': '3GB',
    'MULTIAGENT_CPU_LIMIT': '3.0',
    
    # API RAG Simples  
    'SIMPLE_API_PORT': 8001,
    'SIMPLE_API_WORKERS': 2,
    'SIMPLE_API_TIMEOUT': 60,
    'SIMPLE_MEMORY_LIMIT': '1.5GB',
    'SIMPLE_CPU_LIMIT': '1.5',
    
    # Configurações comuns
    'HEALTH_CHECK_INTERVAL': 30,
    'HEALTH_CHECK_TIMEOUT': 15,
    'STARTUP_TIMEOUT': 60,
    'FACTORY_PATTERN_ENABLED': True,
    'NATIVE_MODELS_ONLY': True,
    'RESPONSE_COMPRESSION': True,
    'REQUEST_ID_TRACKING': True
}

# =============================================================================
# MODELOS NATIVOS SUPORTADOS
# =============================================================================

NATIVE_MODELS_CONFIG = {
    # Multi-Agent Researcher
    'AGENT_RESULT': 'researcher.agents.base.AgentResult',
    'AGENT_CONTEXT': 'researcher.agents.base.AgentContext', 
    'AGENT_STATE': 'researcher.agents.base.AgentState',
    'OPENAI_LEAD_RESEARCHER': 'researcher.agents.openai_lead_researcher.OpenAILeadResearcher',
    
    # SimpleRAG
    'SIMPLE_RAG': 'search.SimpleRAG',
    'SYSTEM_CONFIG': 'config.SystemConfig',
    
    # Factory Patterns
    'RESPONSE_FACTORY': 'ResponseFactory',
    'SIMPLE_RESPONSE_FACTORY': 'SimpleResponseFactory'
}

# =============================================================================
# ENDPOINTS DAS APIs REFATORADAS
# =============================================================================

API_ENDPOINTS = {
    # API Multi-Agente (Port 8000)
    'MULTIAGENT': {
        'BASE_URL': 'http://localhost:8000',
        'HEALTH': '/health',
        'RESEARCH': '/research',
        'INDEX': '/index', 
        'DOCUMENTS': '/documents/{collection_name}',
        'STATS': '/stats',
        'DOCS': '/docs'
    },
    
    # API RAG Simples (Port 8001)
    'SIMPLE': {
        'BASE_URL': 'http://localhost:8001',
        'HEALTH': '/health',
        'SEARCH': '/search',
        'DOCUMENTS': '/documents/{collection_name}',
        'CONFIG': '/config',
        'STATS': '/stats',
        'DOCS': '/docs'
    }
}

# =============================================================================
# DOCKER CONFIGURAÇÕES
# =============================================================================

DOCKER_CONFIG = {
    # Containers
    'MULTIAGENT_CONTAINER': 'rag-api-multiagent',
    'SIMPLE_CONTAINER': 'rag-api-simple',
    'REDIS_CONTAINER': 'rag-redis',
    'NGINX_CONTAINER': 'rag-nginx',
    'PROMETHEUS_CONTAINER': 'rag-prometheus',
    'GRAFANA_CONTAINER': 'rag-grafana',
    
    # Network
    'NETWORK_NAME': 'rag-network',
    'SUBNET': '172.20.0.0/16',
    
    # Volumes
    'REDIS_VOLUME': 'redis_data',
    'PROMETHEUS_VOLUME': 'prometheus_data',
    'GRAFANA_VOLUME': 'grafana_data',
    
    # Health Checks
    'HEALTH_INTERVAL': '30s',
    'HEALTH_TIMEOUT': '15s',
    'HEALTH_RETRIES': 3,
    'HEALTH_START_PERIOD': '60s'
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_env_or_default(env_key: str, config_dict: dict, config_key: str):
    """
    Obtém valor do ambiente ou retorna valor padrão da configuração.
    
    Args:
        env_key: Nome da variável de ambiente
        config_dict: Dicionário de configuração
        config_key: Chave no dicionário de configuração
        
    Returns:
        Valor da variável de ambiente ou valor padrão
    """
    import os
    return os.getenv(env_key, config_dict.get(config_key))

def get_all_defaults() -> dict:
    """
    Retorna todas as configurações padrão em um único dicionário.
    
    Returns:
        Dict com todas as configurações padrão
    """
    return {
        **DEFAULT_MODELS,
        **TOKEN_LIMITS,
        **CACHE_CONFIG,
        **TIMEOUT_CONFIG,
        **PROCESSING_CONFIG,
        **MULTIAGENT_CONFIG,
        **MEMORY_CONFIG,
        **SYSTEM_DEFAULTS,
        **SYSTEM_LIMITS,
        **FALLBACK_CONFIG,
        **LOGGING_CONFIG,
        **PRODUCTION_CONFIG,
        **DEV_CONFIG
    }

def get_production_config() -> dict:
    """
    Retorna configurações otimizadas especificamente para produção.
    
    Returns:
        Dict com configurações de produção
    """
    return {
        **PRODUCTION_CONFIG,
        **{k: v for k, v in LOGGING_CONFIG.items() if k != 'DEFAULT_LEVEL'},
        **{k: v for k, v in FALLBACK_CONFIG.items() if v != False},
        'ENVIRONMENT': 'production',
        'OPTIMIZED_FOR_PERFORMANCE': True,
        'SECURITY_ENHANCED': True
    }

def validate_production_config() -> list:
    """
    Valida se todas as configurações críticas para produção estão definidas.
    
    Returns:
        Lista de warnings/erros de configuração
    """
    warnings = []
    
    # Verificar se modo debug está desabilitado
    if DEV_CONFIG.get('DEBUG_MODE', False):
        warnings.append("❌ DEBUG_MODE deve ser False em produção")
    
    # Verificar se logging verboso está desabilitado
    if DEV_CONFIG.get('VERBOSE_LOGGING', False):
        warnings.append("⚠️ VERBOSE_LOGGING deve ser False em produção")
    
    # Verificar se mock data está desabilitado
    if FALLBACK_CONFIG.get('USE_MOCK_DATA', False):
        warnings.append("❌ USE_MOCK_DATA deve ser False em produção")
    
    # Verificar timeouts apropriados
    if TIMEOUT_CONFIG.get('SUBAGENT_TIMEOUT', 0) < 180:
        warnings.append("⚠️ SUBAGENT_TIMEOUT pode ser muito baixo para produção")
    
    # Verificar cache adequado
    if CACHE_CONFIG.get('GLOBAL_CACHE_SIZE', 0) < 1000:
        warnings.append("⚠️ GLOBAL_CACHE_SIZE pode ser muito pequeno para produção")
    
    return warnings