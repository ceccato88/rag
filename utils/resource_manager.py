"""Gestão de recursos e limpeza."""
import os
import glob
import logging
from typing import List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def cleanup_temp_files(temp_dir: str, pattern: str = "*", max_age_hours: int = 24) -> List[str]:
    """Remove arquivos temporários mais antigos que max_age_hours."""
    deleted_files = []
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    
    for file_path in glob.glob(os.path.join(temp_dir, pattern)):
        try:
            if os.path.getmtime(file_path) < cutoff.timestamp():
                os.remove(file_path)
                deleted_files.append(file_path)
                logger.info(f"Arquivo temporário removido: {file_path}")
        except Exception as e:
            logger.warning(f"Erro ao tentar remover arquivo {file_path}: {e}")
    
    return deleted_files

class ResourceManager:
    """Gerencia recursos como diretórios temporários."""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._ensure_dirs()
    
    def _ensure_dirs(self) -> None:
        """Garante que os diretórios necessários existem."""
        os.makedirs(self.base_dir, exist_ok=True)
    
    def cleanup(self, max_age_hours: int = 24) -> None:
        """Limpa arquivos temporários antigos."""
        cleanup_temp_files(self.base_dir, max_age_hours=max_age_hours)
