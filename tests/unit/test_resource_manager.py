"""Testes unitários para o módulo de gerenciamento de recursos."""

import pytest
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, call
from utils.resource_manager import cleanup_temp_files, ResourceManager


@pytest.mark.unit
class TestCleanupTempFiles:
    """Testes para a função cleanup_temp_files."""
    
    def test_cleanup_old_files(self, temp_dir):
        """Testa limpeza de arquivos antigos."""
        # Cria arquivos de teste
        old_file = Path(temp_dir) / "old_file.txt"
        new_file = Path(temp_dir) / "new_file.txt"
        
        old_file.write_text("old content")
        new_file.write_text("new content")
        
        # Modifica o tempo de modificação do arquivo antigo
        old_time = time.time() - (25 * 3600)  # 25 horas atrás
        os.utime(old_file, (old_time, old_time))
        
        # Executa limpeza
        deleted = cleanup_temp_files(temp_dir, max_age_hours=24)
        
        # Verifica resultados
        assert str(old_file) in deleted
        assert not old_file.exists()
        assert new_file.exists()
        assert len(deleted) == 1
    
    def test_cleanup_with_pattern(self, temp_dir):
        """Testa limpeza com padrão específico."""
        # Cria arquivos de diferentes tipos
        txt_file = Path(temp_dir) / "old.txt"
        py_file = Path(temp_dir) / "old.py"
        
        txt_file.write_text("content")
        py_file.write_text("content")
        
        # Torna ambos antigos
        old_time = time.time() - (25 * 3600)
        os.utime(txt_file, (old_time, old_time))
        os.utime(py_file, (old_time, old_time))
        
        # Limpa apenas arquivos .txt
        deleted = cleanup_temp_files(temp_dir, pattern="*.txt", max_age_hours=24)
        
        assert str(txt_file) in deleted
        assert str(py_file) not in deleted
        assert not txt_file.exists()
        assert py_file.exists()
    
    def test_cleanup_no_old_files(self, temp_dir):
        """Testa limpeza quando não há arquivos antigos."""
        # Cria arquivo recente
        recent_file = Path(temp_dir) / "recent.txt"
        recent_file.write_text("content")
        
        deleted = cleanup_temp_files(temp_dir, max_age_hours=24)
        
        assert deleted == []
        assert recent_file.exists()
    
    def test_cleanup_empty_directory(self, temp_dir):
        """Testa limpeza em diretório vazio."""
        deleted = cleanup_temp_files(temp_dir, max_age_hours=24)
        assert deleted == []
    
    def test_cleanup_nonexistent_directory(self):
        """Testa limpeza em diretório inexistente."""
        deleted = cleanup_temp_files("/nonexistent/path", max_age_hours=24)
        assert deleted == []
    
    def test_cleanup_with_permission_error(self, temp_dir):
        """Testa limpeza com erro de permissão."""
        # Cria arquivo antigo
        old_file = Path(temp_dir) / "protected.txt"
        old_file.write_text("content")
        
        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))
        
        # Mock os.remove para simular erro de permissão
        with patch('os.remove', side_effect=PermissionError("Access denied")):
            with patch('utils.resource_manager.logger') as mock_logger:
                deleted = cleanup_temp_files(temp_dir, max_age_hours=24)
                
                assert deleted == []
                mock_logger.warning.assert_called_once()
    
    def test_cleanup_logs_deleted_files(self, temp_dir):
        """Testa se a limpeza registra arquivos deletados."""
        old_file = Path(temp_dir) / "log_test.txt"
        old_file.write_text("content")
        
        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))
        
        with patch('utils.resource_manager.logger') as mock_logger:
            cleanup_temp_files(temp_dir, max_age_hours=24)
            mock_logger.info.assert_called_once()
            assert "removido" in mock_logger.info.call_args[0][0]


@pytest.mark.unit
class TestResourceManager:
    """Testes para a classe ResourceManager."""
    
    def test_initialization(self, temp_dir):
        """Testa inicialização do ResourceManager."""
        manager = ResourceManager(temp_dir)
        assert manager.base_dir == temp_dir
        assert os.path.exists(temp_dir)
    
    def test_initialization_creates_directory(self):
        """Testa se a inicialização cria diretório inexistente."""
        with tempfile.TemporaryDirectory() as parent_dir:
            new_dir = os.path.join(parent_dir, "new_subdir")
            assert not os.path.exists(new_dir)
            
            manager = ResourceManager(new_dir)
            assert os.path.exists(new_dir)
            assert manager.base_dir == new_dir
    
    def test_cleanup_calls_cleanup_temp_files(self, temp_dir):
        """Testa se cleanup chama a função cleanup_temp_files."""
        manager = ResourceManager(temp_dir)
        
        with patch('utils.resource_manager.cleanup_temp_files') as mock_cleanup:
            manager.cleanup(max_age_hours=48)
            mock_cleanup.assert_called_once_with(temp_dir, max_age_hours=48)
    
    def test_cleanup_default_max_age(self, temp_dir):
        """Testa cleanup com valor padrão de max_age_hours."""
        manager = ResourceManager(temp_dir)
        
        with patch('utils.resource_manager.cleanup_temp_files') as mock_cleanup:
            manager.cleanup()
            mock_cleanup.assert_called_once_with(temp_dir, max_age_hours=24)
    
    def test_multiple_managers_same_directory(self, temp_dir):
        """Testa múltiplos managers no mesmo diretório."""
        manager1 = ResourceManager(temp_dir)
        manager2 = ResourceManager(temp_dir)
        
        assert manager1.base_dir == manager2.base_dir
        assert os.path.exists(temp_dir)
    
    def test_nested_directory_creation(self):
        """Testa criação de diretórios aninhados."""
        with tempfile.TemporaryDirectory() as parent_dir:
            nested_path = os.path.join(parent_dir, "level1", "level2", "level3")
            
            manager = ResourceManager(nested_path)
            assert os.path.exists(nested_path)
            assert manager.base_dir == nested_path
    
    def test_ensure_dirs_idempotent(self, temp_dir):
        """Testa se _ensure_dirs é idempotente."""
        manager = ResourceManager(temp_dir)
        
        # Chama múltiplas vezes - não deve causar erro
        manager._ensure_dirs()
        manager._ensure_dirs()
        manager._ensure_dirs()
        
        assert os.path.exists(temp_dir)


@pytest.mark.unit
class TestIntegration:
    """Testes de integração entre componentes do resource_manager."""
    
    def test_full_workflow(self, temp_dir):
        """Testa fluxo completo de uso do ResourceManager."""
        manager = ResourceManager(temp_dir)
        
        # Cria arquivos de teste
        old_file = Path(temp_dir) / "old_temp.log"
        new_file = Path(temp_dir) / "new_temp.log"
        
        old_file.write_text("old log")
        new_file.write_text("new log")
        
        # Torna um arquivo antigo
        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))
        
        # Executa limpeza
        manager.cleanup(max_age_hours=24)
        
        # Verifica resultados
        assert not old_file.exists()
        assert new_file.exists()
    
    def test_resource_manager_with_patterns(self, temp_dir):
        """Testa ResourceManager com patterns customizados."""
        manager = ResourceManager(temp_dir)
        
        # Cria diferentes tipos de arquivos
        files = [
            Path(temp_dir) / "temp.log",
            Path(temp_dir) / "cache.tmp",
            Path(temp_dir) / "data.json"
        ]
        
        for file in files:
            file.write_text("content")
            old_time = time.time() - (25 * 3600)
            os.utime(file, (old_time, old_time))
        
        # Test cleanup with specific pattern through direct function call
        # (ResourceManager doesn't expose pattern parameter, but we can test the underlying function)
        deleted_logs = cleanup_temp_files(temp_dir, pattern="*.log", max_age_hours=24)
        
        assert any("temp.log" in path for path in deleted_logs)
        assert len(deleted_logs) == 1
