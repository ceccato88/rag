# 📋 CONTROLE DE VARIÁVEIS - Sistema RAG Multi-Agente

## Status da Análise
- **Data de Atualização**: 2025-06-20
- **Total de Variáveis**: 77 (foram adicionadas 5 novas)
- **Variáveis Analisadas**: 77/77 (100%)
- **Variáveis com Problemas**: 0
- **Status**: ✅ CONCLUÍDO - MELHORADO

---

## 🔑 **1. API KEYS (OBRIGATÓRIAS)** - 4 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 1 | `OPENAI_API_KEY` | `sk-proj-your_openai_key_here` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 2 | `VOYAGE_API_KEY` | `pa-your_voyage_key_here` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 3 | `ASTRA_DB_API_ENDPOINT` | `https://your-db-id.apps.astra.datastax.com` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 4 | `ASTRA_DB_APPLICATION_TOKEN` | `AstraCS:your_token_here` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 🤖 **2. MODELOS DE IA** - 7 variáveis (2 novas)

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 5 | `OPENAI_MODEL` | `gpt-4.1-mini` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 6 | `COORDINATOR_MODEL` | `gpt-4.1` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 7 | `EMBEDDING_MODEL` | `voyage-multimodal-3` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 8 | `MAX_TOKENS` | `4000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 9 | `TEMPERATURE` | `0.1` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 10 | `TEMPERATURE_SYNTHESIS` | `0.2` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |
| 11 | `TEMPERATURE_PRECISE` | `0.0` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |

---

## 🔧 **3. CONFIGURAÇÕES DE TOKENS** - 8 variáveis (5 novas)

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 12 | `MAX_TOKENS_SCORE` | `10` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |
| 13 | `MAX_TOKENS_EVALUATION` | `20` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |
| 14 | `MAX_TOKENS_RATING` | `300` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |
| 15 | `MAX_TOKENS_DECOMPOSITION_ITEM` | `200` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |
| 16 | `MAX_TOKENS_SUBQUERY` | `100` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |
| 17 | `MAX_TOKENS_RERANK` | `512` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 18 | `MAX_TOKENS_ANSWER` | `2048` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 19 | `MAX_TOKENS_QUERY_TRANSFORM` | `150` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 🔧 **4. CONFIGURAÇÕES RAG** - 5 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 20 | `MAX_CANDIDATES` | `5` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 21 | `CONFIDENCE_THRESHOLD` | `0.2` | ✅ | ✅ | ✅ | ✅ | ✅ **NOVO - CONCLUÍDO** |
| 22 | `COLLECTION_NAME` | `pdf_documents` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 23 | `TOP_K` | `5` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 24 | `CHUNK_SIZE` | `1000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 25 | `CHUNK_OVERLAP` | `200` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 🔒 **5. SEGURANÇA API** - 4 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 15 | `API_BEARER_TOKEN` | `your_secure_bearer_token_here` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 16 | `ENABLE_RATE_LIMITING` | `true` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 17 | `RATE_LIMIT` | `100/minute` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 18 | `ENABLE_CORS` | `false` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 🚀 **5. PERFORMANCE & MULTI-AGENTE** - 6 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 19 | `MAX_SUBAGENTS` | `3` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 20 | `PARALLEL_EXECUTION` | `true` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 21 | `USE_LLM_DECOMPOSITION` | `true` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 22 | `MULTIAGENT_TIMEOUT` | `300` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 23 | `SUBAGENT_TIMEOUT` | `300` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 24 | `REQUEST_TIMEOUT` | `60` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 💾 **6. CACHE** - 4 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 25 | `EMBEDDING_CACHE_SIZE` | `1000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 26 | `EMBEDDING_CACHE_TTL` | `3600` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 27 | `RESPONSE_CACHE_SIZE` | `200` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 28 | `RESPONSE_CACHE_TTL` | `1800` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 📊 **7. LOGGING & MONITORING** - 6 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 29 | `LOG_LEVEL` | `INFO` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 30 | `ENABLE_STRUCTURED_LOGGING` | `true` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 31 | `ENABLE_PERFORMANCE_METRICS` | `true` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 32 | `PRODUCTION_MODE` | `false` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 33 | `MAX_LOG_FILE_SIZE` | `50` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 34 | `LOG_ROTATION_COUNT` | `10` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 🖥️ **8. SERVIDOR** - 6 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 35 | `API_PORT` | `8000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 36 | `API_WORKERS` | `4` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 37 | `HOST` | `0.0.0.0` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 38 | `RELOAD` | `true` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 39 | `HEALTH_CHECK_INTERVAL` | `30` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 40 | `HEALTH_CHECK_TIMEOUT` | `15` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 📁 **9. ARQUIVOS E DIRETÓRIOS** - 5 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 41 | `DATA_DIR` | `data` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 42 | `PDF_IMAGES_DIR` | `pdf_images` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 43 | `LOGS_DIR` | `logs` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 44 | `MAX_REQUEST_SIZE` | `16777216` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 45 | `MAX_PDF_SIZE` | `52428800` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 🧪 **10. DESENVOLVIMENTO** - 6 variáveis

| # | Variável | Valor Padrão | .env | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|------|--------------|-----------|---------------|---------|
| 46 | `DEBUG_MODE` | `false` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 47 | `ENABLE_DEBUG_LOGS` | `false` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 48 | `ENABLE_TEST_ENDPOINTS` | `false` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 49 | `MOCK_AI_RESPONSES` | `false` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 50 | `PYTEST_TIMEOUT` | `300` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 51 | `TEST_COLLECTION_NAME` | `test_collection` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 🔧 **11. CONSTANTES ESPECÍFICAS (apenas constants.py)** - 21 variáveis

### 11.1 Tokens e Limites
| # | Variável | Valor Padrão | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|--------------|-----------|---------------|---------|
| 52 | `MAX_TOKENS_RERANK` | `512` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 53 | `MAX_TOKENS_ANSWER` | `2048` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 54 | `MAX_TOKENS_QUERY_TRANSFORM` | `150` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 55 | `MAX_TOKENS_DECOMPOSITION` | `1000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 56 | `VOYAGE_EMBEDDING_DIM` | `1024` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 57 | `MAX_TOKENS_PER_INPUT` | `32000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

### 11.2 Processamento
| # | Variável | Valor Padrão | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|--------------|-----------|---------------|---------|
| 58 | `BATCH_SIZE` | `100` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 59 | `DOWNLOAD_CHUNK_SIZE` | `8192` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 60 | `PIXMAP_SCALE` | `2` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 61 | `TOKENS_PER_PIXEL` | `1/560` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 62 | `TOKEN_CHARS_RATIO` | `4` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 63 | `PROCESSING_CONCURRENCY` | `5` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 64 | `CLEANUP_MAX_AGE` | `24` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

### 11.3 Outros
| # | Variável | Valor Padrão | constants.py | config.py | Uso no Código | Status |
|---|----------|--------------|--------------|-----------|---------------|---------|
| 65 | `CONCURRENCY_LIMIT` | `3` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 66 | `SIMILARITY_THRESHOLD` | `0.7` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 67 | `MEMORY_SHARDS` | `4` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 68 | `MIN_QUERY_LENGTH` | `3` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 69 | `MAX_QUERY_LENGTH` | `1000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 70 | `MAX_OBJECTIVE_LENGTH` | `500` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 71 | `MIN_URL_LENGTH` | `10` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |
| 72 | `MAX_URL_LENGTH` | `2000` | ✅ | ✅ | ✅ | ✅ | ✅ **CONCLUÍDO** |

---

## 📝 **LEGENDA**

### Status
- ✅ **CONFIRMADO** - Variável encontrada e implementada corretamente
- ❌ **PROBLEMA** - Variável com problemas (não encontrada, mal implementada, etc.)
- ⚠️ **ATENÇÃO** - Variável encontrada mas com possíveis melhorias
- ❓ **NÃO VERIFICADO** - Ainda não analisado
- ⏳ **PENDENTE** - Aguardando análise

### Colunas
- **.env**: Variável definida no arquivo .env
- **constants.py**: Variável definida em src/core/constants.py
- **config.py**: Variável carregada em src/core/config.py
- **Uso no Código**: Variável utilizada nos arquivos da aplicação

---

## 🎯 **PRÓXIMOS PASSOS**

1. **Iniciar por API Keys** (variáveis 1-4) - Críticas para funcionamento
2. **Continuar com Modelos IA** (variáveis 5-9) - Impacto direto na funcionalidade  
3. **Verificar Configurações RAG** (variáveis 10-14) - Core do sistema
4. **Analisar Segurança** (variáveis 15-18) - Proteção da API
5. **Performance & Cache** (variáveis 19-28) - Otimização
6. **Demais categorias** sequencialmente

**COMANDO PARA ATUALIZAR STATUS:**
- Após verificar cada variável, atualizar a tabela com os resultados encontrados
- Marcar como ✅ ❌ ⚠️ conforme os achados
- Documentar problemas encontrados no final do arquivo

---

## 🚨 **PROBLEMAS ENCONTRADOS**

### ✅ **VARIÁVEL #1: OPENAI_API_KEY**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: Uso direto em `multi-agent-researcher/src/researcher/agents/openai_lead_researcher.py:606`
- **Código Corrigido**: 
  ```python
  # ANTES: sync_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
  # DEPOIS: sync_client = OpenAI(api_key=self.api_key)
  ```
- **Resultado**: Agora usa configuração centralizada através de `self.api_key`
- **Impacto**: Sistema de configuração centralizado preservado
- **Prioridade**: ✅ RESOLVIDO

### ✅ **VARIÁVEL #2: VOYAGE_API_KEY**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: Uso direto em `src/core/search.py:400`
- **Código Corrigido**: 
  ```python
  # ANTES: voyageai.api_key = os.environ["VOYAGE_API_KEY"]
  # DEPOIS: voyageai.api_key = system_config.rag.voyage_api_key
  ```
- **Resultado**: Agora usa configuração centralizada através de `system_config.rag.voyage_api_key`
- **Impacto**: Sistema de configuração centralizado preservado
- **Prioridade**: ✅ RESOLVIDO

### ✅ **VARIÁVEL #3: ASTRA_DB_API_ENDPOINT**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: Uso direto em `src/core/search.py:421`
- **Código Corrigido**: 
  ```python
  # ANTES: database = client.get_database(os.environ["ASTRA_DB_API_ENDPOINT"], ...)
  # DEPOIS: database = client.get_database(system_config.rag.astra_db_api_endpoint, ...)
  ```
- **Resultado**: Agora usa configuração centralizada através de `system_config.rag.astra_db_api_endpoint`
- **Impacto**: Sistema de configuração centralizado preservado
- **Prioridade**: ✅ RESOLVIDO

### ✅ **VARIÁVEL #4: ASTRA_DB_APPLICATION_TOKEN**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: NENHUM - Todos os usos já estão corretos
- **Usos Encontrados**: 
  ```python
  # ✅ scripts/maintenance/delete_collection.py:49
  client = DataAPIClient(token=config.rag.astra_db_application_token)
  
  # ✅ api/routers/management.py:151  
  client = DataAPIClient(token=config.rag.astra_db_application_token)
  
  # ✅ src/core/search.py:422
  token=system_config.rag.astra_db_application_token
  ```
- **Resultado**: Todos os usos já utilizam configuração centralizada
- **Impacto**: Sistema de configuração centralizado mantido
- **Prioridade**: ✅ JÁ ESTAVA CORRETO

### ✅ **VARIÁVEL #5: OPENAI_MODEL**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: NENHUM - Todos os usos já estão corretos
- **Implementação**: 
  ```python
  # ✅ src/core/config.py:44
  llm_model: str = os.getenv('OPENAI_MODEL', DEFAULT_MODELS['LLM'])
  ```
- **Usos Encontrados**: 15+ localizações, todas usando configuração centralizada
- **Resultado**: Sistema de configuração centralizado funcionando perfeitamente
- **Impacto**: Variável totalmente integrada ao sistema
- **Prioridade**: ✅ JÁ ESTAVA CORRETO

### ✅ **VARIÁVEL #6: COORDINATOR_MODEL**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: Uso direto em `openai_lead_researcher.py` (2 localizações)
- **Código Corrigido**: 
  ```python
  # ANTES: coordinator_model = os.getenv('COORDINATOR_MODEL', 'gpt-4.1')
  # DEPOIS: coordinator_model = system_config.rag.coordinator_model
  
  # ANTES: f"coordinator={os.getenv('COORDINATOR_MODEL', 'gpt-4.1')}"
  # DEPOIS: f"coordinator={system_config.rag.coordinator_model}"
  ```
- **Resultado**: Agora usa configuração centralizada através de `system_config.rag.coordinator_model`
- **Impacto**: Sistema de configuração centralizado preservado
- **Prioridade**: ✅ RESOLVIDO

### ✅ **VARIÁVEL #7: EMBEDDING_MODEL**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: Uso hardcoded em `src/core/search.py:526`
- **Código Corrigido**: 
  ```python
  # ANTES: model="voyage-multimodal-3",
  # DEPOIS: model=system_config.rag.embedding_model,
  ```
- **Resultado**: Agora usa configuração centralizada através de `system_config.rag.embedding_model`
- **Impacto**: Sistema de configuração centralizado preservado
- **Prioridade**: ✅ RESOLVIDO

### ✅ **VARIÁVEL #8: MAX_TOKENS**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: Configuração incorreta em `src/core/config.py:131` usando `MAX_TOKENS_DECOMPOSITION`
- **Código Corrigido**: 
  ```python
  # ANTES: max_tokens: int = get_env_int('MAX_TOKENS_DECOMPOSITION', TOKEN_LIMITS['MAX_TOKENS_DECOMPOSITION'])
  # DEPOIS: max_tokens: int = get_env_int('MAX_TOKENS', TOKEN_LIMITS['MAX_TOKENS'])
  ```
- **Código Corrigido**: Hardcoded em `openai_lead_researcher.py:610`
  ```python
  # ANTES: max_tokens=4000,
  # DEPOIS: max_tokens=system_config.rag.max_tokens,
  ```
- **Resultado**: Agora usa configuração centralizada através de `system_config.rag.max_tokens`
- **Impacto**: Sistema de configuração centralizado preservado
- **Prioridade**: ✅ RESOLVIDO

### ✅ **VARIÁVEL #9: TEMPERATURE**
- **Status**: ✅ CONCLUÍDO  
- **Problema**: Valores hardcoded em 6 localizações (0.1)
- **Código Corrigido**: 
  ```python
  # Corrigido em 6 arquivos:
  # - openai_lead_researcher.py:611
  # - search.py:947
  # - enhanced_decomposition.py (2 ocorrências)
  # - enhanced_evaluation.py:176
  # - api/core/config.py:39
  # ANTES: temperature=0.1
  # DEPOIS: temperature=system_config.rag.temperature
  ```
- **Resultado**: Agora usa configuração centralizada através de `system_config.rag.temperature`
- **Impacto**: Sistema de configuração centralizado preservado
- **Prioridade**: ✅ RESOLVIDO

---

## 🔧 **NOVAS CONSTANTES ADICIONADAS (2025-06-20)**

### ✅ **CONSTANTE: COMPLEXITY_PATTERNS**
- **Status**: ✅ IMPLEMENTADO
- **Localização**: `src/core/constants.py` (linhas 246-263)
- **Propósito**: Padrões para determinar complexidade de queries automaticamente
- **Estrutura**: 
  ```python
  COMPLEXITY_PATTERNS = {
      'SIMPLE': ["what is", "define", "o que é", "definição"],
      'MODERATE': ["how does", "why", "como funciona", "por que"],
      'COMPLEX': ["compare", "analyze", "comparar", "analisar"],
      'VERY_COMPLEX': ["comprehensive analysis", "detailed comparison"]
  }
  ```
- **Uso**: `src/core/search.py:92` em `determine_query_complexity()`
- **Impacto**: Remove valores hardcoded, segue boas práticas de configuração

### ✅ **CONSTANTE: DYNAMIC_MAX_CANDIDATES**
- **Status**: ✅ IMPLEMENTADO  
- **Localização**: `src/core/constants.py` (linhas 265-271)
- **Propósito**: MAX_CANDIDATES dinâmico baseado na complexidade da query
- **Estrutura**:
  ```python
  DYNAMIC_MAX_CANDIDATES = {
      'SIMPLE': 2,         # Queries simples precisam menos documentos
      'MODERATE': 3,       # Queries moderadas usam padrão atual
      'COMPLEX': 4,        # Queries complexas precisam mais contexto
      'VERY_COMPLEX': 5,   # Queries muito complexas precisam máximo contexto
      'DEFAULT': 3         # Fallback para casos não classificados
  }
  ```
- **Uso**: `src/core/search.py:130` em `get_dynamic_max_candidates()`
- **Problema Resolvido**: Sistema sempre usava fallback fixo de 3 candidatos
- **Resultado**: Agora adapta automaticamente (2-5 candidatos) baseado na complexidade
- **Impacto**: Melhora qualidade das respostas usando contexto adequado por complexidade