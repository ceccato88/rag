# 📚 Como Executar o Indexer Refatorado v2.0.0

## 🚀 Execução Direta via CLI

### 1. Indexar PDF de URL
```bash
python indexer.py https://arxiv.org/pdf/2501.13956.pdf
```

### 2. Indexar PDF local
```bash
python indexer.py /caminho/para/documento.pdf
```

### 3. Especificar nome do documento
```bash
python indexer.py https://example.com/paper.pdf --doc-source "meu_artigo"
```

### 4. Resultado nativo detalhado
```bash
python indexer.py https://example.com/paper.pdf --native-result
```

## 📊 Exemplo de Saída

### Execução Normal
```bash
$ python indexer.py https://arxiv.org/pdf/2501.13956.pdf

🚀 Iniciando indexação refatorada v2.0.0: 2501.13956
📄 PDF: https://arxiv.org/pdf/2501.13956.pdf
📥 Baixando PDF: https://arxiv.org/pdf/2501.13956.pdf
✅ PDF baixado (X páginas)
📊 Extraindo conteúdo de X páginas...
Extraindo páginas: 100%|████████| X/X [00:XX<00:00, X.XXit/s]
✅ Extraídas X páginas
🧠 Gerando embeddings multimodais...
🔄 Gerando embeddings com 5 workers...
✅ Gerados X embeddings
🔌 Conectado ao database: default_keyspace
📚 Usando collection: pdf_documents
🗑️ Removidos X documentos antigos
💾 Inserindo X documentos...
Inserindo no AstraDB: 100%|████████| X/X [00:XX<00:00, X.XXit/s]
✅ Indexação refatorada concluída!
📊 Documentos inseridos: X/X
⏱️ Tempo de processamento: XX.XXs
🎯 Doc source: 2501.13956
🎉 Indexação realizada com sucesso!
```

### Resultado Nativo Detalhado
```bash
$ python indexer.py https://example.com/paper.pdf --native-result

[... processo de indexação ...]

📊 RESULTADO DA INDEXAÇÃO:
✅ Sucesso: True
📄 Doc Source: paper
📊 Páginas: 15
🧩 Chunks: 15
⏱️ Tempo: 45.67s
```

## 🔧 Uso Programático

### 1. Função Compatível (Boolean)
```python
from indexer import process_pdf_from_url

# Retorna True/False
success = process_pdf_from_url(
    url="https://example.com/paper.pdf",
    doc_source="meu_documento"  # Opcional
)

if success:
    print("✅ Indexação concluída")
else:
    print("❌ Falha na indexação")
```

### 2. Função Nativa (Resultado Detalhado)
```python
from indexer import index_pdf_native

# Retorna IndexingResult com detalhes
result = index_pdf_native(
    url="https://example.com/paper.pdf",
    doc_source="meu_documento"  # Opcional
)

print(f"Sucesso: {result.success}")
print(f"Páginas processadas: {result.pages_processed}")
print(f"Tempo: {result.processing_time:.2f}s")
print(f"Metadata: {result.metadata}")

if result.error:
    print(f"Erro: {result.error}")
```

### 3. Usar com APIs Refatoradas
```python
# As APIs automaticamente usam o indexer refatorado
import requests

# API Multi-Agente (Port 8000)
response = requests.post("http://localhost:8000/index", 
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "url": "https://example.com/paper.pdf",
        "doc_source": "meu_artigo"
    }
)

result = response.json()
print(f"✅ Sucesso: {result['success']}")
print(f"📊 Páginas: {result['pages_processed']}")
print(f"⏱️ Tempo: {result['processing_time']}")
```

## 🛠️ Configurações Avançadas

### Variáveis de Ambiente Necessárias
```bash
# APIs obrigatórias
OPENAI_API_KEY=sk-proj-...
VOYAGE_API_KEY=pa-...
ASTRA_DB_API_ENDPOINT=https://...
ASTRA_DB_APPLICATION_TOKEN=AstraCS:...

# Configurações opcionais
BATCH_SIZE=100                    # Tamanho do lote
PROCESSING_CONCURRENCY=5          # Workers paralelos
DOWNLOAD_TIMEOUT=30               # Timeout de download
MAX_RETRIES=3                     # Tentativas de retry
```

### Configurações no SystemConfig
```python
from config import SystemConfig

config = SystemConfig()

# Configurações de processamento
config.processing.batch_size = 50
config.processing.processing_concurrency = 3
config.processing.download_timeout = 60

# Configurações de retry
config.multiagent.max_retries = 5
config.multiagent.retry_delay = 2.0
```

## 📁 Estrutura de Arquivos Gerados

```
pdf_images/
├── documento_page_1.png         # Imagem da página 1
├── documento_page_2.png         # Imagem da página 2
└── ...                          # Demais páginas
```

## 🔍 Validações Automáticas

O indexer refatorado inclui validações automáticas:

### URLs Suportadas
- ✅ `https://example.com/paper.pdf`
- ✅ `http://example.com/paper.pdf` 
- ✅ `/caminho/local/documento.pdf`
- ❌ URLs inválidas ou sem extensão .pdf

### Nomes de Documentos
- ✅ `documento_valido`
- ✅ `artigo-2024.pdf`
- ✅ `paper_v1.2`
- ❌ `doc@especial#chars`
- ❌ Nomes muito longos (>100 chars)

### Ambiente
- ✅ Todas as variáveis obrigatórias presentes
- ❌ APIs keys ausentes ou inválidas

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de API Key**
```bash
❌ Variáveis de ambiente ausentes: VOYAGE_API_KEY
```
**Solução**: Configurar .env com todas as APIs

2. **Erro de Download**
```bash
❌ Falha ao baixar PDF após 3 tentativas
```
**Solução**: Verificar URL e conectividade

3. **Erro de Embedding**
```bash
❌ Nenhum embedding gerado
```
**Solução**: Verificar VOYAGE_API_KEY e quotas

4. **Erro de Database**
```bash
❌ Erro ao conectar com AstraDB
```
**Solução**: Verificar ASTRA_DB_* configurações

### Logs Detalhados
```bash
# Ativar logs detalhados
LOG_LEVEL=DEBUG python indexer.py documento.pdf

# Ou alterar no .env
LOG_LEVEL=DEBUG
VERBOSE_LOGGING=true
```

### Validar Configuração
```bash
python -c "from config import SystemConfig; SystemConfig().print_status()"
```

## 📊 Performance

### Otimizações Disponíveis
- **Concorrência**: Até 5 workers paralelos para embeddings
- **Batch Size**: Inserção em lotes (padrão: 100)
- **Cache**: Embeddings e respostas cacheadas
- **Retry**: Retry automático com backoff exponencial

### Tempos Típicos
- **PDF pequeno** (1-5 páginas): 10-30 segundos
- **PDF médio** (10-20 páginas): 1-3 minutos
- **PDF grande** (50+ páginas): 5-15 minutos

*Tempos variam com conectividade, quotas de API e tamanho das imagens*

## 🔄 Integração com Docker

```bash
# Executar via container
docker-compose exec api-multiagent python indexer.py documento.pdf

# Ou buildar imagem específica
docker build -f Dockerfile.api-multiagent -t rag-indexer .
docker run -v ./pdf_images:/app/pdf_images rag-indexer python indexer.py documento.pdf
```

---

**Indexer Refatorado v2.0.0** - Sistema RAG Multi-Agente  
*Otimizado para modelos nativos e integração com APIs*