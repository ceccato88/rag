#!/usr/bin/env python3
"""
🔧 Configuração Centralizada - API Multi-Agente

Sistema centralizado de configuração usando Pydantic V2 Settings
com validação automática e carregamento de variáveis de ambiente.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()


class DatabaseConfig(BaseSettings):
    """Configurações do banco de dados"""
    model_config = SettingsConfigDict(case_sensitive=False)
    
    astra_db_api_endpoint: str = Field(..., description="Endpoint da API do AstraDB")
    astra_db_application_token: str = Field(..., description="Token de aplicação do AstraDB")
    astra_db_namespace: str = Field(default="default_keyspace", description="Namespace do AstraDB")


class AIConfig(BaseSettings):
    """Configurações de IA e modelos"""
    model_config = SettingsConfigDict(case_sensitive=False)
    
    openai_api_key: str = Field(..., description="Chave da API OpenAI")
    voyage_api_key: str = Field(..., description="Chave da API Voyage")
    openai_model: str = Field(default="gpt-4.1-mini", description="Modelo OpenAI para subagentes")
    coordinator_model: str = Field(default="gpt-4.1", description="Modelo OpenAI para coordenador")
    embedding_model: str = Field(default="voyage-multimodal-3", description="Modelo de embedding")
    max_tokens: int = Field(default=4000, ge=1, le=100000, description="Máximo de tokens")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperatura do modelo")


class SecurityConfig(BaseSettings):
    """Configurações de segurança"""
    model_config = SettingsConfigDict(case_sensitive=False)
    
    bearer_token: Optional[str] = Field(default=None, alias="api_bearer_token", description="Token Bearer para autenticação")
    enable_cors: bool = Field(default=False, description="Habilitar CORS")
    cors_origins: Union[str, List[str]] = Field(default="", description="Origens permitidas para CORS")
    enable_rate_limiting: bool = Field(default=True, description="Habilitar rate limiting")
    rate_limit: str = Field(default="100/minute", description="Limite de requisições")
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if not v or v.strip() == "":
                return []
            # Se é uma string, dividir por vírgula
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna cors_origins como lista garantindo compatibilidade"""
        if isinstance(self.cors_origins, str):
            if not self.cors_origins or self.cors_origins.strip() == "":
                return []
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins if isinstance(self.cors_origins, list) else []
    
    @field_validator('bearer_token')
    @classmethod
    def validate_bearer_token_in_production(cls, v):
        production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
        if production_mode and not v:
            raise ValueError("Bearer token é obrigatório em modo de produção")
        return v


class ServerConfig(BaseSettings):
    """Configurações do servidor"""
    model_config = SettingsConfigDict(case_sensitive=False)
    
    host: str = Field(default="0.0.0.0", alias="api_host", description="Host do servidor")
    port: int = Field(default=8000, alias="api_port", ge=1, le=65535, description="Porta do servidor")
    workers: int = Field(default=1, alias="api_workers", ge=1, le=10, description="Número de workers")
    reload: bool = Field(default=False, alias="api_reload", description="Habilitar reload automático")
    log_level: str = Field(default="INFO", alias="api_log_level", description="Nível de log")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level deve ser um de: {valid_levels}")
        return v_upper


class ProductionConfig(BaseSettings):
    """Configurações específicas de produção"""
    model_config = SettingsConfigDict(case_sensitive=False)
    
    production_mode: bool = Field(default=True, description="Modo de produção")
    debug_mode: bool = Field(default=False, description="Modo debug")
    verbose_logging: bool = Field(default=False, description="Logging verboso")
    monitoring_enabled: bool = Field(default=True, description="Monitoramento habilitado")
    enable_metrics: bool = Field(default=True, description="Habilitar métricas")
    enable_tracing: bool = Field(default=False, description="Habilitar tracing")
    max_request_size: int = Field(default=16 * 1024 * 1024, description="Tamanho máximo de requisição")
    request_timeout: int = Field(default=300, ge=1, description="Timeout de requisição em segundos")
    
    # Timeouts adicionais
    redis_timeout: int = Field(default=5, ge=1, description="Timeout Redis em segundos")
    database_timeout: int = Field(default=30, ge=1, description="Timeout banco de dados em segundos")
    external_api_timeout: int = Field(default=10, ge=1, description="Timeout APIs externas em segundos")
    download_timeout: int = Field(default=30, ge=1, description="Timeout downloads em segundos")
    cache_ttl: int = Field(default=3600, ge=1, description="TTL cache em segundos")


class PathConfig(BaseSettings):
    """Configurações de caminhos e diretórios"""
    model_config = SettingsConfigDict(case_sensitive=False)
    
    workspace_root: Path = Field(default=Path("/workspaces/rag"), description="Diretório raiz do workspace")
    log_dir: Path = Field(default=Path("logs"), description="Diretório de logs")
    temp_dir: Path = Field(default=Path("temp"), description="Diretório temporário")
    pdf_images_dir: Path = Field(default=Path("pdf_images"), description="Diretório de imagens PDF")
    
    @field_validator('log_dir', 'temp_dir', 'pdf_images_dir')
    @classmethod
    def ensure_directories_exist(cls, v, info):
        workspace_root = info.data.get('workspace_root', Path("/workspaces/rag"))
        if not v.is_absolute():
            v = workspace_root / v
        v.mkdir(exist_ok=True, parents=True)
        return v
    
    @property
    def multiagent_src_path(self) -> Path:
        """Caminho para o código fonte do multi-agent-researcher"""
        return self.workspace_root / "multi-agent-researcher" / "src"
    
    @property
    def maintenance_path(self) -> Path:
        """Caminho para scripts de manutenção"""
        return self.workspace_root / "maintenance"


class APIConfig:
    """Configuração principal da API agregando todas as subconfigs"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.ai = AIConfig()
        self.security = SecurityConfig()
        self.server = ServerConfig()
        self.production = ProductionConfig()
        self.paths = PathConfig()
    
    def validate_all(self) -> Dict[str, Any]:
        """Valida todas as configurações e retorna status"""
        try:
            return {
                "valid": True,
                "database_valid": bool(self.database.astra_db_api_endpoint and self.database.astra_db_application_token),
                "ai_valid": bool(self.ai.openai_api_key and self.ai.voyage_api_key),
                "security_configured": bool(self.security.bearer_token) if self.production.production_mode else True,
                "paths_valid": all([
                    self.paths.workspace_root.exists(),
                    self.paths.log_dir.exists(),
                    self.paths.temp_dir.exists()
                ])
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Retorna resumo do ambiente configurado"""
        return {
            "production_mode": self.production.production_mode,
            "server": f"{self.server.host}:{self.server.port}",
            "log_level": self.server.log_level,
            "cors_enabled": self.security.enable_cors,
            "rate_limiting": self.security.enable_rate_limiting,
            "metrics_enabled": self.production.enable_metrics,
            "ai_model": self.ai.openai_model,
            "embedding_model": self.ai.embedding_model
        }


# Instância global da configuração
config = APIConfig()
