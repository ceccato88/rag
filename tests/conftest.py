"""Configuração global de testes e fixtures compartilhadas."""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, Generator
from dataclasses import dataclass
from PIL import Image
import json

# Adiciona o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurações de teste
TEST_ENV_VARS = {
    "ASTRA_DB_API_ENDPOINT": "test_endpoint",
    "ASTRA_DB_APPLICATION_TOKEN": "test_token",
    "VOYAGE_API_KEY": "test_voyage_key",
    "OPENAI_API_KEY": "test_openai_key",
}

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configura o ambiente de teste global."""
    # Aplica variáveis de ambiente de teste
    original_env = {}
    for key, value in TEST_ENV_VARS.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restaura variáveis originais
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def sample_image():
    """Cria uma imagem de teste."""
    img = Image.new('RGB', (100, 100), color='red')
    return img

@pytest.fixture
def sample_document():
    """Documento de exemplo para testes."""
    return {
        'id': 'test_doc_1',
        'page_num': 1,
        'markdown_text': '# Test Document\n\nThis is a test document with some content.',
        'image_path': '/test/path/image.png',
        'doc_source': 'test_source.pdf'
    }

@pytest.fixture
def sample_embedding():
    """Embedding de exemplo para testes."""
    return [0.1] * 1024  # Embedding de 1024 dimensões

@pytest.fixture
def mock_config():
    """Configuração mockada para testes."""
    from indexer import Config
    return Config(
        PDF_URL="test://example.pdf",
        IMAGE_DIR="test_images",
        CONCURRENCY=2,
        BATCH_SIZE=10,
        MAX_RETRIES=1,
        RETRY_DELAY=0.1,
        DOWNLOAD_TIMEOUT=5
    )

@pytest.fixture
def mock_voyage_client():
    """Mock do cliente Voyage AI."""
    mock = Mock()
    mock.embed.return_value.embeddings = [[0.1] * 1024]
    return mock

@pytest.fixture
def mock_astra_collection():
    """Mock da collection do Astra DB."""
    mock = Mock()
    mock.insert_many.return_value = Mock(inserted_ids=['id1', 'id2'])
    mock.find.return_value = [
        {'_id': 'id1', 'page_num': 1, 'markdown_text': 'Test content'},
        {'_id': 'id2', 'page_num': 2, 'markdown_text': 'More content'}
    ]
    return mock

@pytest.fixture
def mock_openai_client():
    """Mock do cliente OpenAI."""
    mock = Mock()
    mock.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content="Mocked response"))
    ]
    return mock

@pytest.fixture
def sample_pdf_path(temp_dir):
    """Cria um arquivo PDF simulado para testes."""
    pdf_path = Path(temp_dir) / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")
    return str(pdf_path)

@pytest.fixture
def sample_test_questions():
    """Perguntas de teste para avaliação."""
    return [
        {
            "id": "q1",
            "question": "What is machine learning?",
            "expected_pages": [1, 2],
            "expected_keywords": ["machine", "learning", "algorithm"],
            "category": "conceptual",
            "difficulty": "easy"
        },
        {
            "id": "q2", 
            "question": "How does gradient descent work?",
            "expected_pages": [5, 6],
            "expected_keywords": ["gradient", "descent", "optimization"],
            "category": "technical",
            "difficulty": "medium"
        }
    ]

@pytest.fixture
def mock_pymupdf_document():
    """Mock de um documento PyMuPDF."""
    mock_doc = Mock()
    mock_doc.page_count = 3
    
    # Mock das páginas
    mock_pages = []
    for i in range(3):
        mock_page = Mock()
        mock_page.number = i
        mock_page.get_pixmap.return_value = Mock()
        mock_pages.append(mock_page)
    
    mock_doc.__iter__ = lambda self: iter(mock_pages)
    mock_doc.__getitem__ = lambda self, idx: mock_pages[idx]
    
    return mock_doc

@pytest.fixture
def mock_requests_response():
    """Mock de resposta HTTP do requests."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/pdf'}
    mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
    mock_response.raise_for_status.return_value = None
    return mock_response

class TestMetrics:
    """Classe auxiliar para coletar métricas de teste."""
    
    def __init__(self):
        self.errors = []
        self.performance_data = {}
    
    def add_error(self, test_name: str, error: str):
        self.errors.append({"test": test_name, "error": error})
    
    def add_performance(self, test_name: str, duration: float):
        self.performance_data[test_name] = duration
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_errors": len(self.errors),
            "errors": self.errors,
            "performance": self.performance_data
        }

@pytest.fixture
def test_metrics():
    """Fixture para coletar métricas durante os testes."""
    return TestMetrics()

# Marks personalizados
def pytest_configure(config):
    """Configura marks personalizados."""
    config.addinivalue_line("markers", "unit: marca testes unitários")
    config.addinivalue_line("markers", "integration: marca testes de integração") 
    config.addinivalue_line("markers", "functional: marca testes funcionais")
    config.addinivalue_line("markers", "slow: marca testes que demoram mais para executar")
    config.addinivalue_line("markers", "external: marca testes que dependem de recursos externos")
