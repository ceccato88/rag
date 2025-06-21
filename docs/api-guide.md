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

**Descrição**: Pesquisa avançada com sistema multi-agente enhanced e síntese crítica.

**Request**:
```json
{
  "query": "Como Zep implementa temporal knowledge graphs para memória de agentes AI?",
  "focus_areas": ["conceptual", "technical", "examples"],
  "timeout": 300
}
```

**Response**:
```json
{
  "success": true,
  "query": "Como Zep implementa temporal knowledge graphs...",
  "result": "# 🤖 Enhanced Multi-Agent Research Synthesis\n\n**Coordinator Model**: gpt-4.1\n**Synthesis Method**: Enhanced AI Critical Analysis\n**Specialists Used**: 3 (CONCEPTUAL, TECHNICAL, EXAMPLES)\n**Timestamp**: 2025-06-19 23:46:44\n\n---\n\n## Resumo Executivo\n\nEsta análise compara criticamente...",
  "agent_id": "abc-123-def-456",
  "status": "COMPLETED",
  "processing_time": 24.5,
  "timestamp": "2025-06-19T23:46:44.123456",
  "confidence_score": 0.87,
  "sources": [],
  "reasoning_trace": "=== Trace de Raciocínio - OpenAI Lead Researcher (abc-123) ===\n\n🔍 Passo 1: FACT_GATHERING\n⏰ 23:46:12\n💭 Coletando fatos para: Research planning for Zep temporal knowledge graphs\n👁️ Observações: Query complexity: high, Technical depth: high\n➡️ Próxima ação: Analisar fatos dados e relembrar conhecimento relevante\n\n──────────────────────────────────────────────────\n\n🔍 Passo 2: PLANNING\n⏰ 23:46:13\n💭 Criando plano para: Create comprehensive research plan for Zep temporal KG\n👁️ Observações: Recursos disponíveis: ['OpenAI gpt-4.1-mini', 'RAG subagents']\n➡️ Próxima ação: Desenvolver plano estruturado em etapas\n\n──────────────────────────────────────────────────\n\n🔍 Passo 3: EXECUTION\n⏰ 23:46:14\n💭 Executando: LLM-based decomposition informed by ReAct reasoning\n👁️ Observações: Integrating manual reasoning with gpt-4.1-mini for optimal focus area selection\n➡️ Próxima ação: Avaliar resultado e determinar próximo passo",
  "error": null
}
```

**Parâmetros**:
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `query` | string | ✅ | Query de pesquisa |
| `focus_areas` | array | ❌ | Areas de foco específicas |
| `max_specialists` | integer | ❌ | Máximo de especialistas (padrão: 3) |
| `timeout` | integer | ❌ | Timeout em segundos (padrão: 300) |

**Nota**: O parâmetro `include_reasoning` foi removido pois o reasoning está **sempre habilitado** por padrão no sistema enhanced.

**Exemplo cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explique as vantagens do Zep vs MemGPT para aplicações empresariais",
    "focus_areas": ["comparative", "applications", "technical"]
  }'
```

### 2. 🔍 Simple Search

**Endpoint**: `POST /api/v1/research`

**Descrição**: Busca RAG simples e direta, usando o endpoint unificado.

**Request**:
```json
{
  "query": "O que é Zep?",
  "max_candidates": 5
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
curl -X POST "http://localhost:8000/api/v1/research" \
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
  "uptime_seconds": 3712.6,    "components": {
      "database": true,
      "simple_rag": true,
      "enhanced_system": true
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
    "enhanced_queries": 20,
    "simple_queries": 5,
    "average_processing_time": 12.3
  },
  "specialist_stats": {
    "total_specialists_used": 60,
    "successful_executions": 58,
    "failed_executions": 2,
    "specialist_distribution": {
      "CONCEPTUAL": 18,
      "TECHNICAL": 22,
      "COMPARATIVE": 15,
      "EXAMPLES": 12,
      "GENERAL": 8
    }
  },
  "model_usage": {
    "coordinator_calls": 20,
    "specialist_calls": 60,
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
  "focus_areas": ["technical", "examples"], // Forçar focus areas específicas
  "max_specialists": 3,                // 1-5, padrão: 3
  "timeout": 300,                      // Segundos, padrão: 300
  "complexity": "auto",                // "simple"|"moderate"|"complex"|"very_complex"|"auto"
  "synthesis_model": "gpt-4.1",       // Override coordinator model
  "parallel_execution": true          // true|false, padrão: true
}

**Nota**: O reasoning está sempre habilitado - não é necessário especificar `include_reasoning`.
```

### Simple Search Parameters

```json
{
  "query": "string",                   // Obrigatório
  "max_candidates": 5,                // 1-10, padrão: varies by complexity
  "similarity_threshold": 0.7,        // 0.0-1.0, padrão: varies by specialist
  "include_images": false             // true|false, padrão: false
}
```

## 🎯 Focus Areas na API

### Seleção Automática de Especialistas
```json
{
  "query": "O que é Zep?"
}
// ⬇️ Sistema detecta padrões "O que é" → Seleciona CONCEPTUAL
// ⬇️ CONCEPTUAL automaticamente usa focus_area: "conceptual"
```

### Seleção Múltipla (Query Complexa)
```json
{
  "query": "Compare Zep vs MemGPT para implementação em chatbots"
}
// ⬇️ Sistema detecta: "Compare" → COMPARATIVE + "implementação" → TECHNICAL
// ⬇️ 2 especialistas executam em paralelo com focus areas correspondentes
```

### Override Manual (Opcional)
```json
{
  "query": "Compare Zep vs MemGPT",
  "focus_areas": ["comparative", "technical", "applications"]
}
// ⬇️ Força os focus areas especificados (bypassa seleção automática)
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
# 🤖 Enhanced Multi-Agent Research Synthesis

**Coordinator Model**: gpt-4.1
**Synthesis Method**: Enhanced AI Critical Analysis  
**Specialists Used**: 3 (CONCEPTUAL, TECHNICAL, EXAMPLES)
**Query Complexity**: MODERATE
**ReAct Reasoning**: ENABLED (sempre ativo)
**Timestamp**: 2025-06-19 23:46:44

---

## Resumo Executivo
[Síntese crítica dos achados]

## Achados Principais
### 1. [Specialist: CONCEPTUAL] 
[Resultados específicos]

### 2. [Specialist: TECHNICAL]
[Resultados específicos]

---

## 📊 Research Metadata
- **Complexity Detection**: Auto-detected as MODERATE
- **Total Specialists**: 3
- **Success Rate**: 3/3 (100%)
- **AI Models**: Specialists (gpt-4.1-mini) + Coordinator (gpt-4.1)
- **Reasoning Steps**: 12 (fact_gathering, planning, execution, validation)
```

### Response Fields
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `success` | boolean | Status da operação |
| `query` | string | Query original processada |
| `result` | string | Síntese final estruturada |
| `agent_id` | string | ID único do agente coordenador |
| `status` | string | Estado final (COMPLETED/FAILED) |
| `processing_time` | float | Tempo total em segundos |
| `timestamp` | string | Timestamp ISO da conclusão |
| `confidence_score` | float | Nível de confiança do reasoning (0.0-1.0) |
| `sources` | array | Fontes dos documentos consultados |
| `reasoning_trace` | string | **Trace completo do ReAct reasoning (sempre presente)** |
| `error` | string/null | Mensagem de erro se houver falha |

### Quality Indicators
- **Coordinator Model**: `gpt-4.1` ← Síntese avançada ativada
- **Success Rate**: `100%` ← Todos especialistas executaram
- **Processing Time**: `< 30s` ← Performance aceitável
- **Synthesis Method**: `Enhanced AI Critical Analysis` ← Reasoning sofisticado
- **Query Complexity**: `MODERATE` ← Detecção automática de complexidade
- **Confidence Score**: `0.87` ← Alta confiança no reasoning
- **Reasoning Trace**: `Sempre presente` ← Rastreabilidade completa

## 🧠 Reasoning Trace (Sempre Habilitado)

O sistema enhanced **sempre** inclui o trace completo do ReAct reasoning no response, fornecendo transparência total sobre o processo de tomada de decisão.

### Estrutura do Reasoning Trace
```
=== Trace de Raciocínio - OpenAI Lead Researcher (agent-id) ===

🔍 Passo 1: FACT_GATHERING
⏰ 23:46:12
💭 Coletando fatos para: Research planning for [query]
👁️ Observações: Query complexity: [level], Technical depth: [level]
➡️ Próxima ação: Analisar fatos dados e relembrar conhecimento relevante

──────────────────────────────────────────────────

🔍 Passo 2: PLANNING
⏰ 23:46:13
💭 Criando plano para: Create comprehensive research plan
👁️ Observações: Recursos disponíveis: ['OpenAI gpt-4.1-mini', 'RAG subagents']
➡️ Próxima ação: Desenvolver plano estruturado em etapas

──────────────────────────────────────────────────

🔍 Passo 3: EXECUTION
⏰ 23:46:14
💭 Executando: LLM-based/Heuristic decomposition
👁️ Observações: Integrating reasoning with optimal focus area selection
➡️ Próxima ação: Avaliar resultado e determinar próximo passo

──────────────────────────────────────────────────

🔍 Passo 4: VALIDATION
⏰ 23:46:15
💭 Final reasoning validation: Consistent
👁️ Observações: Confidence: 0.87, Progress: All steps completed successfully
➡️ Próxima ação: Processo concluído com sucesso
```

### Tipos de Steps do Reasoning
| Step Type | Descrição | Momento |
|-----------|-----------|---------|
| `FACT_GATHERING` | Coleta de fatos e contexto | Início do planejamento |
| `PLANNING` | Criação do plano estruturado | Após fact gathering |
| `EXECUTION` | Execução de subagentes | Durante processamento |
| `VALIDATION` | Validação do progresso | Várias etapas |
| `SYNTHESIS` | Síntese final avançada | Coordenação de resultados |
| `REFLECTION` | Reflexão sobre problemas | Quando necessário |

### Usando o Reasoning Trace
```python
# Exemplo de análise do trace
response = client.multi_agent_research("Como implementar Zep?")

# Trace completo
trace = response["reasoning_trace"]
print("TRACE COMPLETO:")
print(trace)

# Análise de confiança
confidence = response["confidence_score"]
print(f"\nCONFIANÇA: {confidence:.2f}")

# Verificar se houve reflexões (indicam problemas)
if "REFLECTION" in trace:
    print("⚠️ ATENÇÃO: Reasoning teve que se ajustar durante execução")
else:
    print("✅ SUCESSO: Reasoning executou sem problemas")
```

### Benefícios do Reasoning Sempre Ativo
1. **Transparência**: Veja exatamente como o sistema tomou decisões
2. **Debugging**: Identifique problemas no processo de reasoning
3. **Confiança**: Avalie a qualidade do raciocínio antes de usar resultados
4. **Auditoria**: Trace completo para compliance e governança
5. **Otimização**: Identifique padrões para melhorar queries futuras

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
        """Executa pesquisa multi-agente enhanced"""
        data = {"query": query, **kwargs}
        
        response = requests.post(
            f"{self.base_url}/api/v1/research",
            json=data,
            headers=self.headers,
            timeout=60
        )
        
        return response.json()
    
    def simple_search(self, query: str, **kwargs):
        """Executa busca simples via API unificada"""
        data = {"query": query, **kwargs}
        
        response = requests.post(
            f"{self.base_url}/api/v1/research",
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

# Pesquisa multi-agente enhanced
result = client.multi_agent_research(
    "Como Zep se compara com MemGPT?",
    focus_areas=["comparative", "technical"],
    max_specialists=3
)

print(result["result"])
print("\n--- TRACE DE REASONING (SEMPRE PRESENTE) ---")
print(result["reasoning_trace"])
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
        const data = { query, ...options };
        
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
    { 
        focus_areas: ['conceptual', 'technical'], 
        max_specialists: 3
    }
);

console.log(result.result);
console.log('\n--- TRACE DE REASONING (SEMPRE PRESENTE) ---');
console.log(result.reasoning_trace);
```

---

## 📚 Links Relacionados

- [⚡ Quick Start](quick-start.md) - Setup rápido
- [🤖 Sistema Multi-Agente](multi-agent.md) - Como funciona internamente
- [� Sistema Enhanced](enhanced-system.md) - Detalhes do sistema enhanced
- [🏗️ Arquitetura](architecture.md) - Arquitetura do sistema
- [� ReAct Reasoning](reasoning.md) - Sistema de reasoning
- [🧪 Testing](testing.md) - Testes e validação