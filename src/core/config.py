"""
Configurações centralizadas do sistema RAG Multi-Agente
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv
from .constants import (
    DEFAULT_MODELS, MODEL_CONFIG, TOKEN_LIMITS, CACHE_CONFIG, TIMEOUT_CONFIG,
    PROCESSING_CONFIG, MULTIAGENT_CONFIG, SYSTEM_DEFAULTS,
    LOGGING_CONFIG, PRODUCTION_CONFIG, DEV_CONFIG, FALLBACK_CONFIG,
    NATIVE_MODELS_CONFIG, API_ENDPOINTS, DOCKER_CONFIG, SECURITY_CONFIG,
    FILE_LIMITS, API_UNIFIED_CONFIG, validate_production_config, get_production_config
)

# Carregar variáveis de ambiente
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)

def get_env_int(key: str, default: int) -> int:
    """Obtém valor inteiro do ambiente ou retorna padrão."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

def get_env_float(key: str, default: float) -> float:
    """Obtém valor float do ambiente ou retorna padrão."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

def get_env_bool(key: str, default: bool) -> bool:
    """Obtém valor booleano do ambiente ou retorna padrão."""
    return os.getenv(key, str(default)).lower() in ('true', '1', 'yes', 'on')

@dataclass
class RAGConfig:
    """Configurações do sistema RAG."""
    # Modelos (usando nomes padronizados)
    llm_model: str = os.getenv('OPENAI_MODEL', DEFAULT_MODELS['LLM'])
    coordinator_model: str = os.getenv('COORDINATOR_MODEL', DEFAULT_MODELS['COORDINATOR'])
    embedding_model: str = os.getenv('EMBEDDING_MODEL', DEFAULT_MODELS['EMBEDDING'])
    multimodal_model: str = os.getenv('EMBEDDING_MODEL', DEFAULT_MODELS['MULTIMODAL'])
    
    # Limites de tokens
    max_candidates: int = get_env_int('MAX_CANDIDATES', TOKEN_LIMITS['MAX_CANDIDATES'])
    max_tokens: int = get_env_int('MAX_TOKENS', TOKEN_LIMITS['MAX_TOKENS'])
    max_tokens_rerank: int = get_env_int('MAX_TOKENS_RERANK', TOKEN_LIMITS['MAX_TOKENS_RERANK'])
    max_tokens_answer: int = get_env_int('MAX_TOKENS_ANSWER', TOKEN_LIMITS['MAX_TOKENS_ANSWER'])
    max_tokens_query_transform: int = get_env_int('MAX_TOKENS_QUERY_TRANSFORM', TOKEN_LIMITS['MAX_TOKENS_QUERY_TRANSFORM'])
    max_tokens_score: int = get_env_int('MAX_TOKENS_SCORE', TOKEN_LIMITS['MAX_TOKENS_SCORE'])
    max_tokens_evaluation: int = get_env_int('MAX_TOKENS_EVALUATION', TOKEN_LIMITS['MAX_TOKENS_EVALUATION'])
    max_tokens_rating: int = get_env_int('MAX_TOKENS_RATING', TOKEN_LIMITS['MAX_TOKENS_RATING'])
    max_tokens_decomposition_item: int = get_env_int('MAX_TOKENS_DECOMPOSITION_ITEM', TOKEN_LIMITS['MAX_TOKENS_DECOMPOSITION_ITEM'])
    max_tokens_subquery: int = get_env_int('MAX_TOKENS_SUBQUERY', TOKEN_LIMITS['MAX_TOKENS_SUBQUERY'])
    voyage_embedding_dim: int = get_env_int('VOYAGE_EMBEDDING_DIM', TOKEN_LIMITS['VOYAGE_EMBEDDING_DIM'])
    max_tokens_per_input: int = get_env_int('MAX_TOKENS_PER_INPUT', TOKEN_LIMITS['MAX_TOKENS_PER_INPUT'])
    
    # Cache
    embedding_cache_size: int = get_env_int('EMBEDDING_CACHE_SIZE', CACHE_CONFIG['EMBEDDING_CACHE_SIZE'])
    embedding_cache_ttl: int = get_env_int('EMBEDDING_CACHE_TTL', CACHE_CONFIG['EMBEDDING_CACHE_TTL'])
    response_cache_size: int = get_env_int('RESPONSE_CACHE_SIZE', CACHE_CONFIG['RESPONSE_CACHE_SIZE'])
    response_cache_ttl: int = get_env_int('RESPONSE_CACHE_TTL', CACHE_CONFIG['RESPONSE_CACHE_TTL'])
    
    # Processing
    top_k: int = get_env_int('TOP_K', PROCESSING_CONFIG['TOP_K'])
    chunk_size: int = get_env_int('CHUNK_SIZE', PROCESSING_CONFIG['CHUNK_SIZE'])
    chunk_overlap: int = get_env_int('CHUNK_OVERLAP', PROCESSING_CONFIG['CHUNK_OVERLAP'])
    temperature: float = get_env_float('TEMPERATURE', PROCESSING_CONFIG['TEMPERATURE'])
    temperature_synthesis: float = get_env_float('TEMPERATURE_SYNTHESIS', PROCESSING_CONFIG['TEMPERATURE_SYNTHESIS'])
    temperature_precise: float = get_env_float('TEMPERATURE_PRECISE', PROCESSING_CONFIG['TEMPERATURE_PRECISE'])
    confidence_threshold: float = get_env_float('CONFIDENCE_THRESHOLD', PROCESSING_CONFIG['CONFIDENCE_THRESHOLD'])
    
    # Database
    collection_name: str = os.getenv('COLLECTION_NAME', SYSTEM_DEFAULTS['COLLECTION_NAME'])
    
    # File and Directory
    data_dir: str = os.getenv('DATA_DIR', SYSTEM_DEFAULTS['DATA_DIR'])
    pdf_images_dir: str = os.getenv('PDF_IMAGES_DIR', SYSTEM_DEFAULTS['PDF_IMAGES_DIR'])
    logs_dir: str = os.getenv('LOGS_DIR', SYSTEM_DEFAULTS['LOGS_DIR'])
    max_request_size: int = get_env_int('MAX_REQUEST_SIZE', FILE_LIMITS['MAX_REQUEST_SIZE'])
    max_pdf_size: int = get_env_int('MAX_PDF_SIZE', FILE_LIMITS['MAX_PDF_SIZE'])
    
    # APIs
    openai_api_key: Optional[str] = None
    voyage_api_key: Optional[str] = None
    astra_db_api_endpoint: Optional[str] = None
    astra_db_application_token: Optional[str] = None
    
    def __post_init__(self):
        """Carregar configurações do ambiente."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.astra_db_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        self.astra_db_application_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    
    def validate(self) -> Dict[str, Any]:
        """Valida se as configurações estão corretas."""
        errors = []
        warnings = []
        
        # Verificar APIs obrigatórias
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY não configurada")
        if not self.voyage_api_key:
            errors.append("VOYAGE_API_KEY não configurada")
        if not self.astra_db_api_endpoint:
            errors.append("ASTRA_DB_API_ENDPOINT não configurada")
        if not self.astra_db_application_token:
            errors.append("ASTRA_DB_APPLICATION_TOKEN não configurada")
        
        # Verificar limites
        if self.max_candidates < 1 or self.max_candidates > 20:
            warnings.append(f"max_candidates ({self.max_candidates}) fora do range recomendado (1-20)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


@dataclass
class MultiAgentConfig:
    """Configurações do sistema multi-agente."""
    # Agentes
    max_subagents: int = get_env_int('MAX_SUBAGENTS', MULTIAGENT_CONFIG['MAX_SUBAGENTS'])
    parallel_execution: bool = get_env_bool('PARALLEL_EXECUTION', MULTIAGENT_CONFIG['PARALLEL_EXECUTION'])
    concurrency_limit: int = get_env_int('CONCURRENCY_LIMIT', MULTIAGENT_CONFIG['CONCURRENCY_LIMIT'])
    subagent_timeout: float = get_env_float('SUBAGENT_TIMEOUT', TIMEOUT_CONFIG['SUBAGENT_TIMEOUT'])
    
    # LLM
    model: str = os.getenv('MULTIAGENT_MODEL', DEFAULT_MODELS['MULTIAGENT'])
    use_llm_decomposition: bool = get_env_bool('USE_LLM_DECOMPOSITION', MULTIAGENT_CONFIG['USE_LLM_DECOMPOSITION'])
    max_tokens: int = get_env_int('MAX_TOKENS', TOKEN_LIMITS['MAX_TOKENS'])
    
    # Timeouts e retries
    multiagent_timeout: float = get_env_float('MULTIAGENT_TIMEOUT', TIMEOUT_CONFIG['MULTIAGENT_TIMEOUT'])
    subagent_timeout: float = get_env_float('SUBAGENT_TIMEOUT', TIMEOUT_CONFIG['SUBAGENT_TIMEOUT'])
    request_timeout: float = get_env_float('REQUEST_TIMEOUT', TIMEOUT_CONFIG['REQUEST_TIMEOUT'])
    max_retries: int = get_env_int('MAX_RETRIES', TIMEOUT_CONFIG['MAX_RETRIES'])
    retry_delay: float = get_env_float('RETRY_DELAY', TIMEOUT_CONFIG['RETRY_DELAY'])
    circuit_breaker_threshold: int = get_env_int('CIRCUIT_BREAKER_THRESHOLD', TIMEOUT_CONFIG['CIRCUIT_BREAKER_THRESHOLD'])
    circuit_breaker_timeout: int = get_env_int('CIRCUIT_BREAKER_TIMEOUT', TIMEOUT_CONFIG['CIRCUIT_BREAKER_TIMEOUT'])
    exponential_backoff_max: float = get_env_float('EXPONENTIAL_BACKOFF_MAX', TIMEOUT_CONFIG['EXPONENTIAL_BACKOFF_MAX'])
    linear_backoff_max: float = get_env_float('LINEAR_BACKOFF_MAX', TIMEOUT_CONFIG['LINEAR_BACKOFF_MAX'])
    immediate_retry_delay: float = get_env_float('IMMEDIATE_RETRY_DELAY', TIMEOUT_CONFIG['IMMEDIATE_RETRY_DELAY'])
    similarity_threshold: float = get_env_float('SIMILARITY_THRESHOLD', MULTIAGENT_CONFIG['SIMILARITY_THRESHOLD'])
    
    # APIs
    openai_api_key: Optional[str] = None
    
    def __post_init__(self):
        """Carregar configurações do ambiente."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def validate(self) -> Dict[str, Any]:
        """Valida configurações."""
        errors = []
        warnings = []
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY não configurada para multi-agente")
        
        if self.max_subagents < 1 or self.max_subagents > 10:
            warnings.append(f"max_subagents ({self.max_subagents}) fora do range recomendado (1-10)")
        
        if self.subagent_timeout < 30:
            warnings.append(f"subagent_timeout ({self.subagent_timeout}s) muito baixo")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


@dataclass
class ProcessingConfig:
    """Configurações de processamento e indexing."""
    # URLs e caminhos
    default_pdf_url: str = os.getenv('DEFAULT_PDF_URL', SYSTEM_DEFAULTS['DEFAULT_PDF_URL'])
    image_dir: str = os.getenv('IMAGE_DIR', SYSTEM_DEFAULTS['IMAGE_DIR'])
    
    # Processamento
    batch_size: int = get_env_int('BATCH_SIZE', PROCESSING_CONFIG['BATCH_SIZE'])
    processing_concurrency: int = get_env_int('PROCESSING_CONCURRENCY', PROCESSING_CONFIG['PROCESSING_CONCURRENCY'])
    download_timeout: int = get_env_int('DOWNLOAD_TIMEOUT', TIMEOUT_CONFIG['DOWNLOAD_TIMEOUT'])
    download_chunk_size: int = get_env_int('DOWNLOAD_CHUNK_SIZE', PROCESSING_CONFIG['DOWNLOAD_CHUNK_SIZE'])
    pixmap_scale: int = get_env_int('PIXMAP_SCALE', PROCESSING_CONFIG['PIXMAP_SCALE'])
    
    # Cálculos de tokens
    tokens_per_pixel: float = get_env_float('TOKENS_PER_PIXEL', PROCESSING_CONFIG['TOKENS_PER_PIXEL'])
    token_chars_ratio: int = get_env_int('TOKEN_CHARS_RATIO', PROCESSING_CONFIG['TOKEN_CHARS_RATIO'])
    
    # Limpeza
    cleanup_max_age: int = get_env_int('CLEANUP_MAX_AGE', PROCESSING_CONFIG['CLEANUP_MAX_AGE'])


@dataclass
class MemoryConfig:
    """Configurações do sistema de memória."""
    # Cache hierárquico
    l1_cache_max_size: int = get_env_int('L1_CACHE_MAX_SIZE', CACHE_CONFIG['L1_CACHE_MAX_SIZE'])
    l2_cache_max_size: int = get_env_int('L2_CACHE_MAX_SIZE', CACHE_CONFIG['L2_CACHE_MAX_SIZE'])
    global_cache_size: int = get_env_int('GLOBAL_CACHE_SIZE', CACHE_CONFIG['GLOBAL_CACHE_SIZE'])
    global_cache_ttl: int = get_env_int('GLOBAL_CACHE_TTL', CACHE_CONFIG['GLOBAL_CACHE_TTL'])
    
    # Sharding
    memory_shards: int = get_env_int('MEMORY_SHARDS', 4)
    shard_strategy: str = os.getenv('SHARD_STRATEGY', 'agent_hash')


@dataclass
class SecurityConfig:
    """Configurações de segurança da API."""
    # Segurança
    api_bearer_token: str = os.getenv('API_BEARER_TOKEN', SECURITY_CONFIG['API_BEARER_TOKEN'])
    enable_rate_limiting: bool = get_env_bool('ENABLE_RATE_LIMITING', SECURITY_CONFIG['ENABLE_RATE_LIMITING'])
    rate_limit: str = os.getenv('RATE_LIMIT', SECURITY_CONFIG['RATE_LIMIT'])
    enable_cors: bool = get_env_bool('ENABLE_CORS', SECURITY_CONFIG['ENABLE_CORS'])
    max_requests_per_minute: int = get_env_int('MAX_REQUESTS_PER_MINUTE', SECURITY_CONFIG['MAX_REQUESTS_PER_MINUTE'])
    max_concurrent_requests: int = get_env_int('MAX_CONCURRENT_REQUESTS', SECURITY_CONFIG['MAX_CONCURRENT_REQUESTS'])
    enable_request_validation: bool = get_env_bool('ENABLE_REQUEST_VALIDATION', SECURITY_CONFIG['ENABLE_REQUEST_VALIDATION'])
    security_headers_enabled: bool = get_env_bool('SECURITY_HEADERS_ENABLED', SECURITY_CONFIG['SECURITY_HEADERS_ENABLED'])
    cors_strict_mode: bool = get_env_bool('CORS_STRICT_MODE', SECURITY_CONFIG['CORS_STRICT_MODE'])


@dataclass 
class ProductionConfig:
    """Configurações específicas para ambiente de produção."""
    
    # Configurações de desenvolvimento/debug (usando nomes padronizados)
    debug_mode: bool = get_env_bool('DEBUG_MODE', DEV_CONFIG['DEBUG_MODE'])
    verbose_logging: bool = get_env_bool('VERBOSE_LOGGING', DEV_CONFIG['VERBOSE_LOGGING'])
    production_mode: bool = get_env_bool('PRODUCTION_MODE', True)  # Padrão para True
    enable_performance_metrics: bool = get_env_bool('ENABLE_PERFORMANCE_METRICS', DEV_CONFIG['ENABLE_PERFORMANCE_METRICS'])
    enable_structured_logging: bool = get_env_bool('ENABLE_STRUCTURED_LOGGING', LOGGING_CONFIG['ENABLE_STRUCTURED_LOGGING'])
    
    # Desenvolvimento
    enable_debug_logs: bool = get_env_bool('ENABLE_DEBUG_LOGS', DEV_CONFIG['ENABLE_DEBUG_LOGS'])
    enable_test_endpoints: bool = get_env_bool('ENABLE_TEST_ENDPOINTS', DEV_CONFIG['ENABLE_TEST_ENDPOINTS'])
    mock_ai_responses: bool = get_env_bool('MOCK_AI_RESPONSES', DEV_CONFIG['MOCK_AI_RESPONSES'])
    pytest_timeout: int = get_env_int('PYTEST_TIMEOUT', DEV_CONFIG['PYTEST_TIMEOUT'])
    test_collection_name: str = os.getenv('TEST_COLLECTION_NAME', DEV_CONFIG['TEST_COLLECTION_NAME'])
    
    # Logging
    log_level: str = os.getenv('LOG_LEVEL', LOGGING_CONFIG['DEFAULT_LEVEL'])
    enable_structured_logging: bool = get_env_bool('ENABLE_STRUCTURED_LOGGING', LOGGING_CONFIG['ENABLE_STRUCTURED_LOGGING'])
    max_log_file_size: int = get_env_int('MAX_LOG_FILE_SIZE', LOGGING_CONFIG['MAX_LOG_FILE_SIZE'])
    log_rotation_count: int = get_env_int('LOG_ROTATION_COUNT', LOGGING_CONFIG['LOG_ROTATION_COUNT'])
    async_logging: bool = get_env_bool('ASYNC_LOGGING', LOGGING_CONFIG['ASYNC_LOGGING'])
    
    # Multi-Agent System Logging
    enable_multiagent_logs: bool = get_env_bool('ENABLE_MULTIAGENT_LOGS', LOGGING_CONFIG['ENABLE_MULTIAGENT_LOGS'])
    multiagent_log_level: str = os.getenv('MULTIAGENT_LOG_LEVEL', LOGGING_CONFIG['MULTIAGENT_LOG_LEVEL'])
    enable_reasoning_trace_logs: bool = get_env_bool('ENABLE_REASONING_TRACE_LOGS', LOGGING_CONFIG['ENABLE_REASONING_TRACE_LOGS'])
    enable_subagent_logs: bool = get_env_bool('ENABLE_SUBAGENT_LOGS', LOGGING_CONFIG['ENABLE_SUBAGENT_LOGS'])
    multiagent_log_file: str = os.getenv('MULTIAGENT_LOG_FILE', LOGGING_CONFIG['MULTIAGENT_LOG_FILE'])
    
    # Segurança e Rate Limiting (removido hardcoding)
    # Agora usando SecurityConfig
    
    # Monitoramento
    monitoring_enabled: bool = get_env_bool('MONITORING_ENABLED', True)  # Usar valor padrão
    
    # Timeouts específicos de produção (usando valores padrão)
    database_timeout: int = get_env_int('DATABASE_TIMEOUT', 30)
    redis_timeout: int = get_env_int('REDIS_TIMEOUT', 5)
    external_api_timeout: int = get_env_int('EXTERNAL_API_TIMEOUT', 10)
    download_timeout: int = get_env_int('DOWNLOAD_TIMEOUT', 30)
    cache_ttl: int = get_env_int('CACHE_TTL', 3600)
    
    def validate(self) -> Dict[str, Any]:
        """Valida configurações de produção."""
        errors = []
        warnings = []
        
        # Verificações críticas para produção
        if self.debug_mode:
            errors.append("DEBUG_MODE deve ser False em produção")
        
        if self.verbose_logging:
            warnings.append("VERBOSE_LOGGING recomendado como False em produção")
            
        if not self.production_mode:
            warnings.append("PRODUCTION_MODE deve ser True em produção")
            
        if not self.enable_rate_limiting:
            warnings.append("Rate limiting recomendado para produção")
            
        # Validações da função validate_production_config
        prod_warnings = validate_production_config()
        warnings.extend(prod_warnings)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors, 
            "warnings": warnings
        }


@dataclass
class APIConfig:
    """Configurações específicas para as APIs."""
    
    # API Settings
    api_port: int = get_env_int('API_PORT', API_UNIFIED_CONFIG['API_PORT'])
    api_workers: int = get_env_int('API_WORKERS', API_UNIFIED_CONFIG['API_WORKERS'])
    api_timeout: int = get_env_int('API_TIMEOUT', API_UNIFIED_CONFIG['API_TIMEOUT'])
    host: str = os.getenv('HOST', API_UNIFIED_CONFIG['HOST'])
    reload: bool = get_env_bool('RELOAD', API_UNIFIED_CONFIG['RELOAD'])
    
    # Common settings
    health_check_interval: int = get_env_int('HEALTH_CHECK_INTERVAL', API_UNIFIED_CONFIG['HEALTH_CHECK_INTERVAL'])
    health_check_timeout: int = get_env_int('HEALTH_CHECK_TIMEOUT', API_UNIFIED_CONFIG['HEALTH_CHECK_TIMEOUT'])
    startup_timeout: int = get_env_int('STARTUP_TIMEOUT', API_UNIFIED_CONFIG['STARTUP_TIMEOUT'])
    factory_pattern_enabled: bool = get_env_bool('FACTORY_PATTERN_ENABLED', API_UNIFIED_CONFIG['FACTORY_PATTERN_ENABLED'])
    native_models_only: bool = get_env_bool('NATIVE_MODELS_ONLY', API_UNIFIED_CONFIG['NATIVE_MODELS_ONLY'])
    
    def get_api_base_url(self) -> str:
        """Retorna URL base da API."""
        return f"http://localhost:{self.api_port}"
    
    def get_endpoints(self) -> Dict[str, Any]:
        """Retorna endpoints configurados."""
        endpoints = API_ENDPOINTS['UNIFIED'].copy()
        endpoints['BASE_URL'] = self.get_api_base_url()
        return endpoints


class SystemConfig:
    """Configuração central do sistema."""
    
    def __init__(self):
        self.rag = RAGConfig()
        self.multiagent = MultiAgentConfig()
        self.processing = ProcessingConfig()
        self.memory = MemoryConfig()
        self.production = ProductionConfig()
        self.security = SecurityConfig()
        self.api = APIConfig()
    
    def validate_all(self) -> Dict[str, Any]:
        """Valida todas as configurações."""
        rag_validation = self.rag.validate()
        multiagent_validation = self.multiagent.validate()
        production_validation = self.production.validate()
        
        all_errors = rag_validation["errors"] + multiagent_validation["errors"] + production_validation["errors"]
        all_warnings = rag_validation["warnings"] + multiagent_validation["warnings"] + production_validation["warnings"]
        
        # Validações específicas das APIs
        if not self.api.native_models_only:
            all_warnings.append("APIs devem usar apenas modelos nativos")
        
        if not self.api.factory_pattern_enabled:
            all_warnings.append("Factory pattern recomendado para APIs")
        
        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "rag_valid": rag_validation["valid"],
            "multiagent_valid": multiagent_validation["valid"],
            "production_valid": production_validation["valid"],
            "apis_ready": True
        }
    
    def print_status(self):
        """Imprime status das configurações."""
        validation = self.validate_all()
        
        print("🔧 STATUS DAS CONFIGURAÇÕES")
        print("=" * 50)
        
        if validation["valid"]:
            print("✅ Todas as configurações válidas!")
        else:
            print("❌ Configurações com problemas:")
            for error in validation["errors"]:
                print(f"  • {error}")
        
        if validation["warnings"]:
            print("\n⚠️  Avisos:")
            for warning in validation["warnings"]:
                print(f"  • {warning}")
        
        print(f"\n📊 Status dos componentes:")
        print(f"  • RAG: {'✅' if validation['rag_valid'] else '❌'}")
        print(f"  • Multi-Agente: {'✅' if validation['multiagent_valid'] else '❌'}")
        print(f"  • Produção: {'✅' if validation['production_valid'] else '❌'}")
        print(f"  • APIs: {'✅' if validation['apis_ready'] else '❌'}")
        
        print(f"\n🔧 Configurações ativas:")
        print(f"  • Modelo LLM: {self.rag.llm_model}")
        print(f"  • Modelo Multi-Agente: {self.multiagent.model}")
        print(f"  • Max Candidatos: {self.rag.max_candidates}")
        print(f"  • Max Tokens: {self.rag.max_tokens}")
        print(f"  • Temperature: {self.rag.temperature}")
        print(f"  • Top K: {self.rag.top_k}")
        print(f"  • Chunk Size: {self.rag.chunk_size}")
        print(f"  • Max Subagentes: {self.multiagent.max_subagents}")
        print(f"  • Cache TTL: {self.rag.embedding_cache_ttl}s")
        print(f"  • Timeout Subagentes: {self.multiagent.subagent_timeout}s")
        print(f"  • Timeout Multi-Agente: {self.multiagent.multiagent_timeout}s")
        print(f"  • Request Timeout: {self.multiagent.request_timeout}s")
        print(f"  • Data Dir: {self.rag.data_dir}")
        print(f"  • PDF Images Dir: {self.rag.pdf_images_dir}")
        print(f"  • Logs Dir: {self.rag.logs_dir}")
        
        print(f"\n🚀 API:")
        print(f"  • API Base URL: {self.api.get_api_base_url()}")
        print(f"  • Workers: {self.api.api_workers}")
        print(f"  • Host: {self.api.host}")
        print(f"  • Reload: {'✅' if self.api.reload else '❌'}")
        print(f"  • Timeout: {self.api.api_timeout}s")
        print(f"  • Modelos Nativos: {'✅' if self.api.native_models_only else '❌'}")
        print(f"  • Factory Pattern: {'✅' if self.api.factory_pattern_enabled else '❌'}")
        
        print(f"\n🔒 Segurança:")
        print(f"  • Rate Limiting: {'✅' if self.security.enable_rate_limiting else '❌'}")
        print(f"  • CORS: {'✅' if self.security.enable_cors else '❌'}")
        print(f"  • Max Requests/min: {self.security.max_requests_per_minute}")
        print(f"  • Security Headers: {'✅' if self.security.security_headers_enabled else '❌'}")
        print(f"  • Request Validation: {'✅' if self.security.enable_request_validation else '❌'}")
        
        print(f"\n🚀 Configurações de Produção:")
        print(f"  • Modo Produção: {'✅' if self.production.production_mode else '❌'}")
        print(f"  • Debug Mode: {'❌' if not self.production.debug_mode else '⚠️'}")
        print(f"  • Logging Estruturado: {'✅' if self.production.enable_structured_logging else '❌'}")
        print(f"  • Monitoramento: {'✅' if self.production.monitoring_enabled else '❌'}")
        print(f"  • Log Level: {self.production.log_level}")
        print(f"  • Debug Logs: {'✅' if self.production.enable_debug_logs else '❌'}")
        print(f"  • Test Endpoints: {'✅' if self.production.enable_test_endpoints else '❌'}")
        print(f"  • Mock AI: {'✅' if self.production.mock_ai_responses else '❌'}")
    
    def get_native_models(self) -> Dict[str, str]:
        """Retorna configuração de modelos nativos."""
        return NATIVE_MODELS_CONFIG
    
    def get_docker_config(self) -> Dict[str, Any]:
        """Retorna configuração Docker."""
        return DOCKER_CONFIG


# Instância global de configuração
config = SystemConfig()

if __name__ == "__main__":
    config.print_status()