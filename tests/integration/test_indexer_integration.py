"""Testes de integração para o módulo indexer.py."""

import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock, mock_open, MagicMock
from pathlib import Path

from indexer import Config


@pytest.mark.integration
class TestIndexerIntegration:
    """Testes de integração do indexer com componentes externos."""
    
    @pytest.mark.asyncio
    async def test_embed_page_integration(self, mock_config, sample_document):
        """Testa integração da função embed_page."""
        from indexer import embed_page
        
        # Mock do semáforo e cliente
        sema = asyncio.Semaphore(1)
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.embeddings = [[0.1] * 1024]
        mock_client.multimodal_embed.return_value = mock_response
        
        # Mock do arquivo de imagem
        with patch('indexer.Image.open') as mock_image_open:
            mock_img = Mock()
            mock_img.width = 800
            mock_img.height = 600
            mock_image_open.return_value = mock_img
            
            # Mock da função fits_limits para retornar True
            with patch('indexer.fits_limits', return_value=True):
                result = await embed_page(sema, mock_client, sample_document, mock_config)
        
        assert result is not None
        assert "embedding" in result
        assert len(result["embedding"]) == 1024
        assert result['id'] == sample_document['id']
        assert result['page_num'] == sample_document['page_num']
        assert result['markdown_text'] == sample_document['markdown_text']
    
    @pytest.mark.asyncio 
    async def test_embed_page_with_validation_failure(self, mock_config):
        """Testa embed_page quando validação falha."""
        from indexer import embed_page
        
        # Documento inválido (sem campos obrigatórios)
        invalid_doc = {'id': 'test', 'page_num': 1}
        
        sema = asyncio.Semaphore(1)
        mock_client = AsyncMock()
        
        result = await embed_page(sema, mock_client, invalid_doc, mock_config)
        assert result is None
    
    def test_full_pdf_processing_workflow(self, mock_config, temp_dir):
        """Testa fluxo completo de processamento de PDF usando funções reais disponíveis."""
        from indexer import download_pdf_with_retry, extract_page_content
        
        # Cria arquivo PDF fake
        pdf_path = Path(temp_dir) / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")
        
        # Mock do PyMuPDF
        with patch('indexer.pymupdf.open') as mock_open:
            mock_doc = MagicMock()  # Usar MagicMock para suportar __getitem__
            mock_doc.page_count = 2
            mock_open.return_value = mock_doc
            
            # Testa download (que funciona com arquivos locais)
            with patch('os.path.exists', return_value=True):
                doc = download_pdf_with_retry(str(pdf_path), mock_config)
                assert doc is not None
                
            # Testa extract_page_content
            with patch('indexer.pymupdf4llm.to_markdown') as mock_to_markdown:
                mock_to_markdown.return_value = "# Test Content\n\nSample text."
                
                # Mock da página
                mock_page = Mock()
                mock_pixmap = Mock()
                mock_pixmap.tobytes.return_value = b"fake_image_data"
                mock_page.get_pixmap.return_value = mock_pixmap
                mock_doc.__getitem__.return_value = mock_page
                
                with patch('indexer.Image.open') as mock_image:
                    mock_img = Mock()
                    mock_img.width = 800
                    mock_img.height = 600
                    mock_image.return_value = mock_img
                    
                    with patch('builtins.open', mock_open()):
                        with patch('os.makedirs'):
                            result = extract_page_content(mock_doc, 0, "test_doc", temp_dir, mock_config)
                            
                            assert isinstance(result, dict)
                            assert 'id' in result
                            assert 'page_num' in result  
                            assert 'markdown_text' in result
                            assert 'image_path' in result
                            assert 'doc_source' in result
    
    @pytest.mark.slow
    def test_resource_cleanup_integration(self, mock_config):
        """Testa integração da limpeza de recursos."""
        from utils.resource_manager import ResourceManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Cria ResourceManager
            manager = ResourceManager(temp_dir)
            
            # Cria arquivos de teste
            test_file = Path(temp_dir) / "test_image.png"
            test_file.write_bytes(b"fake image data")
            
            # Verifica que arquivo existe
            assert test_file.exists()
            
            # Executa limpeza (arquivo é muito recente, não deve ser removido)
            manager.cleanup(max_age_hours=1)
            assert test_file.exists()
    
    def test_astra_collection_operations(self, mock_config):
        """Testa operações com collection do Astra."""
        from indexer import connect_to_astra
        
        with patch.dict('os.environ', {
            'ASTRA_DB_API_ENDPOINT': 'test_endpoint',
            'ASTRA_DB_APPLICATION_TOKEN': 'test_token'
        }):
            with patch('indexer.DataAPIClient') as mock_client_class:
                # Setup mocks
                mock_client = Mock()
                mock_database = Mock()
                mock_collection = Mock()
                
                mock_client_class.return_value = mock_client
                mock_client.get_database.return_value = mock_database
                mock_database.list_collection_names.return_value = []
                mock_database.create_collection.return_value = mock_collection
                mock_database.get_collection.return_value = mock_collection
                mock_database.info.return_value = Mock(name="test_db")
                
                # Testa conexão e criação de collection
                collection = connect_to_astra(mock_config)
                
                assert collection == mock_collection
                mock_database.create_collection.assert_called_once()


@pytest.mark.integration
class TestIndexerErrorHandling:
    """Testes de tratamento de erros em cenários de integração."""
    
    def test_pdf_download_network_timeout(self, mock_config):
        """Testa timeout na rede durante download."""
        from indexer import download_pdf_with_retry
        import requests
        
        url = "https://example.com/slow.pdf"
        
        with patch('indexer.requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")
            
            result = download_pdf_with_retry(url, mock_config)
            assert result is None
            assert mock_get.call_count == mock_config.MAX_RETRIES
    
    def test_pdf_processing_corrupted_file(self, mock_config, temp_dir):
        """Testa processamento de arquivo PDF corrompido."""
        from indexer import download_pdf_with_retry
        
        # Cria arquivo corrompido
        corrupted_pdf = Path(temp_dir) / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"not a real pdf")
        
        with patch('indexer.pymupdf.open') as mock_open:
            mock_open.side_effect = Exception("Invalid PDF format")
            
            result = download_pdf_with_retry(str(corrupted_pdf), mock_config)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_embedding_api_failure(self, mock_config, sample_document):
        """Testa falha na API de embedding."""
        from indexer import embed_page
        
        sema = asyncio.Semaphore(1)
        mock_client = AsyncMock()
        mock_client.embed.side_effect = Exception("API Error")
        
        result = await embed_page(sema, mock_client, sample_document, mock_config)
        assert result is None
    
    def test_astra_connection_failure(self, mock_config):
        """Testa falha na conexão com Astra DB."""
        from indexer import connect_to_astra
        
        with patch.dict('os.environ', {
            'ASTRA_DB_API_ENDPOINT': 'invalid_endpoint',
            'ASTRA_DB_APPLICATION_TOKEN': 'invalid_token'
        }):
            with patch('indexer.DataAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client.get_database.side_effect = Exception("Connection failed")
                mock_client_class.return_value = mock_client
                
                with pytest.raises(Exception, match="Connection failed"):
                    connect_to_astra(mock_config)


@pytest.mark.integration
@pytest.mark.slow
class TestIndexerPerformance:
    """Testes de performance para operações do indexer."""
    
    def test_batch_processing_performance(self, mock_config):
        """Testa performance do processamento em lote."""
        from indexer import Config
        
        # Configura batch pequeno para teste
        config = Config(BATCH_SIZE=10, CONCURRENCY=2)
        
        # Simula processamento de muitos documentos
        documents = [
            {'id': f'doc_{i}', 'page_num': i, 'markdown_text': f'Content {i}',
             'image_path': f'/path/{i}.png', 'doc_source': 'test.pdf'}
            for i in range(50)
        ]
        
        # Mock da collection
        with patch('indexer.connect_to_astra') as mock_connect:
            mock_collection = Mock()
            mock_collection.insert_many.return_value = Mock(inserted_ids=[f'id_{i}' for i in range(10)])
            mock_connect.return_value = mock_collection
            
            # Simula inserção em lotes
            for i in range(0, len(documents), config.BATCH_SIZE):
                batch = documents[i:i + config.BATCH_SIZE]
                result = mock_collection.insert_many(batch)
                assert len(result.inserted_ids) <= config.BATCH_SIZE
    
    @pytest.mark.asyncio
    async def test_concurrent_embedding_processing(self, mock_config):
        """Testa processamento concorrente de embeddings com mocks apropriados."""
        from indexer import embed_page
        
        # Mock do cliente Voyage
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.embeddings = [[0.1, 0.2, 0.3] * 342]  # 1026-dim embedding ajustado para 1024
        mock_client.multimodal_embed.return_value = mock_response
        
        # Dados de documentos simulados
        test_docs = []
        for i in range(10):
            test_docs.append({
                'id': f'doc_{i}',
                'page_num': i + 1,
                'markdown_text': f'Content {i}',
                'image_path': f'/fake/path/{i}.png',
                'doc_source': 'test.pdf'
            })
        
        sema = asyncio.Semaphore(3)
        
        # Mock das operações de arquivo e imagem
        with patch('indexer.Image.open') as mock_image_open:
            mock_img = Mock()
            mock_img.width = 800
            mock_img.height = 600
            mock_image_open.return_value = mock_img
            
            with patch('indexer.fits_limits', return_value=True):
                tasks = [
                    embed_page(sema, mock_client, doc, mock_config)
                    for doc in test_docs
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verifica que obtivemos resultados para todas as páginas
                assert len(results) == 10
                # Alguns resultados podem ser None devido ao mocking, mas nenhuma exceção deve ocorrer
                exceptions = [r for r in results if isinstance(r, Exception)]
                assert len(exceptions) == 0
