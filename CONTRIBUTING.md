# 🤝 Guia de Contribuição

## 🎯 Como Contribuir

Obrigado por considerar contribuir para o projeto RAG Multi-Agente! Este guia vai ajudá-lo a contribuir de forma efetiva.

## 🚀 Começando

### 1. **Setup do Ambiente de Desenvolvimento**

```bash
# Fork e clone o repositório
git clone https://github.com/seu-usuario/rag-multi-agent.git
cd rag-multi-agent

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências de desenvolvimento
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurar hooks de pre-commit
pre-commit install
```

### 2. **Configuração Inicial**

```bash
# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Executar testes para verificar setup
python -m pytest tests/

# Executar verificações de qualidade
python -m flake8 .
python -m black . --check
python -m isort . --check-only
```

## 📋 Tipos de Contribuição

### 🐛 **Reportar Bugs**

#### Antes de reportar:
1. Verificar se o bug já foi reportado nas [Issues](https://github.com/projeto/issues)
2. Testar com a versão mais recente
3. Verificar se não é problema de configuração

#### Template de Bug Report:
```markdown
**Descrição do Bug**
Descrição clara do que está acontecendo.

**Para Reproduzir**
1. Ir para '...'
2. Clicar em '....'
3. Rolar para baixo até '....'
4. Ver erro

**Comportamento Esperado**
Descrição do que deveria acontecer.

**Screenshots**
Se aplicável, adicionar screenshots.

**Ambiente:**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.11]
- Versão: [e.g. 1.0.0]

**Logs**
```
Colar logs relevantes aqui
```

**Contexto Adicional**
Qualquer outra informação relevante.
```

### 💡 **Sugerir Features**

#### Template de Feature Request:
```markdown
**Problema/Necessidade**
Descrição clara do problema que a feature resolveria.

**Solução Proposta**
Descrição da solução que você gostaria de ver.

**Alternativas Consideradas**
Outras soluções que você considerou.

**Contexto Adicional**
Screenshots, mockups, referências, etc.
```

### 🔧 **Contribuições de Código**

#### Workflow de Desenvolvimento:

1. **Criar Branch**:
```bash
git checkout -b feature/nome-da-feature
# ou
git checkout -b fix/nome-do-bug
```

2. **Fazer Alterações**:
   - Seguir guias de estilo
   - Adicionar testes
   - Atualizar documentação

3. **Testar Localmente**:
```bash
# Executar testes
python -m pytest tests/ -v

# Verificar qualidade de código
python -m flake8 .
python -m black .
python -m isort .

# Executar testes de integração
./test_all_endpoints.sh
```

4. **Commit**:
```bash
git add .
git commit -m "tipo: descrição clara da mudança"

# Exemplos:
# feat: adicionar cache para embeddings
# fix: corrigir timeout em queries longas
# docs: atualizar guia de instalação
# test: adicionar testes para API de chat
```

5. **Push e Pull Request**:
```bash
git push origin feature/nome-da-feature
```

## 📏 Padrões de Código

### **Python Style Guide**

#### PEP 8 + Extensões:
```python
# Imports organizados
import os
import sys
from typing import Dict, List, Optional

import requests
from fastapi import FastAPI

from utils.cache import CacheManager
from agents.base import BaseAgent

# Docstrings no formato Google
def search_documents(query: str, max_results: int = 10) -> List[Dict]:
    """
    Busca documentos relevantes na base de conhecimento.
    
    Args:
        query: Texto da consulta
        max_results: Número máximo de resultados
        
    Returns:
        Lista de documentos com scores de relevância
        
    Raises:
        ValueError: Se query estiver vazia
        ConnectionError: Se ChromaDB não estiver disponível
    """
    if not query.strip():
        raise ValueError("Query não pode estar vazia")
    
    # Implementação...
    return results

# Type hints sempre
class RAGAgent:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.memory: Optional[Memory] = None
    
    def process_query(self, query: str) -> Dict[str, Any]:
        # Implementação...
        pass
```

#### Configuração de Ferramentas:

**pyproject.toml**:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = __pycache__, .git, .venv

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short"
```

### **Estrutura de Testes**

#### Organização:
```
tests/
├── unit/              # Testes unitários
│   ├── test_agents.py
│   ├── test_memory.py
│   └── test_utils.py
├── integration/       # Testes de integração
│   ├── test_api.py
│   ├── test_chromadb.py
│   └── test_multiagent.py
├── fixtures/          # Dados de teste
│   ├── sample_documents.json
│   └── test_config.py
└── conftest.py        # Configuração pytest
```

#### Exemplo de Teste:
```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import Mock, patch

from agents.document_search_agent import DocumentSearchAgent

class TestDocumentSearchAgent:
    
    @pytest.fixture
    def agent(self):
        config = {"max_results": 10}
        return DocumentSearchAgent(config)
    
    @pytest.fixture
    def mock_chromadb(self):
        with patch('chromadb.PersistentClient') as mock:
            yield mock
    
    def test_search_documents_success(self, agent, mock_chromadb):
        # Arrange
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["doc1", "doc2"]],
            "distances": [[0.1, 0.2]]
        }
        mock_chromadb.return_value.get_collection.return_value = mock_collection
        
        # Act
        results = agent.search_documents("test query")
        
        # Assert
        assert len(results) == 2
        assert results[0]["content"] == "doc1"
        assert results[0]["score"] > results[1]["score"]
    
    def test_search_documents_empty_query(self, agent):
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Query não pode estar vazia"):
            agent.search_documents("")
    
    @pytest.mark.integration
    def test_search_with_real_chromadb(self, agent):
        # Teste de integração com ChromaDB real
        results = agent.search_documents("machine learning")
        assert isinstance(results, list)
```

### **Documentação de Código**

#### Docstrings Obrigatórias:
```python
class EnhancedRAGSubagent:
    """
    Agente especializado em análise profunda de documentos RAG.
    
    Este agente implementa técnicas avançadas de processamento de linguagem
    natural para extrair insights relevantes de documentos recuperados.
    
    Attributes:
        memory: Sistema de memória para contexto persistente
        reasoning: Motor de raciocínio ReAct
        tools: Conjunto de ferramentas disponíveis
        
    Example:
        >>> memory = EnhancedMemory()
        >>> reasoning = EnhancedReActReasoning()
        >>> agent = EnhancedRAGSubagent(memory, reasoning, tools)
        >>> result = agent.analyze_documents(documents)
    """
    
    def analyze_documents(self, documents: List[Document]) -> Analysis:
        """
        Analisa lista de documentos e extrai insights relevantes.
        
        Processa documentos usando técnicas de NLP avançadas incluindo
        análise semântica, extração de entidades e correlação de conceitos.
        
        Args:
            documents: Lista de documentos a serem analisados
            
        Returns:
            Objeto Analysis contendo insights extraídos, correlações
            encontradas e score de confiança
            
        Raises:
            ValueError: Se lista de documentos estiver vazia
            ProcessingError: Se análise falhar por problemas técnicos
            
        Example:
            >>> documents = [doc1, doc2, doc3]
            >>> analysis = agent.analyze_documents(documents)
            >>> print(f"Confiança: {analysis.confidence_score}")
        """
        pass
```

## 🧪 Testing Guidelines

### **Cobertura de Testes**

```bash
# Executar com cobertura
python -m pytest --cov=. --cov-report=html

# Ver relatório
open htmlcov/index.html
```

#### Metas de Cobertura:
- **Core modules**: 90%+
- **API endpoints**: 95%+
- **Utility functions**: 85%+
- **Overall**: 85%+

### **Tipos de Teste**

#### 1. **Testes Unitários**
```python
def test_cache_get_miss():
    cache = CacheManager()
    result = cache.get("non_existent_key")
    assert result is None

def test_cache_set_get():
    cache = CacheManager()
    cache.set("test_key", "test_value")
    result = cache.get("test_key")
    assert result == "test_value"
```

#### 2. **Testes de Integração**
```python
@pytest.mark.integration
def test_api_search_endpoint():
    response = client.post("/search", json={
        "query": "test query",
        "max_results": 5
    })
    assert response.status_code == 200
    assert "results" in response.json()
```

#### 3. **Testes End-to-End**
```python
@pytest.mark.e2e
def test_full_rag_pipeline():
    # Indexar documento
    indexer.add_document("test.txt", "conteúdo de teste")
    
    # Buscar
    response = client.post("/search", json={"query": "teste"})
    
    # Verificar resultado
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    assert "conteúdo de teste" in results[0]["content"]
```

## 📚 Documentação

### **Atualizações Obrigatórias**

Ao adicionar features, sempre atualizar:

1. **README.md** - Se mudar interface principal
2. **API_USAGE.md** - Se adicionar/modificar endpoints
3. **docs/EXAMPLES.md** - Se criar novos casos de uso
4. **CHANGELOG.md** - Para toda mudança

### **Formato Markdown**

```markdown
# Use títulos descritivos

## Seções bem organizadas

### Subseções específicas

- Listas claras
- Pontos objetivos

1. Procedimentos numerados
2. Quando ordem importa

```bash
# Comandos sempre em blocos de código
python script.py
```

**Negrito** para termos importantes
*Itálico* para ênfase
`Código inline` para variáveis/comandos

> **⚠️ Aviso**: Informações críticas sempre destacadas
```

## 🔄 Processo de Review

### **Checklist do Pull Request**

#### Antes de submeter:
- [ ] Código segue padrões do projeto
- [ ] Testes passando (unit + integration)
- [ ] Cobertura mantida/melhorada
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] Commit messages descritivas

#### Template de PR:
```markdown
## Descrição
Breve descrição das mudanças.

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova feature
- [ ] Breaking change
- [ ] Documentação

## Testes
- [ ] Testes unitários adicionados/atualizados
- [ ] Testes de integração passando
- [ ] Testado manualmente

## Checklist
- [ ] Código segue style guide
- [ ] Self-review realizada
- [ ] Documentação atualizada
- [ ] Nenhum linting error
```

### **Processo de Review**

#### Reviewers verificam:
1. **Funcionalidade**: Code works as intended
2. **Qualidade**: Follows best practices  
3. **Testes**: Adequate test coverage
4. **Documentação**: Clear and updated
5. **Performance**: No regression

#### Timeline esperado:
- **Review inicial**: 24-48h
- **Feedback/corrections**: 1-3 iterações
- **Merge**: Após approval de 2+ reviewers

## 🎖️ Reconhecimento

### **Tipos de Contribuição**

Reconhecemos todos os tipos de contribuição:

- 💻 **Code**: Implementação de features/fixes
- 📖 **Documentation**: Melhorias na documentação  
- 🐛 **Bug Reports**: Identificação de problemas
- 💡 **Ideas**: Sugestões de melhorias
- 🤔 **Feedback**: Comentários construtivos
- 🔍 **Testing**: Testes e validação
- 🎨 **Design**: UI/UX improvements

### **Contributors**

Mantemos lista de contributors em:
- `CONTRIBUTORS.md`
- Release notes
- GitHub contributors page

## 📞 Comunicação

### **Canais**

- **GitHub Issues**: Bugs e feature requests
- **GitHub Discussions**: Perguntas e discussões
- **Slack/Discord**: Chat real-time (se aplicável)
- **Email**: Contato direto com maintainers

### **Etiqueta**

- 🤝 Seja respeitoso e construtivo
- 💬 Comunique-se claramente
- 🔍 Pesquise antes de perguntar
- 🎯 Seja específico e objetivo
- 🙏 Agradeça o tempo dos outros

## 🆘 Ajuda

Se tiver dúvidas:

1. **Documentação**: Verificar docs/ primeiro
2. **FAQ**: Consultar FAQ.md
3. **Search**: Buscar em issues fechadas
4. **Ask**: Criar nova issue/discussion

**Obrigado por contribuir! 🎉**
