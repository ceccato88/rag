"""Testes unitários para o módulo de métricas."""

import pytest
import time
from unittest.mock import Mock, patch
from utils.metrics import ProcessingMetrics, measure_time


@pytest.mark.unit
class TestProcessingMetrics:
    """Testes para a classe ProcessingMetrics."""
    
    def test_initialization(self):
        """Testa inicialização da classe."""
        metrics = ProcessingMetrics()
        assert isinstance(metrics.start_time, float)
        assert metrics.end_time is None
        assert metrics.steps == {}
        assert metrics.total_duration > 0  # Deve ser positivo
    
    def test_add_step(self):
        """Testa adição de etapas."""
        metrics = ProcessingMetrics()
        metrics.add_step("download", 1.5)
        metrics.add_step("process", 2.3)
        
        assert metrics.steps["download"] == 1.5
        assert metrics.steps["process"] == 2.3
        assert len(metrics.steps) == 2
    
    def test_finish(self):
        """Testa finalização do processamento."""
        metrics = ProcessingMetrics()
        time.sleep(0.01)  # Pequena pausa para garantir diferença de tempo
        metrics.finish()
        
        assert metrics.end_time is not None
        assert metrics.end_time > metrics.start_time
    
    def test_total_duration_before_finish(self):
        """Testa duração total antes de finalizar."""
        metrics = ProcessingMetrics()
        time.sleep(0.01)
        duration = metrics.total_duration
        
        assert duration > 0
        assert metrics.end_time is None  # Ainda não finalizado
    
    def test_total_duration_after_finish(self):
        """Testa duração total após finalizar."""
        metrics = ProcessingMetrics()
        time.sleep(0.01)
        metrics.finish()
        duration = metrics.total_duration
        
        assert duration > 0
        assert duration == metrics.end_time - metrics.start_time
    
    def test_log_summary(self):
        """Testa o log de resumo das métricas."""
        metrics = ProcessingMetrics()
        metrics.add_step("step1", 1.2)
        metrics.add_step("step2", 0.8)
        metrics.finish()
        
        with patch('utils.metrics.logger') as mock_logger:
            metrics.log_summary()
            
            # Verifica se o logger foi chamado
            assert mock_logger.info.call_count >= 3  # Pelo menos 3 chamadas
            
            # Verifica conteúdo das chamadas
            calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Resumo do processamento" in call for call in calls)
            assert any("Tempo total" in call for call in calls)
            assert any("step1" in call for call in calls)
            assert any("step2" in call for call in calls)
    
    def test_multiple_add_step_same_name(self):
        """Testa múltiplas adições com o mesmo nome (sobrescreve)."""
        metrics = ProcessingMetrics()
        metrics.add_step("test", 1.0)
        metrics.add_step("test", 2.0)
        
        assert metrics.steps["test"] == 2.0
        assert len(metrics.steps) == 1


@pytest.mark.unit
class TestMeasureTime:
    """Testes para o context manager measure_time."""
    
    def test_measure_time_success(self):
        """Testa medição de tempo com sucesso."""
        metrics = ProcessingMetrics()
        
        with measure_time(metrics, "test_operation"):
            time.sleep(0.01)  # Simula operação
        
        assert "test_operation" in metrics.steps
        assert metrics.steps["test_operation"] > 0
    
    def test_measure_time_with_exception(self):
        """Testa medição de tempo quando ocorre exceção."""
        metrics = ProcessingMetrics()
        
        with pytest.raises(ValueError):
            with measure_time(metrics, "failing_operation"):
                time.sleep(0.01)
                raise ValueError("Test error")
        
        # Mesmo com exceção, o tempo deve ser registrado
        assert "failing_operation" in metrics.steps
        assert metrics.steps["failing_operation"] > 0
    
    def test_measure_time_accuracy(self):
        """Testa precisão da medição de tempo."""
        metrics = ProcessingMetrics()
        expected_duration = 0.05  # 50ms
        
        with measure_time(metrics, "timed_operation"):
            time.sleep(expected_duration)
        
        # Verifica se a duração está aproximadamente correta (±20ms de tolerância)
        actual_duration = metrics.steps["timed_operation"]
        assert abs(actual_duration - expected_duration) < 0.02
    
    def test_measure_time_multiple_operations(self):
        """Testa medição de múltiplas operações."""
        metrics = ProcessingMetrics()
        
        with measure_time(metrics, "op1"):
            time.sleep(0.01)
        
        with measure_time(metrics, "op2"):
            time.sleep(0.02)
        
        with measure_time(metrics, "op3"):
            time.sleep(0.01)
        
        assert len(metrics.steps) == 3
        assert metrics.steps["op1"] > 0
        assert metrics.steps["op2"] > 0
        assert metrics.steps["op3"] > 0
        # op2 deve ser maior que op1 e op3
        assert metrics.steps["op2"] > metrics.steps["op1"]
        assert metrics.steps["op2"] > metrics.steps["op3"]
    
    def test_nested_measure_time(self):
        """Testa medições de tempo aninhadas."""
        metrics = ProcessingMetrics()
        
        with measure_time(metrics, "outer"):
            time.sleep(0.01)
            with measure_time(metrics, "inner"):
                time.sleep(0.01)
            time.sleep(0.01)
        
        assert "outer" in metrics.steps
        assert "inner" in metrics.steps
        assert metrics.steps["outer"] > metrics.steps["inner"]
    
    def test_measure_time_zero_duration(self):
        """Testa medição com duração muito pequena."""
        metrics = ProcessingMetrics()
        
        with measure_time(metrics, "instant"):
            pass  # Operação instantânea
        
        assert "instant" in metrics.steps
        assert metrics.steps["instant"] >= 0  # Pode ser 0 ou muito pequeno
