# ⚡ QUICKSTART - Sistema RAG Multi-Agente

## 🎯 Execução em 3 Passos

### **1️⃣ Instalar**
```bash
# Ativar ambiente virtual primeiro
source .venv/bin/activate

# Instalar dependências
python install.py
```

### **2️⃣ Executar**
```bash
# Manter ambiente virtual ativo
source .venv/bin/activate

# Terminal 1: API RAG Simples
python api_simple.py

# Terminal 2: API Multi-Agente  
python api_multiagent.py
```

### **3️⃣ Testar**
```bash
# Ambiente virtual ativo
source .venv/bin/activate

python example_api_client.py
```

---

## 🔥 Exemplos Rápidos

### **📊 API RAG Simples**
```python
# Ativar ambiente virtual primeiro: source .venv/bin/activate
import requests

response = requests.post("http://localhost:8000/search", json={
    "query": "O que é machine learning?"
})

print(response.json()["response"])
```

### **🤖 API Multi-Agente**
```python
# Ambiente virtual deve estar ativo
import requests

response = requests.post("http://localhost:8001/research", json={
    "query": "Compare TensorFlow vs PyTorch",
    "processing_mode": "sync"
})

print(response.json()["final_answer"])
```

---

## 📚 Recursos

- **Documentação**: `README.md`
- **APIs**: `API_USAGE.md` 
- **Dependências**: `DEPENDENCIES.md`
- **Setup Completo**: `SETUP_FINAL.md`

## 🚨 Problemas?

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Testar configuração
python test_api_config.py

# Ver logs (se usando Docker)
docker-compose logs -f
```

---

## 🎯 URLs Principais

- **API Simples**: http://localhost:8000
- **Multi-Agente**: http://localhost:8001
- **Docs Simples**: http://localhost:8000/docs
- **Docs Multi**: http://localhost:8001/docs
- **Dashboard**: http://localhost/ (com Nginx)

**🚀 Sistema pronto para produção!**