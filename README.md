# 🚀 Sistema RAG Multi-Agente Avançado

Um sistema de **Geração Aumentada por Recuperação (RAG)** com arquitetura multi-agente especializada, reasoning avançado e sistema de memória distribuída.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com)
[![Voyage AI](https://img.shields.io/badge/Voyage-Embeddings-purple.svg)](https://voyageai.com)
[![Astra DB](https://img.shields.io/badge/DataStax-Astra_DB-orange.svg)](https://astra.datastax.com)

---

## 🎯 **O que é este Sistema?**

Este é um **sistema RAG multi-agente** que combina:

- **🔍 Busca semântica avançada** com embeddings multimodais
- **🤖 Arquitetura multi-agente** com especialização por domínio
- **🧠 Reasoning ReAct** (Reason + Act) para tomada de decisão
- **💾 Sistema de memória distribuída** com cache hierárquico
- **📊 Processamento multimodal** (texto + imagem)

### **Por que usar?**

**Problemas do RAG tradicional:**
- ❌ Respostas genéricas e superficiais
- ❌ Falta de especialização por domínio
- ❌ Limitado a texto apenas

**Soluções deste sistema:**
- ✅ **Agentes especializados** para diferentes análises
- ✅ **Reasoning avançado** com padrão ReAct
- ✅ **Processamento multimodal** (texto + imagem)
- ✅ **Configuração flexível** para diferentes casos de uso

---

## ⚡ **Início Rápido**

### **3 Passos Simples:**

```bash
# 1. Instalar
source .venv/bin/activate
python install.py

# 2. Executar
python api_simple.py      # Terminal 1 - API RAG Simples (porta 8000)
python api_multiagent.py  # Terminal 2 - API Multi-Agente (porta 8001)

# 3. Testar
python example_api_client.py
```

### **URLs Principais:**
- **API Simples**: http://localhost:8000
- **Multi-Agente**: http://localhost:8001
- **Docs Swagger**: /docs em cada API
- **Dashboard**: http://localhost/ (com Docker)

---

## 📚 **Documentação Completa**

### **🚀 Para Começar Rapidamente**
- **[QUICKSTART.md](QUICKSTART.md)** - 3 passos para usar o sistema
- **[FAQ.md](FAQ.md)** - Perguntas frequentes e soluções rápidas

### **🎯 Para Gerentes e Leads**
- **[SETUP_FINAL.md](SETUP_FINAL.md)** - Resumo executivo e status do projeto
- **[docs/PERFORMANCE.md](docs/PERFORMANCE.md)** - Métricas e benchmarks

### **🔧 Para DevOps e Administradores**
- **[DEPENDENCIES.md](DEPENDENCIES.md)** - Guia completo de instalação
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Resolução de problemas

### **👨‍💻 Para Desenvolvedores**
- **[ESTRUTURA_FINAL.md](ESTRUTURA_FINAL.md)** - Mapa da organização do código
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Como contribuir com o projeto
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitetura técnica detalhada

### **🔌 Para Integradores**
- **[API_USAGE.md](API_USAGE.md)** - Guia completo das APIs
- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - Exemplos práticos de uso

### **📖 Para Estudiosos**
- **[docs/THEORY.md](docs/THEORY.md)** - Teoria RAG e conceitos multi-agente
- **[CHANGELOG.md](CHANGELOG.md)** - Histórico de versões e mudanças

---

## 🏗️ **Arquitetura Resumida**

### **Componentes Principais:**
```
📊 Sistema RAG Core (search.py)
    ↓
🤖 Sistema Multi-Agente (multi-agent-researcher/)
    ↓  
🚀 APIs de Produção (api_simple.py, api_multiagent.py)
    ↓
🐳 Deploy com Docker (docker-compose.yml)
```

### **Fluxo de Dados:**
```
Query → Lead Researcher → Agentes Especializados → RAG Engine → Resposta
```

**Detalhes completos**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🔧 **Configuração Básica**

### **1. Requisitos:**
- Python 3.8+
- Chaves API: OpenAI, Voyage AI, Astra DB

### **2. Instalação Automática:**
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar tudo
python install.py
```

### **3. Configuração:**
```bash
# Copiar template
cp .env.example .env

# Editar com suas chaves
# OPENAI_API_KEY=sk-...
# VOYAGE_API_KEY=pa-...
# ASTRA_DB_API_ENDPOINT=https://...
# ASTRA_DB_APPLICATION_TOKEN=AstraCS:...
```

**Guia completo**: [DEPENDENCIES.md](DEPENDENCIES.md)

---

## 💡 **Casos de Uso**

### **📊 API RAG Simples** - Consultas diretas
```python
import requests
response = requests.post("http://localhost:8000/search", json={
    "query": "O que é machine learning?"
})
print(response.json()["response"])
```

### **🤖 API Multi-Agente** - Análises complexas
```python
response = requests.post("http://localhost:8001/research", json={
    "query": "Compare TensorFlow vs PyTorch para deep learning",
    "processing_mode": "sync"
})
print(response.json()["final_answer"])
```

**Mais exemplos**: [docs/EXAMPLES.md](docs/EXAMPLES.md)

---

## 🚀 **Deploy em Produção**

### **Método 1: Docker (Recomendado)**
```bash
docker-compose up -d
```

### **Método 2: Manual**
```bash
python api_simple.py      # Porta 8000
python api_multiagent.py  # Porta 8001
```

**Guia completo**: [SETUP_FINAL.md](SETUP_FINAL.md)

---

## 📊 **Performance**

| Métrica | API Simples | Multi-Agente |
|---------|-------------|--------------|
| **Tempo médio** | 5-30s | 30-300s |
| **Precisão** | >85% | >90% |
| **Casos de uso** | Consultas diretas | Análises complexas |

**Detalhes**: [docs/PERFORMANCE.md](docs/PERFORMANCE.md)

---

## 🛠️ **Desenvolvimento**

### **Estrutura do Projeto:**
```
rag/
├── 📄 config.py              # Configuração centralizada
├── 📄 search.py              # Sistema RAG principal
├── 📄 indexer.py             # Processamento de documentos
├── 🚀 api_simple.py          # API RAG simples
├── 🚀 api_multiagent.py      # API multi-agente
├── 📁 multi-agent-researcher/ # Sistema multi-agente
├── 📁 utils/                 # Utilitários
└── 📁 docs/                  # Documentação detalhada
```

**Detalhes**: [ESTRUTURA_FINAL.md](ESTRUTURA_FINAL.md)

### **Como Contribuir:**
1. Fork do repositório
2. Criar branch para feature
3. Seguir padrões do [CONTRIBUTING.md](CONTRIBUTING.md)
4. Submeter Pull Request

---

## ❓ **Problemas?**

### **Diagnóstico Rápido:**
```bash
# Verificar configuração
source .venv/bin/activate
python diagnostico_simples.py
```

### **Problemas Comuns:**
- **APIs não respondem**: Verificar se portas 8000/8001 estão livres
- **Erro de configuração**: Verificar chaves no .env
- **Timeout**: Ajustar MULTIAGENT_TIMEOUT no .env

**Guia completo**: [FAQ.md](FAQ.md) | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 📚 **Recursos Adicionais**

- **Documentação FastAPI**: Acesse `/docs` em qualquer API
- **Logs do sistema**: Diretório `logs/`
- **Exemplos avançados**: [docs/EXAMPLES.md](docs/EXAMPLES.md)
- **Teoria RAG**: [docs/THEORY.md](docs/THEORY.md)

---

## 🎯 **Resumo**

Este sistema RAG Multi-Agente oferece uma solução completa para consultas inteligentes, combinando:

✅ **Facilidade de uso** (3 passos para começar)  
✅ **Flexibilidade** (APIs simples e avançada)  
✅ **Escalabilidade** (deploy em produção pronto)  
✅ **Documentação completa** (para todos os perfis)

**🚀 Pronto para produção e desenvolvimento!**

---

## 📞 **Suporte**

- **Dúvidas rápidas**: [FAQ.md](FAQ.md)
- **Problemas técnicos**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Contribuições**: [CONTRIBUTING.md](CONTRIBUTING.md)

**Happy Coding!** 🎉
