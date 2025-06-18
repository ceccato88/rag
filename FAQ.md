# ❓ FAQ - Perguntas Frequentes

## 🚀 **Instalação e Configuração**

### **Q: Como instalar o sistema rapidamente?**
```bash
# Método mais rápido
source .venv/bin/activate
python install.py
```

### **Q: Quais APIs keys eu preciso?**
Você precisa de 3 chaves:
- **OpenAI API Key**: https://platform.openai.com/api-keys
- **Voyage AI Key**: https://www.voyageai.com/
- **Astra DB Token**: https://astra.datastax.com/

### **Q: Onde configurar as chaves?**
```bash
# 1. Copiar template
cp .env.example .env

# 2. Editar arquivo .env
OPENAI_API_KEY=sk-proj-sua_chave_aqui
VOYAGE_API_KEY=pa-sua_chave_aqui
ASTRA_DB_API_ENDPOINT=https://seu-db-id.apps.astra.datastax.com
ASTRA_DB_APPLICATION_TOKEN=AstraCS:sua_token_aqui
```

### **Q: Como verificar se está tudo configurado?**
```bash
source .venv/bin/activate
python diagnostico_simples.py
```

---

## 🔧 **Uso do Sistema**

### **Q: Qual a diferença entre as duas APIs?**

| Aspecto | API Simples | Multi-Agente |
|---------|-------------|--------------|
| **Porta** | 8000 | 8001 |
| **Tempo** | 5-30s | 30-300s |
| **Uso** | Consultas diretas | Análises complexas |
| **Exemplo** | "O que é IA?" | "Compare TensorFlow vs PyTorch" |

### **Q: Como fazer minha primeira consulta?**
```python
import requests

# API Simples (consultas rápidas)
response = requests.post("http://localhost:8000/search", json={
    "query": "O que é machine learning?"
})
print(response.json()["response"])

# Multi-Agente (análises complexas)
response = requests.post("http://localhost:8001/research", json={
    "query": "Compare metodologias ágeis vs waterfall",
    "processing_mode": "sync"
})
print(response.json()["final_answer"])
```

### **Q: Como usar via linha de comando?**
```bash
# Sistema interativo
source .venv/bin/activate
python search.py

# Comandos na interface:
# /help - ajuda
# /clear - limpa histórico
# /stats - estatísticas
# sair - finaliza
```

---

## ⚠️ **Problemas Comuns**

### **Q: "ModuleNotFoundError" ao importar**
```bash
# Solução: ativar ambiente virtual
source .venv/bin/activate
```

### **Q: "API key not found"**
```bash
# Verificar se .env existe e tem as chaves
ls -la .env
cat .env | grep API_KEY
```

### **Q: "Connection timeout" ou "API não responde"**
```bash
# 1. Verificar se APIs estão rodando
curl http://localhost:8000/health
curl http://localhost:8001/health

# 2. Verificar se portas estão livres
netstat -tulpn | grep :8000
netstat -tulpn | grep :8001

# 3. Reiniciar APIs
python api_simple.py      # Terminal 1
python api_multiagent.py  # Terminal 2
```

### **Q: "Timeout na consulta" ou muito lento**
Ajustar timeouts no .env:
```bash
# Para consultas mais rápidas (menos precisão)
MULTIAGENT_TIMEOUT=60
MAX_SUBAGENTS=2

# Para consultas mais precisas (mais tempo)
MULTIAGENT_TIMEOUT=300
MAX_SUBAGENTS=5
```

### **Q: "Erro de memória" ou "Out of memory"**
```bash
# Reduzir concorrência
MAX_SUBAGENTS=2
PROCESSING_CONCURRENCY=3
EMBEDDING_CACHE_SIZE=200
```

---

## 🚀 **Deploy e Produção**

### **Q: Como colocar em produção?**
```bash
# Método 1: Docker (recomendado)
docker-compose up -d

# Método 2: Manual
python api_simple.py &      # Background
python api_multiagent.py &  # Background
```

### **Q: Como monitorar o sistema?**
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8001/health

# Métricas
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics

# Jobs ativos (multi-agente)
curl http://localhost:8001/jobs

# Logs
docker-compose logs -f  # Se usando Docker
tail -f logs/*.log      # Se manual
```

### **Q: Como configurar SSL/HTTPS?**
Configure no nginx.conf ou use proxy reverso:
```nginx
server {
    listen 443 ssl;
    server_name seu-dominio.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location /api/simple/ {
        proxy_pass http://localhost:8000/;
    }
    
    location /api/multiagent/ {
        proxy_pass http://localhost:8001/;
    }
}
```

---

## 💰 **Custos e Performance**

### **Q: Quanto custa usar o sistema?**
Custos aproximados (baseado nos modelos configurados):

**OpenAI GPT-4:**
- API Simples: ~$0.03 por consulta
- Multi-Agente: ~$0.10-0.30 por consulta

**Voyage AI:**
- ~$0.10 por 1 milhão de tokens
- Consulta típica: ~500 tokens = $0.00005

**Astra DB:**
- Tier gratuito: 5GB, 20M operações/mês
- Tier pago: $0.10 por milhão de operações

### **Q: Como otimizar custos?**
```bash
# Usar modelos mais baratos
RAG_LLM_MODEL=gpt-4o-mini-2024-07-18
MULTIAGENT_MODEL=gpt-4o-mini-2024-07-18

# Reduzir candidatos
MAX_CANDIDATES=3

# Aumentar cache
EMBEDDING_CACHE_SIZE=1000
EMBEDDING_CACHE_TTL=7200
```

### **Q: Como melhorar performance?**
```bash
# Para velocidade máxima
RAG_LLM_MODEL=gpt-4o-mini-2024-07-18
MAX_CANDIDATES=3
MAX_SUBAGENTS=2
PROCESSING_CONCURRENCY=8

# Para qualidade máxima
RAG_LLM_MODEL=gpt-4o-2024-11-20
MAX_CANDIDATES=10
MAX_SUBAGENTS=5
SIMILARITY_THRESHOLD=0.8
```

---

## 🔧 **Desenvolvimento e Customização**

### **Q: Como adicionar novos documentos?**
```bash
# Indexar novo PDF
source .venv/bin/activate
DEFAULT_PDF_URL=https://exemplo.com/documento.pdf python indexer.py

# Indexar arquivo local
DEFAULT_PDF_URL=meu_arquivo.pdf python indexer.py
```

### **Q: Como modificar os modelos usados?**
Edite o arquivo .env:
```bash
# Modelos disponíveis
RAG_LLM_MODEL=gpt-4o-2024-11-20           # Melhor qualidade
RAG_LLM_MODEL=gpt-4o-mini-2024-07-18      # Mais rápido/barato
RAG_EMBEDDING_MODEL=voyage-3               # Texto
VOYAGE_MULTIMODAL_MODEL=voyage-multimodal-3 # Texto + imagem
```

### **Q: Como adicionar novos agentes especializados?**
Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes, mas basicamente:
1. Criar novo agente em `multi-agent-researcher/src/researcher/agents/`
2. Herdar de `EnhancedRAGSubagent`
3. Implementar `adapt_query_for_specialty()`
4. Registrar no sistema

### **Q: Como acessar logs detalhados?**
```bash
# Ativar debug no .env
API_LOG_LEVEL=debug

# Logs específicos
tail -f rag_production_debug.log
tail -f logs/api_simple.log
tail -f logs/api_multiagent.log
```

---

## 📊 **Integração e APIs**

### **Q: Como integrar com minha aplicação?**
```python
# Exemplo de classe wrapper
import requests

class RAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def search(self, query, max_results=5):
        response = requests.post(f"{self.base_url}/search", json={
            "query": query,
            "max_results": max_results
        })
        return response.json()

# Uso
client = RAGClient()
result = client.search("Como implementar machine learning?")
```

### **Q: Como usar WebSocket para streaming?**
```javascript
const ws = new WebSocket('ws://localhost:8001/research/stream');

ws.onopen = function() {
    ws.send(JSON.stringify({
        query: "Análise detalhada de quantum computing",
        processing_mode: "stream"
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Resultado:', data);
};
```

### **Q: Como tratar erros da API?**
```python
try:
    response = requests.post("http://localhost:8000/search", 
                           json={"query": "test"}, 
                           timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(result["response"])
    elif response.status_code == 422:
        print("Erro de validação:", response.json())
    elif response.status_code == 500:
        print("Erro interno do servidor")
    else:
        print(f"Erro: {response.status_code}")
        
except requests.exceptions.Timeout:
    print("Timeout - consulta muito lenta")
except requests.exceptions.ConnectionError:
    print("Erro de conexão - API não está rodando?")
```

---

## 🎯 **Casos de Uso Específicos**

### **Q: Como analisar documentos acadêmicos?**
Use a API Multi-Agente com configuração para qualidade:
```python
response = requests.post("http://localhost:8001/research", json={
    "query": "Analise a metodologia e resultados deste paper sobre deep learning",
    "objective": "Análise acadêmica detalhada",
    "processing_mode": "sync",
    "include_reasoning": True
})
```

### **Q: Como fazer comparações técnicas?**
```python
response = requests.post("http://localhost:8001/research", json={
    "query": "Compare as vantagens e desvantagens de React vs Vue.js",
    "objective": "Comparação técnica para decisão de projeto",
    "processing_mode": "sync"
})
```

### **Q: Como buscar exemplos práticos?**
```python
response = requests.post("http://localhost:8000/search", json={
    "query": "Exemplo prático de implementação de neural network",
    "max_results": 10,
    "similarity_threshold": 0.7
})
```

---

## 🆘 **Ainda com Problemas?**

### **Recursos Adicionais:**
- **Troubleshooting Detalhado**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Guia de Arquitetura**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Exemplos Avançados**: [docs/EXAMPLES.md](docs/EXAMPLES.md)
- **Como Contribuir**: [CONTRIBUTING.md](CONTRIBUTING.md)

### **Diagnóstico Completo:**
```bash
source .venv/bin/activate
python validacao_documentacao.py
```

### **Reset Completo do Sistema:**
```bash
# Para em caso de problemas graves
docker-compose down
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
python install.py
```

---

**💡 Não encontrou sua pergunta? Abra uma issue ou contribua com este FAQ!**
