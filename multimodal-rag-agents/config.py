"""Configuration management for multimodal RAG agents."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EnvConfig:
    """Flexible environment configuration loader."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Optional path to .env file. If None, searches automatically.
        """
        self.env_vars = {}
        self.env_file_used = None
        
        if env_file:
            # Use specific file provided
            self._load_env_file(env_file)
        else:
            # Auto-search for .env files
            self._auto_find_env()
    
    def _auto_find_env(self) -> bool:
        """Automatically find .env file in various locations."""
        search_paths = [
            # Current directory
            Path.cwd() / ".env",
            
            # Project root (multimodal-rag-agents directory)
            Path(__file__).parent / ".env",
            
            # Parent directory (useful for development)
            Path(__file__).parent.parent / ".env",
            
            # Home directory
            Path.home() / ".env",
            
            # Common config locations
            Path.home() / ".config" / "multimodal-rag" / ".env",
            Path("/etc/multimodal-rag/.env"),
            
            # Environment variable pointing to config
            Path(os.getenv("RAG_CONFIG_PATH", "")) / ".env" if os.getenv("RAG_CONFIG_PATH") else None,
        ]
        
        # Remove None entries
        search_paths = [p for p in search_paths if p is not None]
        
        for env_path in search_paths:
            if env_path.exists() and env_path.is_file():
                logger.info(f"Found .env file at: {env_path}")
                self._load_env_file(str(env_path))
                return True
        
        logger.warning("No .env file found in search paths")
        logger.info("Searched paths:")
        for path in search_paths:
            logger.info(f"  - {path}")
        
        return False
    
    def _load_env_file(self, env_file: str) -> bool:
        """Load variables from .env file."""
        try:
            env_path = Path(env_file)
            if not env_path.exists():
                logger.error(f"Env file not found: {env_file}")
                return False
            
            self.env_file_used = str(env_path.absolute())
            logger.info(f"Loading environment from: {self.env_file_used}")
            
            with open(env_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        self.env_vars[key] = value
                        # Also set in os.environ for compatibility
                        os.environ[key] = value
                    else:
                        logger.warning(f"Invalid line {line_num} in {env_file}: {line}")
            
            logger.info(f"Loaded {len(self.env_vars)} environment variables")
            return True
            
        except Exception as e:
            logger.error(f"Error loading env file {env_file}: {e}")
            return False
    
    def get_required_vars(self) -> Dict[str, str]:
        """Get required environment variables for RAG system."""
        required = {
            "OPENAI_API_KEY": "OpenAI API key for GPT models",
            "VOYAGE_API_KEY": "Voyage AI API key for multimodal embeddings", 
            "ASTRA_DB_API_ENDPOINT": "Astra DB endpoint URL",
            "ASTRA_DB_APPLICATION_TOKEN": "Astra DB application token"
        }
        
        return {var: desc for var, desc in required.items() if self.get(var)}
    
    def get_missing_vars(self) -> Dict[str, str]:
        """Get missing required environment variables."""
        required = {
            "OPENAI_API_KEY": "OpenAI API key for GPT models",
            "VOYAGE_API_KEY": "Voyage AI API key for multimodal embeddings", 
            "ASTRA_DB_API_ENDPOINT": "Astra DB endpoint URL",
            "ASTRA_DB_APPLICATION_TOKEN": "Astra DB application token"
        }
        
        return {var: desc for var, desc in required.items() if not self.get(var)}
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value."""
        # Priority: 1. Environment variable, 2. Loaded from file, 3. Default
        return os.getenv(key) or self.env_vars.get(key, default)
    
    def is_ready(self) -> bool:
        """Check if all required variables are available."""
        return len(self.get_missing_vars()) == 0
    
    def print_status(self):
        """Print configuration status."""
        print("🔧 Environment Configuration Status")
        print("=" * 50)
        
        if self.env_file_used:
            print(f"📁 Config file: {self.env_file_used}")
        else:
            print("📁 Config file: Not used (using environment variables)")
        
        required_vars = self.get_required_vars()
        missing_vars = self.get_missing_vars()
        
        print(f"✅ Found variables ({len(required_vars)}):")
        for var in required_vars:
            value = self.get(var)
            masked_value = f"{value[:8]}..." if value and len(value) > 8 else "***"
            print(f"   • {var}: {masked_value}")
        
        if missing_vars:
            print(f"\n❌ Missing variables ({len(missing_vars)}):")
            for var, desc in missing_vars.items():
                print(f"   • {var}: {desc}")
            
            print(f"\n💡 Setup options:")
            print(f"1. Create .env file in current directory")
            print(f"2. Create .env file in project root: {Path(__file__).parent}")
            print(f"3. Set environment variables directly:")
            for var in missing_vars:
                print(f"   export {var}='your-{var.lower().replace('_', '-')}'")
            print(f"4. Set RAG_CONFIG_PATH environment variable to config directory")
        else:
            print(f"\n🎉 All required variables found!")
        
        print("=" * 50)


def create_default_env_file(path: Optional[str] = None) -> str:
    """Create a default .env file template."""
    if path is None:
        path = Path.cwd() / ".env"
    else:
        path = Path(path)
    
    template = """# =============================================================================
# MULTIMODAL RAG AGENTS CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# API KEYS (REQUIRED)
# -----------------------------------------------------------------------------
# OpenAI API key for GPT models (get from: https://platform.openai.com/api-keys)
OPENAI_API_KEY=your-openai-api-key-here

# Voyage AI API key for multimodal embeddings (get from: https://www.voyageai.com/)
VOYAGE_API_KEY=your-voyage-api-key-here

# -----------------------------------------------------------------------------
# ASTRA DB CONFIGURATION (REQUIRED)
# -----------------------------------------------------------------------------
# Astra DB endpoint (get from DataStax console)
ASTRA_DB_API_ENDPOINT=https://your-database-id-region.apps.astra.datastax.com

# Astra DB application token (generate in DataStax console)
ASTRA_DB_APPLICATION_TOKEN=AstraCS:your-token-here

# -----------------------------------------------------------------------------
# OPTIONAL CONFIGURATION
# -----------------------------------------------------------------------------
# Collection name in Astra DB (default: pdf_documents)
COLLECTION_NAME=pdf_documents

# Image directory for PDF processing (default: pdf_images)
IMAGE_DIR=pdf_images

# OpenAI model to use (default: gpt-4o)
LLM_MODEL=gpt-4o

# Maximum candidates for retrieval (default: 5)
MAX_CANDIDATES=5

# Processing timeouts and limits
MAX_TOKENS_ANSWER=2048
MAX_TOKENS_RERANK=512
CONCURRENCY=5
BATCH_SIZE=100
"""
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"✅ Created .env template at: {path}")
        print(f"📝 Please edit the file and add your API keys")
        return str(path)
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return ""


# Global configuration instance
config = EnvConfig()


def get_config() -> EnvConfig:
    """Get the global configuration instance."""
    return config


def reload_config(env_file: Optional[str] = None) -> EnvConfig:
    """Reload configuration from file."""
    global config
    config = EnvConfig(env_file)
    return config


if __name__ == "__main__":
    # Test configuration
    print("Testing environment configuration...")
    config.print_status()
    
    if not config.is_ready():
        print("\n❓ Would you like to create a .env template? (y/n)")
        response = input().lower().strip()
        if response in ['y', 'yes']:
            create_default_env_file()