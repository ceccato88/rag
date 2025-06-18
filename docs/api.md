# API Reference - Sistema RAG

Documentação completa da API do sistema RAG.

## 📋 Índice

- [Módulos Principais](#módulos-principais)
- [Módulos Utils](#módulos-utils)
- [Tipos de Dados](#tipos-de-dados)
- [Exemplos de Uso](#exemplos-de-uso)

---

## 🏗️ Módulos Principais

### Indexer

#### `index_pdf(pdf_source: str, config: Optional[Dict] = None) -> Dict`
Indexa um documento PDF no sistema.

**Parâmetros:**
- `pdf_source`: URL ou caminho local do PDF
- `config`: Configurações opcionais

**Retorno:**
```python
{
    "success": bool,
    "pages_processed": int,
    "doc_source": str,
    "processing_time": float,
    "errors": List[str]
}
```

**Exemplo:**
```python
from indexer import index_pdf

result = index_pdf("https://example.com/paper.pdf")
print(f"Páginas processadas: {result['pages_processed']}")
```

### Search

#### `ProductionConversationalRAG`
Sistema principal de busca e geração de respostas.

##### `search_and_answer(query: str, context: Optional[str] = None) -> Dict`
Realiza busca e gera resposta contextual.

**Parâmetros:**
- `query`: Pergunta do usuário
- `context`: Contexto adicional opcional

**Retorno:**
```python
{
    "answer": str,
    "candidates": List[Dict],
    "selected_pages": List[str],
    "total_candidates": int,
    "processing_time": float
}
```

**Exemplo:**
```python
from search import ProductionConversationalRAG

rag = ProductionConversationalRAG()
result = rag.search_and_answer("O que é machine learning?")
print(result['answer'])
```

### Evaluator

#### `RAGEvaluator`
Sistema de avaliação de qualidade.

##### `run_evaluation(test_questions: Optional[List] = None) -> Dict`
Executa avaliação completa do sistema.

**Retorno:**
```python
{
    "precision": float,
    "recall": float,
    "f1_score": float,
    "total_questions": int,
    "processing_time": float,
    "detailed_results": List[Dict]
}
```

---

## 🛠️ Módulos Utils

### Cache (`utils.cache`)

#### `SimpleCache`
Sistema de cache em memória.

##### `__init__(max_size: int = 1000, default_ttl: int = 3600)`
**Parâmetros:**
- `max_size`: Número máximo de itens
- `default_ttl`: TTL padrão em segundos

##### `set(key: str, value: Any, ttl: Optional[int] = None) -> None`
Armazena item no cache.

##### `get(key: str, ttl: Optional[int] = None) -> Any`
Recupera item do cache.

##### `get_stats() -> Dict`
Retorna estatísticas do cache.

**Exemplo:**
```python
from utils.cache import SimpleCache

cache = SimpleCache(max_size=500, default_ttl=1800)
cache.set("embedding_123", [0.1, 0.2, ...])
embedding = cache.get("embedding_123")
```

#### `@cached(ttl: int = 3600)`
Decorator para cache automático de funções.

**Exemplo:**
```python
from utils.cache import cached

@cached(ttl=1800)
def expensive_operation(param):
    # Operação custosa
    return result
```

### Metrics (`utils.metrics`)

#### `ProcessingMetrics`
Coleta métricas de timing.

##### `__init__(operation_name: str)`
**Parâmetros:**
- `operation_name`: Nome da operação

##### `add_step(step_name: str, duration: float) -> None`
Adiciona etapa com duração.

##### `finish() -> None`
Finaliza coleta de métricas.

##### `total_duration -> float`
Retorna duração total.

**Exemplo:**
```python
from utils.metrics import ProcessingMetrics

metrics = ProcessingMetrics("pdf_processing")
metrics.add_step("download", 2.5)
metrics.add_step("parse", 5.2)
metrics.finish()
```

#### `@measure_time(operation: str, context: Optional[Dict] = None)`
Decorator para cronometragem automática.

**Exemplo:**
```python
from utils.metrics import measure_time

@measure_time("embedding_generation")
def generate_embedding(text):
    return embedding
```

### Validation (`utils.validation`)

#### `validate_document(doc: Dict) -> bool`
Valida estrutura de documento.

**Campos obrigatórios:**
- `id`, `page_num`, `markdown_text`, `image_path`, `doc_source`

#### `validate_embedding(embedding: list, expected_dim: int) -> bool`
Valida embedding e sua dimensão.

#### `validate_query(query: str) -> bool`
Valida query de busca.

#### `sanitize_filename(filename: str) -> str`
Sanitiza nome de arquivo.

**Exemplo:**
```python
from utils.validation import validate_document, sanitize_filename

# Validação
if validate_document(doc):
    print("Documento válido")

# Sanitização
clean_name = sanitize_filename("My <File> Name.pdf")
# Resultado: "My_File_Name.pdf"
```

### Resource Manager (`utils.resource_manager`)

#### `ResourceManager`
Gerenciamento de recursos e limpeza.

##### `__init__(base_directory: str)`
**Parâmetros:**
- `base_directory`: Diretório base para recursos

##### `cleanup(max_age_hours: int = 24, pattern: str = "*") -> int`
Limpa arquivos antigos.

**Exemplo:**
```python
from utils.resource_manager import ResourceManager

rm = ResourceManager("/tmp/rag_temp")
deleted = rm.cleanup(max_age_hours=12, pattern="*.pdf")
print(f"Arquivos removidos: {deleted}")
```

---

## 📊 Tipos de Dados

### Document
```python
{
    "id": str,              # ID único do documento
    "page_num": int,        # Número da página
    "markdown_text": str,   # Texto extraído
    "image_path": str,      # Caminho da imagem
    "doc_source": str       # Fonte do documento
}
```

### SearchResult
```python
{
    "answer": str,          # Resposta gerada
    "candidates": List[Dict], # Candidatos encontrados
    "selected_pages": List[str], # Páginas selecionadas
    "total_candidates": int,  # Total de candidatos
    "processing_time": float  # Tempo de processamento
}
```

### CacheStats
```python
{
    "total_requests": int,  # Total de requisições
    "cache_hits": int,      # Acertos do cache
    "cache_misses": int,    # Erros do cache
    "hit_rate": float,      # Taxa de acerto
    "current_size": int     # Tamanho atual
}
```

### Metrics
```python
{
    "operation_name": str,  # Nome da operação
    "steps": List[Dict],    # Etapas cronometradas
    "total_duration": float, # Duração total
    "start_time": datetime, # Início
    "end_time": datetime    # Fim
}
```

---

## 🔧 Exemplos de Uso

### Exemplo Completo: Pipeline de Indexação

```python
from indexer import index_pdf
from utils.metrics import ProcessingMetrics
from utils.resource_manager import ResourceManager

# Setup
metrics = ProcessingMetrics("full_pipeline")
rm = ResourceManager("/tmp/processing")

try:
    # Indexação
    result = index_pdf("https://example.com/paper.pdf")
    
    if result['success']:
        print(f"✅ Documento indexado: {result['pages_processed']} páginas")
    else:
        print(f"❌ Erro na indexação: {result['errors']}")
        
finally:
    # Limpeza
    rm.cleanup()
    metrics.finish()
```

### Exemplo Completo: Sistema de Busca

```python
from search import ProductionConversationalRAG
from utils.cache import cached
from utils.metrics import measure_time

# Sistema de busca com cache
rag = ProductionConversationalRAG()

@cached(ttl=1800)  # Cache por 30 minutos
@measure_time("search_query")
def search_with_cache(query: str):
    return rag.search_and_answer(query)

# Uso
result = search_with_cache("O que é inteligência artificial?")
print(f"Resposta: {result['answer']}")
print(f"Páginas usadas: {len(result['selected_pages'])}")
```

### Exemplo Completo: Avaliação de Qualidade

```python
from evaluator import RAGEvaluator
from utils.metrics import ProcessingMetrics
from utils.validation import validate_document

# Avaliação com métricas
evaluator = RAGEvaluator()
metrics = ProcessingMetrics("rag_evaluation")

# Executar avaliação
report = evaluator.run_evaluation()

# Resultados
print(f"Precisão: {report['precision']:.2%}")
print(f"Recall: {report['recall']:.2%}")
print(f"F1-Score: {report['f1_score']:.2%}")

metrics.finish()
```

---

## 🔍 Códigos de Status

### Success Codes
- `200`: Operação bem-sucedida
- `201`: Recurso criado com sucesso

### Error Codes  
- `400`: Dados inválidos
- `404`: Recurso não encontrado
- `500`: Erro interno do sistema
- `503`: Serviço temporariamente indisponível

### Cache Status
- `HIT`: Item encontrado no cache
- `MISS`: Item não encontrado no cache
- `EXPIRED`: Item expirado no cache

---

## 📈 Métricas Padrão

### Performance Metrics
```python
{
    "operation": str,       # Nome da operação
    "duration": float,      # Duração em segundos
    "success": bool,        # Se foi bem-sucedida
    "timestamp": datetime,  # Timestamp da operação
    "context": Dict         # Contexto adicional
}
```

### Cache Metrics
```python
{
    "hit_rate": float,      # Taxa de acerto (0.0-1.0)
    "total_requests": int,  # Total de requisições
    "avg_response_time": float, # Tempo médio de resposta
    "memory_usage": int     # Uso de memória em bytes
}
```

---

**API Documentation mantida por**: GitHub Copilot Assistant  
**Última atualização**: 18 de Junho de 2025  
**Versão da API**: 2.0.0
