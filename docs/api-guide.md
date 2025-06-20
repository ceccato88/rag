# 📝 Guia da API

Documentação completa dos endpoints da API RAG Multi-Agent System.

## 🔐 Autenticação

Todas as rotas (exceto `/health`) requerem autenticação Bearer Token.

```bash
# Header obrigatório
Authorization: Bearer YOUR_API_BEARER_TOKEN
```

**Obter token do .env**:
```bash
grep API_BEARER_TOKEN .env
```

## 🎯 Endpoints Principais

### 1. 🤖 Multi-Agent Research

**Endpoint**: `POST /api/v1/research`

**Descrição**: Pesquisa avançada com sistema multi-agente, reasoning ReAct e síntese crítica.

**Request**:
```json
{
  "query": "Como Zep implementa temporal knowledge graphs para memória de agentes AI?",
  "use_multiagent": true,
  "max_subagents": 3,
  "timeout": 300
}
```

**Response**:
```json
{
  "success": true,
  "query": "Como Zep implementa temporal knowledge graphs...",
  "result": "# 🤖 AI-Coordinated Research Synthesis\n\n**Coordinator Model**: gpt-4.1\n**Synthesis Method**: Advanced AI Critical Analysis\n**Subagents Processed**: 3/3\n**Timestamp**: 2025-06-19 23:46:44\n\n---\n\n## Resumo Executivo\n\nEsta análise compara criticamente...",
  "agent_id": "abc-123-def-456",
  "status": "COMPLETED",
  "processing_time": 24.5,
  "timestamp": "2025-06-19T23:46:44.123456",
  "confidence_score": null,
  "sources": [],
  "reasoning_trace": null,
  "error": null
}
```

**Parâmetros**:
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `query` | string | ✅ | Query de pesquisa |
| `use_multiagent` | boolean | ✅ | Ativar sistema multi-agente |
| `max_subagents` | integer | ❌ | Máximo de subagentes (padrão: 3) |
| `timeout` | integer | ❌ | Timeout em segundos (padrão: 300) |

**Exemplo cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explique as vantagens do Zep vs MemGPT para aplicações empresariais",
    "use_multiagent": true
  }'
```

### 2. 🔍 Simple Search

**Endpoint**: `POST /api/v1/simple`

**Descrição**: Busca RAG simples e direta, sem multi-agente.

**Request**:
```json
{
  "query": "O que é Zep?",
  "collection_name": "pdf_documents",
  "top_k": 5
}
```

**Response**:
```json
{
  "success": true,
  "query": "O que é Zep?",
  "result": "Zep é um sistema de memória temporal baseado em grafos de conhecimento para agentes de IA...",
  "processing_time": 2.1,
  "sources": [
    {
      "page": 1,
      "similarity": 0.95,
      "content": "Texto do documento..."
    }
  ]
}
```

**Exemplo cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/simple" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "O que é temporal knowledge graph?"}'
```

### 3. 📚 Document Indexing

**Endpoint**: `POST /api/v1/index`

**Descrição**: Indexa documento PDF com extração de texto e imagens.

**Request**:
```json
{
  "pdf_url": "https://arxiv.org/pdf/2501.13956",
  "collection_name": "pdf_documents",
  "extract_images": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "PDF indexado com sucesso",
  "details": {
    "pages_processed": 12,
    "images_extracted": 12,
    "text_chunks": 45,
    "collection": "pdf_documents"
  },
  "processing_time": 156.7
}
```

**Exemplo cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/index" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://arxiv.org/pdf/2501.13956",
    "extract_images": true
  }'
```

### 4. ❤️ Health Check

**Endpoint**: `GET /api/v1/health`

**Descrição**: Verifica status do sistema (sem autenticação).

**Response**:
```json
{
  "status": "healthy",
  "uptime_seconds": 3712.6,
  "components": {
    "memory": true,
    "simple_rag": true,
    "lead_researcher": true
  },
  "metrics": {
    "total_requests": 42,
    "successful_requests": 40,
    "failed_requests": 2,
    "success_rate": 95.2,
    "average_response_time": 8.5
  },
  "timestamp": "2025-06-19T23:18:28.757680"
}
```

**Exemplo cURL**:
```bash
curl http://localhost:8000/api/v1/health | jq
```

## 📊 Endpoints de Gerenciamento

### 5. 📈 Statistics

**Endpoint**: `GET /api/v1/stats`

**Descrição**: Estatísticas detalhadas do sistema.

**Response**:
```json
{
  "system_stats": {
    "uptime_hours": 2.4,
    "total_queries": 25,
    "multiagent_queries": 20,
    "simple_queries": 5,
    "average_processing_time": 12.3
  },
  "agent_stats": {
    "total_subagents_spawned": 60,
    "successful_executions": 58,
    "failed_executions": 2,
    "focus_area_distribution": {
      "conceptual": 18,
      "technical": 22,
      "comparative": 15,
      "examples": 12
    }
  },
  "model_usage": {
    "coordinator_calls": 20,
    "subagent_calls": 60,
    "total_tokens": 125000
  }
}
```

### 6. 🗄️ Document Management

**Endpoint**: `GET /api/v1/documents/{collection_name}`

**Descrição**: Lista documentos na collection.

**Response**:
```json
{
  "collection_name": "pdf_documents",
  "total_documents": 156,
  "documents": [
    {
      "id": "doc_1",
      "source": "https://arxiv.org/pdf/2501.13956",
      "pages": 12,
      "indexed_at": "2025-06-19T20:15:30Z"
    }
  ]
}
```

**Endpoint**: `DELETE /api/v1/documents/{collection_name}`

**Descrição**: Deleta todos documentos da collection.

**Response**:
```json
{
  "success": true,
  "message": "142 documentos deletados da collection 'pdf_documents'"
}
```

### 7. 🖼️ Image Management

**Endpoint**: `DELETE /api/v1/images`

**Descrição**: Deleta todas imagens extraídas.

**Response**:
```json
{
  "success": true,
  "message": "156 imagens deletadas do diretório 'data/pdf_images'"
}
```

## 🔧 Parâmetros Avançados

### Multi-Agent Research Parameters

```json
{
  "query": "string",                    // Obrigatório
  "use_multiagent": true,              // Obrigatório para multi-agent
  "max_subagents": 3,                  // 1-5, padrão: 3
  "timeout": 300,                      // Segundos, padrão: 300
  "focus_areas": ["technical", "examples"], // Forçar focus areas específicas
  "reasoning_detail": "full",          // "minimal"|"full", padrão: minimal
  "synthesis_model": "gpt-4.1",       // Override coordinator model
  "parallel_execution": true          // true|false, padrão: true
}
```

### Simple Search Parameters

```json
{
  "query": "string",                   // Obrigatório
  "collection_name": "pdf_documents", // Padrão: pdf_documents
  "top_k": 5,                         // 1-10, padrão: 5
  "similarity_threshold": 0.7,        // 0.0-1.0, padrão: 0.7
  "include_images": false             // true|false, padrão: false
}
```

## 🎯 Focus Areas na API

### Seleção Automática
```json
{
  "query": "O que é Zep?",
  "use_multiagent": true
}
// ⬇️ Sistema seleciona: ["conceptual", "overview", "examples"]
```

### Seleção Manual
```json
{
  "query": "Compare Zep vs MemGPT",
  "use_multiagent": true,
  "focus_areas": ["comparative", "technical", "applications"]
}
// ⬇️ Força as focus areas especificadas
```

### Focus Areas Disponíveis
| Focus Area | Descrição | Uso Típico |
|------------|-----------|------------|
| `conceptual` | Definições, conceitos | "O que é...?" |
| `technical` | Implementação, código | "Como implementar...?" |
| `comparative` | Comparações, diferenças | "X vs Y" |
| `examples` | Casos de uso práticos | "Exemplos de..." |
| `overview` | Visão geral, introdução | Contexto amplo |
| `applications` | Uso empresarial | "Como usar em produção?" |
| `general` | Pesquisa abrangente | Queries muito gerais |

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": true,
  "error_code": "AUTHENTICATION_ERROR",
  "message": "Credenciais inválidas. Verifique seu token de acesso.",
  "details": {
    "expected_format": "Bearer <token>",
    "received_format": "missing"
  },
  "timestamp": "2025-06-19T23:18:38.763042",
  "method": "POST",
  "url": "http://localhost:8000/api/v1/research",
  "client_ip": "127.0.0.1"
}
```

### Common Error Codes
| Code | HTTP Status | Descrição |
|------|-------------|-----------|
| `AUTHENTICATION_ERROR` | 401 | Token inválido ou ausente |
| `RATE_LIMIT_EXCEEDED` | 429 | Muitas requisições (>100/min) |
| `VALIDATION_ERROR` | 422 | Parâmetros inválidos |
| `PROCESSING_ERROR` | 500 | Erro interno de processamento |
| `TIMEOUT_ERROR` | 504 | Timeout na execução |
| `MODEL_ERROR` | 503 | Falha nos modelos de IA |

### Retry Strategy
```python
import time
import requests

def api_request_with_retry(url, data, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            else:
                response.raise_for_status()
                
        except requests.Timeout:
            if attempt == max_retries - 1:
                raise
            time.sleep(5)  # Wait before retry
            
    raise Exception(f"Failed after {max_retries} attempts")
```

## 🔍 Response Analysis

### Multi-Agent Response Structure
```markdown
# 🤖 AI-Coordinated Research Synthesis

**Coordinator Model**: gpt-4.1
**Synthesis Method**: Advanced AI Critical Analysis  
**Subagents Processed**: 3/3
**Timestamp**: 2025-06-19 23:46:44

---

## Resumo Executivo
[Síntese crítica dos achados]

## Achados Principais
### 1. [Focus Area 1] 
[Resultados específicos]

### 2. [Focus Area 2]
[Resultados específicos]

---

## 📊 Research Metadata
- **Decomposition**: LLM-based
- **Total Tasks**: 3
- **Success Rate**: 3/3 (100%)
- **AI Models**: Subagents (gpt-4.1-mini) + Coordinator (gpt-4.1)
```

### Quality Indicators
- **Coordinator Model**: `gpt-4.1` ← Síntese avançada ativada
- **Success Rate**: `100%` ← Todos subagentes executaram
- **Processing Time**: `< 30s` ← Performance aceitável
- **Synthesis Method**: `Advanced AI Critical Analysis` ← Reasoning sofisticado

## 📚 Integration Examples

### Python SDK Example
```python
import requests
import json

class RAGMultiAgentClient:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def multi_agent_research(self, query: str, **kwargs):
        """Executa pesquisa multi-agente"""
        data = {"query": query, "use_multiagent": True, **kwargs}
        
        response = requests.post(
            f"{self.base_url}/api/v1/research",
            json=data,
            headers=self.headers,
            timeout=60
        )
        
        return response.json()
    
    def simple_search(self, query: str, **kwargs):
        """Executa busca simples"""
        data = {"query": query, **kwargs}
        
        response = requests.post(
            f"{self.base_url}/api/v1/simple",
            json=data,
            headers=self.headers,
            timeout=30
        )
        
        return response.json()

# Uso
client = RAGMultiAgentClient(
    base_url="http://localhost:8000",
    api_token="your_bearer_token"
)

# Pesquisa multi-agente
result = client.multi_agent_research(
    "Como Zep se compara com MemGPT?",
    max_subagents=3,
    focus_areas=["comparative", "technical"]
)

print(result["result"])
```

### JavaScript/Node.js Example
```javascript
class RAGMultiAgentClient {
    constructor(baseUrl, apiToken) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiToken}`,
            'Content-Type': 'application/json'
        };
    }
    
    async multiAgentResearch(query, options = {}) {
        const data = { query, use_multiagent: true, ...options };
        
        const response = await fetch(`${this.baseUrl}/api/v1/research`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return await response.json();
    }
}

// Uso
const client = new RAGMultiAgentClient(
    'http://localhost:8000',
    'your_bearer_token'
);

const result = await client.multiAgentResearch(
    'Explique temporal knowledge graphs no Zep',
    { max_subagents: 3 }
);

console.log(result.result);
```

---

## 📚 Links Relacionados

- [⚡ Quick Start](quick-start.md) - Setup rápido
- [🤖 Sistema Multi-Agente](multi-agent.md) - Como funciona internamente
- [🔧 Configuração](configuration.md) - Configurações avançadas
- [🚀 Deployment](deployment.md) - Deploy em produção
- [🔧 Troubleshooting](troubleshooting.md) - Resolução de problemas