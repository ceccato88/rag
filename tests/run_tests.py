"""Script principal para executar todos os testes do projeto RAG."""

import pytest
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_unit_tests():
    """Executa apenas testes unitários."""
    print("🔧 Executando testes unitários...")
    return pytest.main([
        "tests/unit/",
        "-v",
        "--tb=short",
        "-m", "unit"
    ])

def run_integration_tests():
    """Executa testes de integração."""
    print("🔗 Executando testes de integração...")
    return pytest.main([
        "tests/integration/",
        "-v", 
        "--tb=short",
        "-m", "integration"
    ])

def run_functional_tests():
    """Executa testes funcionais."""
    print("⚙️ Executando testes funcionais...")
    return pytest.main([
        "tests/functional/",
        "-v",
        "--tb=short", 
        "-m", "functional"
    ])

def run_all_tests():
    """Executa todos os testes."""
    print("🧪 Executando todos os testes...")
    return pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])

def run_fast_tests():
    """Executa apenas testes rápidos (exclui marcados como slow)."""
    print("⚡ Executando testes rápidos...")
    return pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "-m", "not slow"
    ])

def run_specific_module(module_name):
    """Executa testes de um módulo específico."""
    print(f"🎯 Executando testes para {module_name}...")
    test_patterns = {
        "validation": "tests/unit/test_validation.py",
        "metrics": "tests/unit/test_metrics.py", 
        "resource_manager": "tests/unit/test_resource_manager.py",
        "indexer": "tests/unit/test_indexer.py tests/integration/test_indexer_integration.py",
        "search": "tests/functional/test_search.py",
        "evaluator": "tests/functional/test_evaluator.py"
    }
    
    if module_name not in test_patterns:
        print(f"❌ Módulo '{module_name}' não encontrado.")
        print(f"Módulos disponíveis: {', '.join(test_patterns.keys())}")
        return 1
    
    test_files = test_patterns[module_name].split()
    return pytest.main([
        *test_files,
        "-v",
        "--tb=short"
    ])

def run_with_coverage():
    """Executa testes com relatório de cobertura detalhado."""
    print("📊 Executando testes com análise de cobertura...")
    return pytest.main([
        "tests/",
        "-v",
        "--cov=utils",
        "--cov=indexer", 
        "--cov=search",
        "--cov=evaluator",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-branch"
    ])

def main():
    """Função principal com menu de opções."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unit":
            return run_unit_tests()
        elif command == "integration": 
            return run_integration_tests()
        elif command == "functional":
            return run_functional_tests()
        elif command == "all":
            return run_all_tests()
        elif command == "fast":
            return run_fast_tests()
        elif command == "coverage":
            return run_with_coverage()
        elif command.startswith("module:"):
            module_name = command.split(":", 1)[1]
            return run_specific_module(module_name)
        else:
            print(f"❌ Comando desconhecido: {command}")
            print_help()
            return 1
    else:
        print_help()
        return 0

def print_help():
    """Exibe ajuda sobre os comandos disponíveis."""
    print("""
🧪 Sistema de Testes do Projeto RAG

Uso: python tests/run_tests.py [comando]

Comandos disponíveis:
  unit        - Executa apenas testes unitários
  integration - Executa testes de integração  
  functional  - Executa testes funcionais
  all         - Executa todos os testes
  fast        - Executa testes rápidos (exclui testes marcados como 'slow')
  coverage    - Executa testes com análise de cobertura detalhada
  module:X    - Executa testes de um módulo específico (X = validation, metrics, etc.)

Exemplos:
  python tests/run_tests.py unit
  python tests/run_tests.py module:indexer
  python tests/run_tests.py coverage

Módulos disponíveis para teste específico:
  - validation      (validação de dados)
  - metrics         (métricas e monitoramento)  
  - resource_manager (gestão de recursos)
  - indexer         (indexação de documentos)
  - search          (busca RAG)
  - evaluator       (avaliação do sistema)

Para executar testes com pytest diretamente:
  pytest tests/ -v                    # Todos os testes
  pytest tests/unit/ -m unit         # Apenas unitários
  pytest tests/ -m "not slow"        # Exclui testes lentos
  pytest tests/ --cov=. --cov-report=html  # Com cobertura
    """)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
