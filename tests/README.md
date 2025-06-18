# Estrutura de Testes do Projeto RAG

Este documento descreve a estrutura de testes implementada para o projeto RAG (Retrieval-Augmented Generation).

## 📁 Estrutura de Diretórios

```
tests/
├── conftest.py                     # Configuração global e fixtures compartilhadas
├── run_tests.py                    # Script principal para executar testes
├── fixtures/
│   └── test_data.py                # Dados de teste reutilizáveis
├── unit/                           # Testes unitários
│   ├── test_validation.py          # Testes para utils/validation.py
│   ├── test_metrics.py             # Testes para utils/metrics.py
│   ├── test_resource_manager.py    # Testes para utils/resource_manager.py
│   └── test_indexer.py             # Testes unitários para indexer.py
├── integration/                    # Testes de integração
│   └── test_indexer_integration.py # Integração do indexer com APIs externas
└── functional/                     # Testes funcionais
    ├── test_search.py              # Testes do sistema de busca RAG
    └── test_evaluator.py           # Testes do sistema de avaliação
```

## 🏷️ Categorias de Testes

### Testes Unitários (`unit/`)
- **Escopo**: Testam componentes individuais isoladamente
- **Características**: Rápidos, sem dependências externas, mockam todas as dependências
- **Cobertura**: Funções utilitárias, classes de configuração, helpers

### Testes de Integração (`integration/`)
- **Escopo**: Testam integração entre componentes do sistema
- **Características**: Podem usar mocks para APIs externas, mas testam fluxos completos
- **Cobertura**: Pipelines de processamento, comunicação entre módulos

### Testes Funcionais (`functional/`)
- **Escopo**: Testam funcionalidades completas do sistema
- **Características**: Simulam cenários reais de uso, podem ser mais lentos
- **Cobertura**: Sistema RAG completo, avaliação end-to-end

## 🏃‍♂️ Como Executar os Testes

### Usando o script run_tests.py

```bash
# Executar todos os testes
python tests/run_tests.py all

# Executar apenas testes unitários
python tests/run_tests.py unit

# Executar testes de integração
python tests/run_tests.py integration

# Executar testes funcionais
python tests/run_tests.py functional

# Executar testes rápidos (exclui testes marcados como 'slow')
python tests/run_tests.py fast

# Executar testes de um módulo específico
python tests/run_tests.py module:indexer
python tests/run_tests.py module:validation

# Executar com análise de cobertura
python tests/run_tests.py coverage
```

### Usando pytest diretamente

```bash
# Todos os testes com verbose
pytest tests/ -v

# Apenas testes unitários
pytest tests/unit/ -m unit

# Excluir testes lentos
pytest tests/ -m "not slow"

# Com cobertura de código
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Testar arquivo específico
pytest tests/unit/test_validation.py -v

# Executar teste específico
pytest tests/unit/test_validation.py::TestValidateDocument::test_valid_document -v
```

## 🎯 Marcadores (Marks)

Os testes usam marcadores para categorização:

- `@pytest.mark.unit` - Testes unitários
- `@pytest.mark.integration` - Testes de integração  
- `@pytest.mark.functional` - Testes funcionais
- `@pytest.mark.slow` - Testes que demoram mais para executar
- `@pytest.mark.external` - Testes que dependem de recursos externos

## 🔧 Fixtures Principais

### Fixtures Globais (conftest.py)
- `setup_test_environment` - Configura variáveis de ambiente para testes
- `temp_dir` - Diretório temporário para testes
- `sample_document` - Documento de exemplo
- `sample_embedding` - Embedding de exemplo
- `mock_config` - Configuração mockada
- `mock_voyage_client` - Cliente Voyage AI mockado
- `mock_astra_collection` - Collection Astra DB mockada
- `mock_openai_client` - Cliente OpenAI mockado

### Fixtures de Dados (fixtures/test_data.py)
- Perguntas de teste para avaliação
- Documentos de exemplo
- Embeddings simulados
- Respostas RAG mockadas

## 📊 Cobertura de Código

O projeto visa manter alta cobertura de código:

- **Alvo**: >90% de cobertura geral
- **Módulos críticos**: >95% (validation, metrics, core indexer)
- **Relatórios**: HTML e terminal

### Verificar cobertura atual
```bash
python tests/run_tests.py coverage
```

Os relatórios serão gerados em:
- `htmlcov/index.html` - Relatório HTML interativo
- Terminal - Resumo com linhas não cobertas

## 🧪 Boas Práticas Implementadas

### Isolamento
- Cada teste é independente
- Uso extensivo de mocks para dependências externas
- Cleanup automático de recursos temporários

### Nomenclatura
- Nomes descritivos: `test_validate_document_missing_id`
- Prefixos indicam cenário: `test_`, `mock_`, `sample_`
- Classes agrupam testes relacionados

### Parametrização
- Testes parametrizados para múltiplos cenários
- Reduz duplicação de código
- Facilita adição de novos casos

### Fixtures Reutilizáveis
- Dados de teste centralizados
- Configurações padrão mockadas
- Facilita manutenção

## 🐛 Depuração de Testes

### Executar teste específico com debug
```bash
pytest tests/unit/test_validation.py::TestValidateDocument::test_valid_document -v -s
```

### Ver output completo
```bash
pytest tests/ -v -s --tb=long
```

### Parar no primeiro erro
```bash
pytest tests/ -x
```

### Rodar apenas testes que falharam na última execução
```bash
pytest tests/ --lf
```

## 📈 Métricas de Teste

### Performance
- Testes unitários: < 1s total
- Testes de integração: < 30s total
- Testes funcionais: < 2min total

### Qualidade
- Todos os testes devem passar
- Sem warnings desnecessários
- Coverage mínima mantida

## 🔄 CI/CD (Futuro)

A estrutura está preparada para integração contínua:

```yaml
# Exemplo para GitHub Actions
- name: Run Unit Tests
  run: python tests/run_tests.py unit

- name: Run Integration Tests  
  run: python tests/run_tests.py integration

- name: Check Coverage
  run: python tests/run_tests.py coverage
```

## 📝 Adicionando Novos Testes

### Para novos módulos:
1. Criar arquivo de teste correspondente em `unit/`
2. Adicionar testes de integração em `integration/` se necessário
3. Atualizar `run_tests.py` com novo módulo
4. Adicionar fixtures específicas se necessário

### Para novos features:
1. Escrever testes primeiro (TDD)
2. Usar fixtures existentes quando possível
3. Marcar apropriadamente com `@pytest.mark.*`
4. Documentar casos de edge testados

## 🆘 Troubleshooting

### Problema: ImportError
- Verificar se está executando do diretório correto
- Verificar se `PYTHONPATH` inclui o diretório do projeto

### Problema: Testes lentos
- Usar marcador `@pytest.mark.slow` para testes demorados
- Executar `python tests/run_tests.py fast` para pular testes lentos

### Problema: Falhas em mocks
- Verificar se mocks estão configurados corretamente
- Usar `patch` com paths absolutos
- Verificar ordem de decorators `@patch`

## 📚 Recursos Adicionais

- [Documentação do pytest](https://docs.pytest.org/)
- [pytest-cov para cobertura](https://pytest-cov.readthedocs.io/)
- [Best practices para testes em Python](https://docs.python-guide.org/writing/tests/)
