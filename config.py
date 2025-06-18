"""
Configurações centralizadas do sistema RAG Multi-Agente
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv
from constants import (
    DEFAULT_MODELS, TOKEN_LIMITS, CACHE_CONFIG, TIMEOUT_CONFIG,
    PROCESSING_CONFIG, MULTIAGENT_CONFIG, SYSTEM_DEFAULTS
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
    # Modelos
    llm_model: str = os.getenv('RAG_LLM_MODEL', DEFAULT_MODELS['LLM'])
    embedding_model: str = os.getenv('RAG_EMBEDDING_MODEL', DEFAULT_MODELS['EMBEDDING'])
    multimodal_model: str = os.getenv('VOYAGE_MULTIMODAL_MODEL', DEFAULT_MODELS['MULTIMODAL'])
    
    # Limites de tokens
    max_candidates: int = get_env_int('MAX_CANDIDATES', TOKEN_LIMITS['MAX_CANDIDATES'])
    max_tokens_rerank: int = get_env_int('MAX_TOKENS_RERANK', TOKEN_LIMITS['MAX_TOKENS_RERANK'])
    max_tokens_answer: int = get_env_int('MAX_TOKENS_ANSWER', TOKEN_LIMITS['MAX_TOKENS_ANSWER'])
    max_tokens_query_transform: int = get_env_int('MAX_TOKENS_QUERY_TRANSFORM', TOKEN_LIMITS['MAX_TOKENS_QUERY_TRANSFORM'])
    voyage_embedding_dim: int = get_env_int('VOYAGE_EMBEDDING_DIM', TOKEN_LIMITS['VOYAGE_EMBEDDING_DIM'])
    max_tokens_per_input: int = get_env_int('MAX_TOKENS_PER_INPUT', TOKEN_LIMITS['MAX_TOKENS_PER_INPUT'])
    
    # Cache
    embedding_cache_size: int = get_env_int('EMBEDDING_CACHE_SIZE', CACHE_CONFIG['EMBEDDING_CACHE_SIZE'])
    embedding_cache_ttl: int = get_env_int('EMBEDDING_CACHE_TTL', CACHE_CONFIG['EMBEDDING_CACHE_TTL'])
    response_cache_size: int = get_env_int('RESPONSE_CACHE_SIZE', CACHE_CONFIG['RESPONSE_CACHE_SIZE'])
    response_cache_ttl: int = get_env_int('RESPONSE_CACHE_TTL', CACHE_CONFIG['RESPONSE_CACHE_TTL'])
    
    # Database
    collection_name: str = os.getenv('COLLECTION_NAME', SYSTEM_DEFAULTS['COLLECTION_NAME'])
    
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
    max_tokens: int = get_env_int('MAX_TOKENS_DECOMPOSITION', TOKEN_LIMITS['MAX_TOKENS_DECOMPOSITION'])
    
    # Timeouts e retries
    max_retries: int = get_env_int('MAX_RETRIES', TIMEOUT_CONFIG['MAX_RETRIES'])
    retry_delay: float = get_env_float('RETRY_DELAY', TIMEOUT_CONFIG['RETRY_DELAY'])
    circuit_breaker_threshold: int = get_env_int('CIRCUIT_BREAKER_THRESHOLD', TIMEOUT_CONFIG['CIRCUIT_BREAKER_THRESHOLD'])
    circuit_breaker_timeout: int = get_env_int('CIRCUIT_BREAKER_TIMEOUT', TIMEOUT_CONFIG['CIRCUIT_BREAKER_TIMEOUT'])
    
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


class SystemConfig:
    """Configuração central do sistema."""
    
    def __init__(self):
        self.rag = RAGConfig()
        self.multiagent = MultiAgentConfig()
        self.processing = ProcessingConfig()
        self.memory = MemoryConfig()
    
    def validate_all(self) -> Dict[str, Any]:
        """Valida todas as configurações."""
        rag_validation = self.rag.validate()
        multiagent_validation = self.multiagent.validate()
        
        all_errors = rag_validation["errors"] + multiagent_validation["errors"]
        all_warnings = rag_validation["warnings"] + multiagent_validation["warnings"]
        
        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "rag_valid": rag_validation["valid"],
            "multiagent_valid": multiagent_validation["valid"]
        }
    
    def print_status(self):
        """Imprime status das configurações."""
        validation = self.validate_all()
        
        print("🔧 STATUS DAS CONFIGURAÇÕES")
        print("=" * 40)
        
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
        
        print(f"\n🔧 Configurações ativas:")
        print(f"  • Modelo LLM: {self.rag.llm_model}")
        print(f"  • Modelo Multi-Agente: {self.multiagent.model}")
        print(f"  • Max Candidatos: {self.rag.max_candidates}")
        print(f"  • Max Subagentes: {self.multiagent.max_subagents}")
        print(f"  • Cache TTL: {self.rag.embedding_cache_ttl}s")
        print(f"  • Timeout Subagentes: {self.multiagent.subagent_timeout}s")


# Instância global de configuração
config = SystemConfig()

if __name__ == "__main__":
    config.print_status()