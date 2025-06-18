"""Testes unitários para o módulo de validação."""

import pytest
from unittest.mock import Mock, patch
from utils.validation import validate_document, validate_embedding, validate_search_result, validate_query, validate_environment_vars, sanitize_filename, validate_file_path


@pytest.mark.unit
class TestValidateDocument:
    """Testes para a função validate_document."""
    
    def test_valid_document(self, sample_document):
        """Testa validação de documento válido."""
        assert validate_document(sample_document) is True
    
    def test_document_missing_id(self, sample_document):
        """Testa documento sem campo id."""
        del sample_document['id']
        assert validate_document(sample_document) is False
    
    def test_document_missing_page_num(self, sample_document):
        """Testa documento sem campo page_num."""
        del sample_document['page_num']
        assert validate_document(sample_document) is False
    
    def test_document_missing_markdown_text(self, sample_document):
        """Testa documento sem campo markdown_text."""
        del sample_document['markdown_text']
        assert validate_document(sample_document) is False
    
    def test_document_missing_image_path(self, sample_document):
        """Testa documento sem campo image_path."""
        del sample_document['image_path']
        assert validate_document(sample_document) is False
    
    def test_document_missing_doc_source(self, sample_document):
        """Testa documento sem campo doc_source."""
        del sample_document['doc_source']
        assert validate_document(sample_document) is False
    
    def test_empty_document(self):
        """Testa documento vazio."""
        assert validate_document({}) is False
    
    def test_none_document(self):
        """Testa documento None."""
        with pytest.raises(TypeError):
            validate_document(None)
    
    def test_document_with_extra_fields(self, sample_document):
        """Testa documento com campos extras (deve ser válido)."""
        sample_document['extra_field'] = 'extra_value'
        assert validate_document(sample_document) is True


@pytest.mark.unit
class TestValidateEmbedding:
    """Testes para a função validate_embedding."""
    
    def test_valid_embedding(self, sample_embedding):
        """Testa validação de embedding válido."""
        assert validate_embedding(sample_embedding, 1024) is True
    
    def test_wrong_dimension(self, sample_embedding):
        """Testa embedding com dimensão incorreta."""
        assert validate_embedding(sample_embedding, 512) is False
    
    def test_empty_embedding(self):
        """Testa embedding vazio."""
        assert validate_embedding([], 0) is True
        assert validate_embedding([], 1024) is False
    
    def test_non_list_embedding(self):
        """Testa embedding que não é uma lista."""
        with patch('utils.validation.logger') as mock_logger:
            result = validate_embedding("not a list", 1024)
            assert result is False
            mock_logger.error.assert_called_once()
    
    def test_none_embedding(self):
        """Testa embedding None."""
        with patch('utils.validation.logger') as mock_logger:
            result = validate_embedding(None, 1024)
            assert result is False
            mock_logger.error.assert_called_once()
    
    @pytest.mark.parametrize("dimension,expected", [
        (1024, True),
        (512, False),
        (2048, False),
        (1, False),
        (0, False)
    ])
    def test_different_dimensions(self, sample_embedding, dimension, expected):
        """Testa validação com diferentes dimensões."""
        result = validate_embedding(sample_embedding, dimension)
        assert result is expected
    
    def test_negative_dimension(self, sample_embedding):
        """Testa validação com dimensão negativa."""
        assert validate_embedding(sample_embedding, -1) is False
    
    def test_embedding_with_non_numeric_values(self):
        """Testa embedding com valores não numéricos."""
        embedding = ['a', 'b', 'c'] + [0.1] * 1021
        # A função agora valida tipos dos elementos (melhoria de segurança)
        assert validate_embedding(embedding, 1024) is False
    
    def test_logging_on_error(self):
        """Testa se o logging é chamado corretamente em caso de erro."""
        with patch('utils.validation.logger') as mock_logger:
            validate_embedding("invalid", 1024)
            mock_logger.error.assert_called()
            
            validate_embedding([1, 2, 3], 1024)
            # Verifica se o erro de dimensão é logado
            assert mock_logger.error.call_count == 2


@pytest.mark.unit
class TestValidateSearchResult:
    """Testes para a função validate_search_result."""
    
    def test_valid_search_result(self):
        """Testa resultado de busca válido."""
        result = {
            'answer': 'Test answer',
            'candidates': [{'page': 1, 'score': 0.9}],
            'selected_pages': [1, 2]
        }
        assert validate_search_result(result) is True
    
    def test_missing_answer(self):
        """Testa resultado sem answer."""
        result = {
            'candidates': [{'page': 1, 'score': 0.9}],
            'selected_pages': [1, 2]
        }
        assert validate_search_result(result) is False
    
    def test_empty_result(self):
        """Testa resultado vazio."""
        assert validate_search_result({}) is False


@pytest.mark.unit
class TestValidateQuery:
    """Testes para a função validate_query."""
    
    def test_valid_query(self):
        """Testa query válida."""
        assert validate_query("What is machine learning?") is True
    
    def test_empty_query(self):
        """Testa query vazia."""
        assert validate_query("") is False
        assert validate_query("   ") is False
    
    def test_none_query(self):
        """Testa query None."""
        assert validate_query(None) is False
    
    def test_very_short_query(self):
        """Testa query muito curta."""
        assert validate_query("ab") is False
    
    def test_minimum_valid_length(self):
        """Testa comprimento mínimo válido."""
        assert validate_query("abc") is True


@pytest.mark.unit
class TestSanitizeFilename:
    """Testes para a função sanitize_filename."""
    
    def test_valid_filename(self):
        """Testa nome de arquivo já válido."""
        assert sanitize_filename("valid_filename.txt") == "valid_filename.txt"
    
    def test_special_characters(self):
        """Testa remoção de caracteres especiais."""
        assert sanitize_filename("file<>name.txt") == "file_name.txt"
    
    def test_spaces(self):
        """Testa substituição de espaços."""
        assert sanitize_filename("file name.txt") == "file_name.txt"
    
    def test_complex_filename(self):
        """Testa nome de arquivo complexo."""
        result = sanitize_filename('___My <File> "Name" | Test___.txt')
        assert result == "My_File_Name_Test.txt"
