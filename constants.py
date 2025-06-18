"""
Constantes e valores padrão para o sistema RAG Multi-Agente.

Este arquivo centraliza todas as constantes utilizadas no sistema,
fornecendo valores padrão para quando as variáveis de ambiente não estão definidas.
"""

# =============================================================================
# MODELOS DE IA - VALORES PADRÃO
# =============================================================================

DEFAULT_MODELS = {
    'LLM': 'gpt-4o-2024-11-20',
    'EMBEDDING': 'voyage-3', 
    'MULTIAGENT': 'gpt-4o-mini-2024-07-18',
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
    'EMBEDDING_CACHE_SIZE': 500,
    'EMBEDDING_CACHE_TTL': 3600,  # 1 hora
    'RESPONSE_CACHE_SIZE': 100,
    'RESPONSE_CACHE_TTL': 1800,   # 30 minutos
    'GLOBAL_CACHE_SIZE': 1000,
    'GLOBAL_CACHE_TTL': 3600,     # 1 hora
    'L1_CACHE_MAX_SIZE': 1000,
    'L2_CACHE_MAX_SIZE': 5000
}

# =============================================================================
# TIMEOUTS E RETRIES
# =============================================================================

TIMEOUT_CONFIG = {
    'SUBAGENT_TIMEOUT': 180.0,    # 3 minutos
    'DOWNLOAD_TIMEOUT': 30,       # 30 segundos
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 1.0,           # 1 segundo
    'CIRCUIT_BREAKER_THRESHOLD': 5,
    'CIRCUIT_BREAKER_TIMEOUT': 60, # 1 minuto
    'EXPONENTIAL_BACKOFF_MAX': 60.0,  # Máximo 60 segundos
    'LINEAR_BACKOFF_MAX': 30.0,       # Máximo 30 segundos
    'IMMEDIATE_RETRY_DELAY': 1.0      # 1 segundo
}

# =============================================================================
# CONFIGURAÇÕES DE PROCESSAMENTO
# =============================================================================

PROCESSING_CONFIG = {
    'BATCH_SIZE': 100,
    'DOWNLOAD_CHUNK_SIZE': 8192,  # 8KB
    'PIXMAP_SCALE': 2,
    'TOKENS_PER_PIXEL': 1 / 560,  # ≈ 0.00178571
    'TOKEN_CHARS_RATIO': 4,
    'PROCESSING_CONCURRENCY': 5,
    'CLEANUP_MAX_AGE': 24         # 24 horas
}

# =============================================================================
# SISTEMA MULTI-AGENTE
# =============================================================================

MULTIAGENT_CONFIG = {
    'MAX_SUBAGENTS': 3,
    'PARALLEL_EXECUTION': True,
    'USE_LLM_DECOMPOSITION': True,
    'CONCURRENCY_LIMIT': 3,
    'SIMILARITY_THRESHOLD': 0.7  # 70% de similaridade para queries
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
    'USE_MOCK_DATA': False,
    'MOCK_RESULTS_COUNT': 3,
    'DEFAULT_ERROR_MESSAGE': "Desculpe, não consegui encontrar informações sobre isso.",
    'FALLBACK_TO_SIMPLE_SEARCH': True,
    'ENABLE_GRACEFUL_DEGRADATION': True
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
    'DEFAULT_LEVEL': 'INFO',
    'MAX_LOG_FILE_SIZE': 10,  # MB
    'LOG_ROTATION_COUNT': 5,
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
# CONFIGURAÇÕES DE DESENVOLVIMENTO
# =============================================================================

DEV_CONFIG = {
    'DEBUG_MODE': False,
    'VERBOSE_LOGGING': False,
    'ENABLE_PERFORMANCE_METRICS': True,
    'SAVE_INTERMEDIATE_RESULTS': False,
    'MOCK_API_CALLS': False
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
        **FALLBACK_CONFIG
    }