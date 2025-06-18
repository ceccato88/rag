# ⚡ QUICKSTART - Sistema RAG Multi-Agente

## 🎯 Execução em 3 Passos

### **1️⃣ Instalar**
```bash
python install.py
```

### **2️⃣ Executar**
```bash
# Terminal 1: API RAG Simples
python api_simple.py

# Terminal 2: API Multi-Agente  
python api_multiagent.py
```

### **3️⃣ Testar**
```bash
python example_api_client.py
```

---

## 🔥 Exemplos Rápidos

### **📊 API RAG Simples**
```python
import requests

response = requests.post("http://localhost:8000/search", json={
    "query": "O que é machine learning?"
})

print(response.json()["response"])
```

### **🤖 API Multi-Agente**
```python
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
# Testar configuração
python test_api_config.py

# Ver logs
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