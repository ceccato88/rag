"""Testes unitários para o módulo indexer.py."""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from PIL import Image
import requests

from indexer import (
    Config, get_config, create_doc_source_name, pixel_token_count,
    text_token_estimate, fits_limits, download_pdf_with_retry,
    connect_to_astra
)


@pytest.mark.unit
class TestConfig:
    """Testes para a classe Config."""
    
    def test_default_config_values(self):
        """Testa valores padrão da configuração."""
        config = Config()
        
        assert config.PDF_URL == "https://arxiv.org/pdf/2501.13956"
        assert config.IMAGE_DIR == "pdf_images"
        assert config.VOYAGE_EMBEDDING_DIM == 1024
        assert config.MAX_TOKENS_PER_INPUT == 32_000
        assert config.TOKENS_PER_PIXEL == 1 / 560
        assert config.TOKEN_CHARS_RATIO == 4
        assert config.CONCURRENCY == 5
        assert config.ERROR_ON_LIMIT is True
        assert config.BATCH_SIZE == 100
        assert config.COLLECTION_NAME == "pdf_documents"
        assert config.DOWNLOAD_TIMEOUT == 30
        assert config.DOWNLOAD_CHUNK_SIZE == 8192
        assert config.PIXMAP_SCALE == 2
        assert config.MAX_RETRIES == 3
        assert config.RETRY_DELAY == 1.0
        assert config.CLEANUP_MAX_AGE == 24
    
    def test_custom_config_values(self):
        """Testa configuração com valores customizados."""
        config = Config(
            PDF_URL="custom_url",
            CONCURRENCY=10,
            BATCH_SIZE=50
        )
        
        assert config.PDF_URL == "custom_url"
        assert config.CONCURRENCY == 10
        assert config.BATCH_SIZE == 50
        # Outros valores devem permanecer padrão
        assert config.VOYAGE_EMBEDDING_DIM == 1024


@pytest.mark.unit
class TestGetConfig:
    """Testes para a função get_config."""
    
    def test_get_config_default(self):
        """Testa get_config sem variável de ambiente."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config()
            assert config.PDF_URL == "https://arxiv.org/pdf/2501.13956"
    
    def test_get_config_with_env_var(self):
        """Testa get_config com variável de ambiente."""
        test_url = "https://custom.example.com/test.pdf"
        with patch.dict(os.environ, {"PDF_URL": test_url}):
            config = get_config()
            assert config.PDF_URL == test_url


@pytest.mark.unit
class TestHelperFunctions:
    """Testes para funções auxiliares."""
    
    @pytest.mark.parametrize("url,expected", [
        ("https://example.com/paper.pdf", "paper"),
        ("https://arxiv.org/pdf/2501.13956.pdf", "2501.13956"),
        ("file with spaces.pdf", "file_with_spaces"),
        ("special-chars@#$.pdf", "special-chars___"),
        ("no_extension", "no_extension"),
        ("multiple.dots.in.name.pdf", "multiple.dots.in.name")
    ])
    def test_create_doc_source_name(self, url, expected):
        """Testa criação de nome de fonte do documento."""
        result = create_doc_source_name(url)
        assert result == expected
    
    def test_pixel_token_count(self, mock_config):
        """Testa contagem de tokens por pixel."""
        img = Image.new('RGB', (100, 200), color='red')  # 100x200 pixels
        
        result = pixel_token_count(img, mock_config)
        expected = int((100 * 200) * mock_config.TOKENS_PER_PIXEL)
        assert result == expected
    
    def test_text_token_estimate(self, mock_config):
        """Testa estimativa de tokens para texto."""
        text = "A" * 100  # 100 caracteres
        
        result = text_token_estimate(text, mock_config)
        expected = max(1, 100 // mock_config.TOKEN_CHARS_RATIO)
        assert result == expected
    
    def test_text_token_estimate_minimum(self, mock_config):
        """Testa que a estimativa retorna pelo menos 1 token."""
        text = "A"  # 1 caractere
        
        result = text_token_estimate(text, mock_config)
        assert result == 1  # Sempre pelo menos 1
    
    def test_fits_limits_true(self, mock_config):
        """Testa fits_limits quando está dentro do limite."""
        text = "A" * 10  # Poucos caracteres
        img = Image.new('RGB', (10, 10), color='red')  # Imagem pequena
        
        result = fits_limits(text, img, mock_config)
        assert result is True
    
    def test_fits_limits_false(self, mock_config):
        """Testa fits_limits quando excede o limite."""
        # Configura limite baixo para teste
        mock_config.MAX_TOKENS_PER_INPUT = 10
        
        text = "A" * 100  # Muitos caracteres
        img = Image.new('RGB', (1000, 1000), color='red')  # Imagem grande
        
        result = fits_limits(text, img, mock_config)
        assert result is False


@pytest.mark.unit
class TestDownloadPdfWithRetry:
    """Testes para a função download_pdf_with_retry."""
    
    def test_download_local_file_success(self, mock_config, sample_pdf_path):
        """Testa abertura de arquivo PDF local."""
        with patch('indexer.pymupdf.open') as mock_open:
            mock_doc = Mock()
            mock_doc.page_count = 5
            mock_open.return_value = mock_doc
            
            result = download_pdf_with_retry(sample_pdf_path, mock_config)
            
            assert result == mock_doc
            mock_open.assert_called_once_with(sample_pdf_path)
    
    def test_download_local_file_not_found(self, mock_config):
        """Testa erro quando arquivo local não existe."""
        non_existent_path = "/path/that/does/not/exist.pdf"
        
        result = download_pdf_with_retry(non_existent_path, mock_config)
        assert result is None
    
    def test_download_url_success(self, mock_config, mock_requests_response):
        """Testa download de URL com sucesso."""
        url = "https://example.com/test.pdf"
        
        with patch('indexer.requests.get') as mock_get:
            mock_get.return_value.__enter__.return_value = mock_requests_response
            
            with patch('indexer.pymupdf.open') as mock_open:
                mock_doc = Mock()
                mock_doc.page_count = 3
                mock_open.return_value = mock_doc
                
                result = download_pdf_with_retry(url, mock_config)
                
                assert result == mock_doc
                mock_get.assert_called_once_with(
                    url, stream=True, timeout=mock_config.DOWNLOAD_TIMEOUT
                )
    
    def test_download_url_retry_on_failure(self, mock_config):
        """Testa retry em caso de falha no download."""
        url = "https://example.com/test.pdf"
        
        with patch('indexer.requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection failed")
            
            with patch('indexer.time.sleep') as mock_sleep:
                result = download_pdf_with_retry(url, mock_config)
                
                assert result is None
                assert mock_get.call_count == mock_config.MAX_RETRIES
                # O sleep é chamado apenas quando não é a última tentativa
                # Se MAX_RETRIES = 1, não há sleep; se = 3, há 2 sleeps
                expected_sleeps = max(0, mock_config.MAX_RETRIES - 1)
                assert mock_sleep.call_count == expected_sleeps
    
    def test_download_url_success_after_retry(self, mock_requests_response):
        """Testa sucesso após algumas tentativas."""
        # Configuração que permite múltiplas tentativas
        config = Config(MAX_RETRIES=3, RETRY_DELAY=0.1)
        url = "https://example.com/test.pdf"
        
        with patch('indexer.requests.get') as mock_get:
            # Primeira tentativa falha, segunda sucesso
            mock_get.side_effect = [
                requests.RequestException("Temporary error"),
                mock_requests_response
            ]
            # Configura o context manager
            mock_requests_response.__enter__ = Mock(return_value=mock_requests_response)
            mock_requests_response.__exit__ = Mock(return_value=None)
            
            with patch('indexer.pymupdf.open') as mock_open:
                mock_doc = Mock()
                mock_open.return_value = mock_doc
                
                with patch('indexer.time.sleep'):
                    result = download_pdf_with_retry(url, config)
                    
                    assert result == mock_doc
                    assert mock_get.call_count == 2
    
    def test_download_invalid_url_format(self, mock_config):
        """Testa tratamento de formato de URL inválido."""
        invalid_input = "not_a_url_or_path"
        
        result = download_pdf_with_retry(invalid_input, mock_config)
        assert result is None


@pytest.mark.unit
class TestConnectToAstra:
    """Testes para a função connect_to_astra."""
    
    def test_connect_missing_env_vars(self, mock_config):
        """Testa conexão sem variáveis de ambiente."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="Variáveis ASTRA_DB_API_ENDPOINT"):
                connect_to_astra(mock_config)
    
    def test_connect_success_existing_collection(self, mock_config):
        """Testa conexão com collection existente."""
        with patch.dict(os.environ, {
            "ASTRA_DB_API_ENDPOINT": "test_endpoint",
            "ASTRA_DB_APPLICATION_TOKEN": "test_token"
        }):
            with patch('indexer.DataAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_database = Mock()
                mock_collection = Mock()
                
                mock_client_class.return_value = mock_client
                mock_client.get_database.return_value = mock_database
                mock_database.list_collection_names.return_value = [mock_config.COLLECTION_NAME]
                mock_database.get_collection.return_value = mock_collection
                mock_database.info.return_value = Mock(name="test_db")
                
                result = connect_to_astra(mock_config)
                
                assert result == mock_collection
                mock_database.get_collection.assert_called_once_with(mock_config.COLLECTION_NAME)
    
    def test_connect_success_create_new_collection(self, mock_config):
        """Testa conexão criando nova collection."""
        with patch.dict(os.environ, {
            "ASTRA_DB_API_ENDPOINT": "test_endpoint", 
            "ASTRA_DB_APPLICATION_TOKEN": "test_token"
        }):
            with patch('indexer.DataAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_database = Mock()
                mock_collection = Mock()
                
                mock_client_class.return_value = mock_client
                mock_client.get_database.return_value = mock_database
                mock_database.list_collection_names.return_value = []  # Collection não existe
                mock_database.create_collection.return_value = mock_collection
                mock_database.get_collection.return_value = mock_collection
                mock_database.info.return_value = Mock(name="test_db")
                
                result = connect_to_astra(mock_config)
                
                assert result == mock_collection
                mock_database.create_collection.assert_called_once()
                mock_database.get_collection.assert_called_once_with(mock_config.COLLECTION_NAME)
    
    def test_connect_database_error(self, mock_config):
        """Testa erro na conexão com database."""
        with patch.dict(os.environ, {
            "ASTRA_DB_API_ENDPOINT": "test_endpoint",
            "ASTRA_DB_APPLICATION_TOKEN": "test_token"
        }):
            with patch('indexer.DataAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client.get_database.side_effect = Exception("Database connection failed")
                mock_client_class.return_value = mock_client
                
                with pytest.raises(Exception, match="Database connection failed"):
                    connect_to_astra(mock_config)
