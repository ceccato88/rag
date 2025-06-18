# 💡 Exemplos Práticos - RAG Multi-Agente

## 🚀 Exemplos de Uso Básico

### 1. **Busca Simples com API**

#### Usando curl
```bash
# Busca básica
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como configurar autenticação OAuth?",
    "max_results": 5
  }'
```

#### Resposta esperada
```json
{
  "results": [
    {
      "content": "Para configurar OAuth, você precisa...",
      "source": "documento_auth.pdf",
      "score": 0.95,
      "metadata": {
        "page": 15,
        "section": "Autenticação"
      }
    }
  ],
  "query_time": 0.45,
  "total_results": 12
}
```

### 2. **Chat Interativo**

#### Exemplo com Python
```python
import requests

def chat_with_rag(query: str):
    response = requests.post(
        "http://localhost:8000/chat",
        json={
            "message": query,
            "session_id": "user_123",
            "context_window": 5
        }
    )
    return response.json()

# Uso
result = chat_with_rag("Explique microserviços")
print(result["response"])
```

### 3. **Pesquisa Multi-Agente Avançada**

#### Script completo
```python
#!/usr/bin/env python3
"""
Exemplo de pesquisa multi-agente completa
"""
import requests
import json
from typing import Dict, Any

class RAGMultiAgentClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def research(self, topic: str, depth: str = "standard") -> Dict[str, Any]:
        """
        Executa pesquisa multi-agente
        
        Args:
            topic: Tópico a pesquisar
            depth: Profundidade (quick, standard, deep)
        """
        payload = {
            "query": topic,
            "research_depth": depth,
            "include_sources": True,
            "max_agents": 3
        }
        
        response = requests.post(f"{self.base_url}/research", json=payload)
        return response.json()
    
    def get_research_status(self, research_id: str) -> Dict[str, Any]:
        """Verifica status de pesquisa em andamento"""
        response = requests.get(f"{self.base_url}/research/{research_id}/status")
        return response.json()

# Exemplo de uso
if __name__ == "__main__":
    client = RAGMultiAgentClient()
    
    # Pesquisa detalhada
    result = client.research(
        topic="Implementação de APIs REST escaláveis",
        depth="deep"
    )
    
    print(f"Resultado: {result['summary']}")
    print(f"Fontes: {len(result['sources'])} documentos consultados")
    print(f"Confiança: {result['confidence_score']}")
```

## 🎯 Casos de Uso Específicos

### 1. **Análise de Documentação Técnica**

```python
"""
Exemplo: Análise de documentação de API
"""
def analyze_api_documentation():
    query = """
    Analise a documentação da API e forneça:
    1. Endpoints principais e suas funções
    2. Métodos de autenticação suportados
    3. Exemplos de requests/responses
    4. Limitações e rate limits
    5. Códigos de erro comuns
    """
    
    response = requests.post("http://localhost:8000/research", json={
        "query": query,
        "focus_areas": ["endpoints", "authentication", "examples", "errors"],
        "output_format": "structured"
    })
    
    return response.json()

# Uso
analysis = analyze_api_documentation()
print(f"Análise completa: {analysis['structured_output']}")
```

### 2. **Pesquisa Acadêmica Colaborativa**

```python
"""
Exemplo: Pesquisa sobre Machine Learning
"""
def academic_research():
    query = """
    Realize uma pesquisa abrangente sobre:
    - Estado da arte em transformers para NLP
    - Comparação de arquiteturas (BERT, GPT, T5)
    - Aplicações práticas e limitações
    - Tendências futuras e pesquisas emergentes
    """
    
    response = requests.post("http://localhost:8000/research", json={
        "query": query,
        "research_type": "academic",
        "citation_style": "APA",
        "include_metrics": True
    })
    
    return response.json()

# Executar pesquisa
research_result = academic_research()

# Salvar relatório
with open("research_report.md", "w") as f:
    f.write(research_result["detailed_report"])
```

### 3. **Troubleshooting Assistido**

```python
"""
Exemplo: Diagnóstico de problemas
"""
def troubleshoot_issue():
    problem_description = """
    Estou enfrentando timeout na API após deploy.
    Contexto:
    - API FastAPI com 1000 req/min
    - Usando ChromaDB local
    - Deploy em Docker
    - Logs mostram 'Connection timeout'
    """
    
    response = requests.post("http://localhost:8000/research", json={
        "query": problem_description,
        "research_type": "troubleshooting",
        "priority": "high",
        "include_solutions": True
    })
    
    return response.json()

# Diagnóstico
diagnosis = troubleshoot_issue()

print("🔧 Possíveis causas:")
for cause in diagnosis["possible_causes"]:
    print(f"  - {cause}")

print("\n💡 Soluções sugeridas:")
for solution in diagnosis["suggested_solutions"]:
    print(f"  - {solution}")
```

## 🔧 Integração com Aplicações

### 1. **Chatbot Web com Streamlit**

```python
import streamlit as st
import requests

st.title("🤖 RAG Multi-Agent Assistant")

# Interface do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Faça sua pergunta..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Pesquisando..."):
            response = requests.post("http://localhost:8000/chat", json={
                "message": prompt,
                "session_id": st.session_state.get("session_id"),
                "stream": False
            })
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["response"]
                
                st.markdown(ai_response)
                
                # Show sources if available
                if "sources" in result and result["sources"]:
                    with st.expander("📚 Fontes consultadas"):
                        for source in result["sources"]:
                            st.write(f"- {source['filename']} (Score: {source['score']:.2f})")
                
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                st.error("Erro na comunicação com a API")
```

### 2. **CLI Tool Interativo**

```python
#!/usr/bin/env python3
"""
CLI interativo para RAG Multi-Agent
"""
import click
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

@click.group()
def cli():
    """RAG Multi-Agent CLI Tool"""
    pass

@cli.command()
@click.argument('query')
@click.option('--depth', default='standard', help='Research depth (quick/standard/deep)')
@click.option('--format', default='text', help='Output format (text/json/markdown)')
def research(query, depth, format):
    """Execute multi-agent research"""
    console.print(f"🔍 Pesquisando: [bold]{query}[/bold]")
    
    response = requests.post("http://localhost:8000/research", json={
        "query": query,
        "research_depth": depth
    })
    
    if response.status_code == 200:
        result = response.json()
        
        if format == 'json':
            console.print_json(data=result)
        elif format == 'markdown':
            console.print(result.get('markdown_report', ''))
        else:
            console.print(f"\n📊 [bold]Resultado:[/bold]\n{result['summary']}")
            
            # Show sources table
            if result.get('sources'):
                table = Table(title="Fontes Consultadas")
                table.add_column("Documento", style="cyan")
                table.add_column("Score", style="magenta")
                table.add_column("Página", style="green")
                
                for source in result['sources'][:5]:
                    table.add_row(
                        source['filename'],
                        f"{source['score']:.2f}",
                        str(source.get('page', 'N/A'))
                    )
                
                console.print(table)
    else:
        console.print(f"❌ Erro: {response.status_code}")

@cli.command()
def health():
    """Check API health"""
    response = requests.get("http://localhost:8000/health")
    
    if response.status_code == 200:
        data = response.json()
        console.print("✅ API está funcionando")
        console.print_json(data=data)
    else:
        console.print("❌ API não está respondendo")

if __name__ == '__main__':
    cli()
```

### 3. **Jupyter Notebook Integration**

```python
# Cell 1: Setup
import requests
import pandas as pd
from IPython.display import display, Markdown
import matplotlib.pyplot as plt

class RAGNotebookHelper:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
    
    def search(self, query, max_results=10):
        response = requests.post(f"{self.api_url}/search", json={
            "query": query,
            "max_results": max_results
        })
        return response.json()
    
    def display_results(self, results):
        df = pd.DataFrame([
            {
                "Score": r["score"],
                "Source": r["source"],
                "Content": r["content"][:100] + "..."
            }
            for r in results["results"]
        ])
        display(df)
    
    def plot_scores(self, results):
        scores = [r["score"] for r in results["results"]]
        sources = [r["source"] for r in results["results"]]
        
        plt.figure(figsize=(10, 6))
        plt.barh(sources, scores)
        plt.xlabel("Relevance Score")
        plt.title("Document Relevance Scores")
        plt.tight_layout()
        plt.show()

# Cell 2: Usage
rag = RAGNotebookHelper()

query = "Como implementar cache distribuído?"
results = rag.search(query)

display(Markdown(f"## Resultados para: '{query}'"))
rag.display_results(results)
rag.plot_scores(results)
```

## 📊 Monitoramento e Analytics

### 1. **Dashboard de Métricas**

```python
"""
Dashboard simples com Streamlit
"""
import streamlit as st
import requests
import plotly.express as px

def get_metrics():
    response = requests.get("http://localhost:8000/metrics")
    return response.json()

st.title("📊 RAG Multi-Agent Dashboard")

# Métricas em tempo real
col1, col2, col3, col4 = st.columns(4)

metrics = get_metrics()

with col1:
    st.metric("Queries/hora", metrics["queries_per_hour"])

with col2:
    st.metric("Latência média", f"{metrics['avg_latency']:.2f}s")

with col3:
    st.metric("Cache Hit Rate", f"{metrics['cache_hit_rate']:.1%}")

with col4:
    st.metric("Agentes ativos", metrics["active_agents"])

# Gráficos
query_history = metrics["query_history"]
df = pd.DataFrame(query_history)

fig = px.line(df, x="timestamp", y="latency", title="Latência ao longo do tempo")
st.plotly_chart(fig)
```

### 2. **Análise de Performance**

```python
"""
Script para análise de performance
"""
import requests
import time
import statistics

def benchmark_api(queries, iterations=10):
    results = []
    
    for query in queries:
        latencies = []
        
        for _ in range(iterations):
            start = time.time()
            
            response = requests.post("http://localhost:8000/search", json={
                "query": query,
                "max_results": 5
            })
            
            latency = time.time() - start
            latencies.append(latency)
        
        results.append({
            "query": query,
            "avg_latency": statistics.mean(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "std_dev": statistics.stdev(latencies)
        })
    
    return results

# Benchmark queries
test_queries = [
    "Como configurar Docker?",
    "Explicar arquitetura microserviços",
    "Tutorial de FastAPI",
    "Implementar autenticação JWT"
]

benchmark_results = benchmark_api(test_queries)

for result in benchmark_results:
    print(f"Query: {result['query']}")
    print(f"  Latência média: {result['avg_latency']:.3f}s")
    print(f"  Min/Max: {result['min_latency']:.3f}s / {result['max_latency']:.3f}s")
    print(f"  Desvio padrão: {result['std_dev']:.3f}s")
    print()
```

## 🧪 Testes e Validação

### 1. **Teste de Integração**

```python
"""
Teste completo do sistema
"""
import pytest
import requests

class TestRAGMultiAgent:
    
    @pytest.fixture
    def api_url(self):
        return "http://localhost:8000"
    
    def test_health_check(self, api_url):
        response = requests.get(f"{api_url}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_simple_search(self, api_url):
        response = requests.post(f"{api_url}/search", json={
            "query": "teste de documentação",
            "max_results": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) <= 3
    
    def test_multi_agent_research(self, api_url):
        response = requests.post(f"{api_url}/research", json={
            "query": "Como otimizar performance de APIs?",
            "research_depth": "quick"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "sources" in data
        assert "confidence_score" in data
    
    def test_chat_functionality(self, api_url):
        response = requests.post(f"{api_url}/chat", json={
            "message": "Olá, como você funciona?",
            "session_id": "test_session"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0

# Executar testes
if __name__ == "__main__":
    pytest.main([__file__])
```

### 2. **Validação de Qualidade**

```python
"""
Validação da qualidade das respostas
"""
def evaluate_response_quality(query: str, response: str) -> dict:
    """
    Avalia qualidade da resposta usando métricas automáticas
    """
    metrics = {}
    
    # Relevância (usando embedding similarity)
    query_embedding = get_embedding(query)
    response_embedding = get_embedding(response)
    metrics["relevance"] = cosine_similarity(query_embedding, response_embedding)
    
    # Completude (baseada no tamanho e estrutura)
    metrics["completeness"] = min(len(response) / 500, 1.0)  # Normalizado
    
    # Coerência (usando análise de sentimento e coesão)
    metrics["coherence"] = analyze_coherence(response)
    
    # Score geral
    metrics["overall_score"] = (
        metrics["relevance"] * 0.4 +
        metrics["completeness"] * 0.3 +
        metrics["coherence"] * 0.3
    )
    
    return metrics

# Teste de qualidade
test_cases = [
    {
        "query": "Como implementar cache Redis?",
        "expected_topics": ["Redis", "cache", "implementação", "configuração"]
    },
    {
        "query": "Explicar arquitetura de microserviços",
        "expected_topics": ["microserviços", "arquitetura", "vantagens", "desvantagens"]
    }
]

for case in test_cases:
    response = requests.post("http://localhost:8000/search", json={
        "query": case["query"]
    })
    
    quality_metrics = evaluate_response_quality(
        case["query"], 
        response.json()["results"][0]["content"]
    )
    
    print(f"Query: {case['query']}")
    print(f"Quality Score: {quality_metrics['overall_score']:.2f}")
    print(f"Relevance: {quality_metrics['relevance']:.2f}")
    print(f"Completeness: {quality_metrics['completeness']:.2f}")
    print(f"Coherence: {quality_metrics['coherence']:.2f}")
    print("-" * 50)
```
