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
    'COORDINATOR': 'gpt-4.1',
    'EMBEDDING': 'voyage-multimodal-3', 
    'MULTIAGENT': 'gpt-4.1-mini',
    'MULTIMODAL': 'voyage-multimodal-3'
}

# Modelos específicos para compatibility com .env
MODEL_CONFIG = {
    'OPENAI_MODEL': 'gpt-4.1-mini',
    'COORDINATOR_MODEL': 'gpt-4.1',
    'EMBEDDING_MODEL': 'voyage-multimodal-3'
}

# =============================================================================
# LIMITES DE TOKENS
# =============================================================================

TOKEN_LIMITS = {
    # IMPORTANTE: MAX_CANDIDATES não é usado como valor fixo global!
    # O valor real é sempre calculado dinamicamente no enhanced_config.py baseado na complexidade:
    # SIMPLE=2, MODERATE=3, COMPLEX=4, VERY_COMPLEX=5
    # Este valor existe apenas para compatibilidade legacy e NÃO deve ser usado
    'MAX_CANDIDATES': 3,  # ⚠️ DEPRECATED - não usar! Valor dinâmico no enhanced_config.py
    'MAX_TOKENS': 4000,
    'MAX_TOKENS_RERANK': 512,
    'MAX_TOKENS_ANSWER': 2048,
    'MAX_TOKENS_QUERY_TRANSFORM': 150,
    'MAX_TOKENS_DECOMPOSITION': 1000,
    'MAX_TOKENS_SCORE': 10,  # Para scores numéricos simples
    'MAX_TOKENS_EVALUATION': 20,  # Para avaliações simples
    'MAX_TOKENS_RATING': 300,  # Para ratings mais detalhados
    'MAX_TOKENS_DECOMPOSITION_ITEM': 200,  # Para itens de decomposição
    'MAX_TOKENS_SUBQUERY': 100,  # Para subqueries
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
    'MULTIAGENT_TIMEOUT': 300.0,
    'REQUEST_TIMEOUT': 60.0,
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
    'CLEANUP_MAX_AGE': 24,
    'TOP_K': 5,
    'CHUNK_SIZE': 1000,
    'CHUNK_OVERLAP': 200,
    'TEMPERATURE': 0.1,
    'TEMPERATURE_SYNTHESIS': 0.2,  # Para síntese criativa
    'TEMPERATURE_PRECISE': 0.0,    # Para operações precisas
    'CONFIDENCE_THRESHOLD': 0.5    # Threshold mínimo para sucesso da API
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
    'DEFAULT_PDF_URL': 'https://arxiv.org/pdf/2501.13956',
    'DATA_DIR': 'data',
    'PDF_IMAGES_DIR': 'pdf_images', 
    'LOGS_DIR': 'logs'
}

# =============================================================================
# LIMITES DE ARQUIVO
# =============================================================================

FILE_LIMITS = {
    'MAX_REQUEST_SIZE': 16777216,    # 16MB
    'MAX_PDF_SIZE': 52428800,        # 50MB
    'MAX_UPLOAD_SIZE': 104857600,    # 100MB
    'ALLOWED_EXTENSIONS': ['.pdf', '.txt', '.md'],
    'MAX_FILENAME_LENGTH': 255
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
    'GENERAL': 'RAGResearchSubagent',
    'CONCEPTUAL': 'ConceptExtractionSubagent',
    'COMPARATIVE': 'ComparativeAnalysisSubagent', 
    'TECHNICAL': 'TechnicalDetailSubagent',
    'EXAMPLES': 'ExampleFinderSubagent'
}

# =============================================================================
# ÁREAS DE FOCO (FOCUS AREAS) - Sistema Original + Atual
# =============================================================================

# Focus areas do sistema original (mais específicas)
ORIGINAL_FOCUS_AREAS = {
    'CONCEPTUAL_UNDERSTANDING': 'conceptual_understanding',
    'TECHNICAL_IMPLEMENTATION': 'technical_implementation', 
    'COMPARATIVE_ANALYSIS': 'comparative_analysis',
    'EXAMPLES_AND_USE_CASES': 'examples_and_use_cases',
    'METHODOLOGICAL_APPROACH': 'methodological_approach',
    'PERFORMANCE_METRICS': 'performance_metrics',
    'LIMITATIONS_AND_CHALLENGES': 'limitations_and_challenges'
}

# Focus areas do sistema atual (simplificadas)
CURRENT_FOCUS_AREAS = {
    'CONCEPTUAL': 'conceptual',
    'TECHNICAL': 'technical',
    'COMPARATIVE': 'comparative',
    'EXAMPLES': 'examples',
    'OVERVIEW': 'overview',
    'APPLICATIONS': 'applications',
    'GENERAL': 'general'
}

# Alias para compatibilidade
FOCUS_AREAS = CURRENT_FOCUS_AREAS

# =============================================================================
# ESTRATÉGIAS DE PESQUISA (Sistema Original)
# =============================================================================

SEARCH_STRATEGIES = {
    'BROAD_TO_SPECIFIC': 'broad_to_specific',
    'SPECIFIC_TO_BROAD': 'specific_to_broad', 
    'COMPARATIVE_ANALYSIS': 'comparative_analysis',
    'ITERATIVE_REFINEMENT': 'iterative_refinement',
    'COMPREHENSIVE_COVERAGE': 'comprehensive_coverage',
    'FOCUSED_DEEP_DIVE': 'focused_deep_dive'
}

QUERY_COMPLEXITY = {
    'SIMPLE': 'simple',
    'MODERATE': 'moderate', 
    'COMPLEX': 'complex',
    'VERY_COMPLEX': 'very_complex'
}

# =============================================================================
# PADRÕES DE QUERY PARA ESPECIALISTAS
# =============================================================================

SPECIALIST_PATTERNS = {
    'GENERAL': [
        'general', 'overview', 'summary', 'introduction',
        'geral', 'visão geral', 'resumo', 'introdução'
    ],
    'CONCEPTUAL': [
        'what is', 'define', 'definition', 'concept', 'meaning', 'explain',
        'o que é', 'definição', 'conceito', 'significado', 'explicar'
    ],
    'COMPARATIVE': [
        'compare', 'versus', 'vs', 'difference', 'similar', 'comparison', 'alternative',
        'comparar', 'diferença', 'similar', 'parecido', 'comparação', 'alternativa'
    ],
    'TECHNICAL': [
        'how to', 'implement', 'technical', 'architecture', 'algorithm', 'implementation',
        'como implementar', 'técnico', 'arquitetura', 'algoritmo', 'implementação'
    ],
    'EXAMPLES': [
        'example', 'case study', 'use case', 'application', 'demonstrate',
        'exemplo', 'caso de uso', 'aplicação', 'demonstração', 'demonstrar'
    ]
}

# =============================================================================
# PADRÕES DE FOCUS AREAS
# =============================================================================

# Padrões para focus areas atuais (simplificadas)
FOCUS_AREA_PATTERNS = {
    'CONCEPTUAL': ['conceptual', 'understanding', 'theory', 'fundamental'],
    'TECHNICAL': ['technical', 'implementation', 'details', 'how-to'],
    'COMPARATIVE': ['comparative', 'analysis', 'comparison', 'versus'],
    'EXAMPLES': ['examples', 'cases', 'use_cases', 'demonstrations'],
    'OVERVIEW': ['overview', 'summary', 'general', 'broad'],
    'APPLICATIONS': ['applications', 'practical', 'real-world', 'usage'],
    'GENERAL': ['general', 'default', 'standard', 'basic']
}

# Padrões para focus areas originais (mais específicas)
ORIGINAL_FOCUS_AREA_PATTERNS = {
    'CONCEPTUAL_UNDERSTANDING': ['concept', 'definition', 'theory', 'principle', 'fundamental'],
    'TECHNICAL_IMPLEMENTATION': ['implementation', 'technical', 'architecture', 'algorithm', 'code'],
    'COMPARATIVE_ANALYSIS': ['compare', 'contrast', 'versus', 'alternative', 'difference'],
    'EXAMPLES_AND_USE_CASES': ['example', 'case study', 'use case', 'application', 'scenario'],
    'METHODOLOGICAL_APPROACH': ['methodology', 'approach', 'method', 'process', 'framework'],
    'PERFORMANCE_METRICS': ['performance', 'metrics', 'benchmark', 'evaluation', 'results'],
    'LIMITATIONS_AND_CHALLENGES': ['limitation', 'challenge', 'problem', 'issue', 'constraint']
}

# =============================================================================
# CONFIGURAÇÕES DE LOGGING
# =============================================================================

LOGGING_CONFIG = {
    'DEFAULT_LEVEL': 'INFO',                        # INFO para produção (não DEBUG)
    'LOG_LEVEL': 'INFO',                            # Compatibility com .env
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
    'MAX_OBJECTIVE_LENGTH': 500,
    'MIN_URL_LENGTH': 10,
    'MAX_URL_LENGTH': 2000,
    'MAX_DOC_SOURCE_LENGTH': 200,
    'DANGEROUS_PATTERNS': [
        '<script', '</script', 'javascript:', 'data:', 'vbscript:',
        'onload=', 'onerror=', 'onclick=', 'eval(', 'expression('
    ],
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
    'ASYNC_CLEANUP': True,                  # Limpeza assíncrona de recursos
    'ENABLE_DEBUG_LOGS': False,             # Logs de debug detalhados
    'ENABLE_TEST_ENDPOINTS': False,         # Endpoints de teste
    'MOCK_AI_RESPONSES': False,             # Respostas mockadas da IA
    'PYTEST_TIMEOUT': 300,                  # Timeout para testes pytest
    'TEST_COLLECTION_NAME': 'test_collection' # Nome da coleção de teste
}

# =============================================================================
# CONFIGURAÇÕES DE SEGURANÇA
# =============================================================================

SECURITY_CONFIG = {
    'API_BEARER_TOKEN': 'your_secure_bearer_token_here',
    'ENABLE_RATE_LIMITING': True,
    'RATE_LIMIT': '100/minute',
    'ENABLE_CORS': False,
    'MAX_REQUESTS_PER_MINUTE': 100,
    'MAX_CONCURRENT_REQUESTS': 20,
    'ENABLE_REQUEST_VALIDATION': True,
    'SECURITY_HEADERS_ENABLED': True,
    'CORS_STRICT_MODE': True
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
# CONFIGURAÇÕES DA API ÚNICA v2.0.0
# =============================================================================

API_UNIFIED_CONFIG = {
    # API Única (Multi-Agente + SimpleRAG)
    'API_PORT': 8000,
    'API_WORKERS': 4,
    'API_TIMEOUT': 300,
    'API_MEMORY_LIMIT': '3GB',
    'API_CPU_LIMIT': '3.0',
    'HOST': '0.0.0.0',
    'RELOAD': True,
    
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
    # API Única (Multi-Agente + SimpleRAG) na porta 8000
    'UNIFIED': {
        'BASE_URL': 'http://localhost:8000',
        'HEALTH': '/api/v1/health',
        'RESEARCH': '/api/v1/research',
        'RESEARCH_SIMPLE': '/api/v1/research/simple',
        'INDEX': '/api/v1/index',
        'DOCUMENTS': '/api/v1/documents/{collection_name}',
        'STATS': '/api/v1/stats',
        'DOCS': '/docs'
    }
}

# =============================================================================
# DOCKER CONFIGURAÇÕES
# =============================================================================

DOCKER_CONFIG = {
    # Containers
    'UNIFIED_API_CONTAINER': 'rag-api-unified',
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
        **DEV_CONFIG,
        **API_UNIFIED_CONFIG,
        'SPECIALIST_TYPES': SPECIALIST_TYPES,
        'FOCUS_AREAS': FOCUS_AREAS,
        'ORIGINAL_FOCUS_AREAS': ORIGINAL_FOCUS_AREAS,
        'SEARCH_STRATEGIES': SEARCH_STRATEGIES,
        'QUERY_COMPLEXITY': QUERY_COMPLEXITY
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