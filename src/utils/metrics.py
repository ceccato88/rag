"""Métricas e monitoramento."""
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class ProcessingMetrics:
    """Métricas de processamento do indexador."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    steps: Dict[str, float] = field(default_factory=dict)
    
    def add_step(self, name: str, duration: float) -> None:
        """Adiciona duração de uma etapa."""
        self.steps[name] = duration
    
    def finish(self) -> None:
        """Finaliza o processamento e calcula métricas finais."""
        self.end_time = time.time()
    
    @property
    def total_duration(self) -> float:
        """Duração total do processamento em segundos."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def log_summary(self) -> None:
        """Registra um resumo das métricas."""
        logger.info("📊 Resumo do processamento:")
        logger.info(f"⏱️  Tempo total: {self.total_duration:.2f}s")
        for step, duration in self.steps.items():
            logger.info(f"   {step}: {duration:.2f}s")

@contextmanager
def measure_time(metrics: ProcessingMetrics, step_name: str):
    """Context manager para medir tempo de execução de uma etapa."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        metrics.add_step(step_name, duration)
