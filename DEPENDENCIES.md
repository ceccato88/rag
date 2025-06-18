# 📦 ESTRUTURA DE DEPENDÊNCIAS - Sistema RAG Multi-Agente

## 📋 Resumo dos Arquivos

### **🔧 Arquivos Principais**

1. **`requirements.txt`** - Dependências principais do sistema
2. **`requirements_api.txt`** - Dependências específicas das APIs de produção
3. **`pyproject.toml`** (raiz) - Configuração completa do projeto principal
4. **`multi-agent-researcher/pyproject.toml`** - Configuração do subsistema multi-agente

---

## 📂 ARQUIVOS DETALHADOS

### **📄 `requirements.txt`** (PRINCIPAL)
```bash
# Uso: pip install -r requirements.txt
```

**Conteúdo:**
- ✅ **Core RAG**: OpenAI, Voyage AI, Astra DB
- ✅ **Processamento**: PyMuPDF, Pillow, PDF processing
- ✅ **Multi-Agente**: Pydantic, aiohttp, Jinja2
- ✅ **Utilitários**: python-dotenv, requests, tqdm
- ✅ **Servidor**: uvicorn
- ✅ **Testes**: pytest, pytest-asyncio
- ✅ **Observabilidade**: OpenTelemetry (opcional)

**Total**: ~17 dependências principais

---

### **📄 `requirements_api.txt`** (APIs DE PRODUÇÃO)
```bash
# Uso: pip install -r requirements_api.txt
```

**Conteúdo:**
- ✅ **FastAPI**: Framework web moderno
- ✅ **WebSockets**: Streaming em tempo real
- ✅ **Cache**: Redis para cache distribuído
- ✅ **Segurança**: JWT, bcrypt, cryptography
- ✅ **Monitoramento**: Prometheus, Sentry
- ✅ **Validação**: Email, telefone

**Total**: ~15 dependências específicas para APIs

---

### **📄 `pyproject.toml`** (RAIZ - PRINCIPAL)
```bash
# Uso: pip install -e .
# Uso: pip install -e .[api,dev,monitoring]
```

**Configuração Completa:**
- ✅ **Metadados**: Nome, versão, descrição, autores
- ✅ **Dependências Core**: Mesmas do requirements.txt
- ✅ **Dependências Opcionais**:
  - `[api]` - FastAPI, WebSocket, Redis
  - `[dev]` - Pytest, Black, MyPy, Flake8
  - `[monitoring]` - OpenTelemetry, Prometheus, Sentry
  - `[all]` - Todas as dependências
- ✅ **Scripts CLI**: Comandos rag-* disponíveis
- ✅ **Configuração de Ferramentas**: pytest, black, isort, mypy

---

### **📄 `multi-agent-researcher/pyproject.toml`** (SUBSISTEMA)
```bash
# Uso: cd multi-agent-researcher && pip install -e .
```

**Configuração Específica:**
- ✅ **Foco**: Sistema multi-agente isolado
- ✅ **Dependências**: OpenAI, instructor, SQLAlchemy
- ✅ **Testes**: pytest-asyncio, pytest-mock
- ✅ **Observabilidade**: OpenTelemetry

---

## 🚀 MÉTODOS DE INSTALAÇÃO

### **Método 1: Instalação Automática (RECOMENDADO)**
```bash
python install.py
```

**O que faz:**
- ✅ Verifica Python 3.11+
- ✅ Instala dependências principais
- ✅ Pergunta sobre dependências opcionais
- ✅ Valida instalação
- ✅ Cria diretórios necessários
- ✅ Verifica configuração

### **Método 2: Instalação Manual Básica**
```bash
# Dependências principais
pip install -r requirements.txt

# OU usando pyproject.toml
pip install -e .
```

### **Método 3: Instalação Manual Completa**
```bash
# Instalar tudo
pip install -e .[all]

# OU instalar grupos específicos
pip install -e .[api]          # APIs de produção
pip install -e .[dev]          # Desenvolvimento
pip install -e .[monitoring]   # Monitoramento
```

### **Método 4: Instalação por Funcionalidade**
```bash
# Sistema básico
pip install -r requirements.txt

# APIs de produção
pip install -r requirements_api.txt

# Subsistema multi-agente
cd multi-agent-researcher
pip install -e .
```

---

## 🎯 CASOS DE USO

### **👨‍💻 Para Desenvolvimento**
```bash
pip install -e .[dev]
```
**Inclui**: pytest, black, isort, mypy, flake8, coverage

### **🚀 Para Produção (APIs)**
```bash
pip install -e .[api]
```
**Inclui**: FastAPI, WebSocket, Redis, estruturação de logs

### **📊 Para Monitoramento**
```bash
pip install -e .[monitoring]  
```
**Inclui**: OpenTelemetry, Prometheus, Sentry

### **🧪 Para Testes Apenas**
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### **🔬 Para Research/Experimentação**
```bash
pip install -r requirements.txt
# Sistema básico é suficiente
```

---

## ⚡ COMANDOS CLI DISPONÍVEIS

Após instalação com `pip install -e .`:

```bash
# Indexar documentos
rag-index

# Buscar documentos  
rag-search

# Executar API RAG simples
rag-api-simple

# Executar API multi-agente
rag-api-multiagent
```

---

## 🔧 RESOLUÇÃO DE PROBLEMAS

### **❌ Erro: "command not found: rag-*"**
```bash
# Reinstalar em modo desenvolvimento
pip install -e .
```

### **❌ Erro: ModuleNotFoundError**
```bash
# Verificar instalação
pip list | grep rag
pip install -r requirements.txt
```

### **❌ Conflitos de Dependências**
```bash
# Criar ambiente limpo
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

pip install -e .
```

### **❌ APIs não funcionam**
```bash
# Instalar dependências das APIs
pip install -r requirements_api.txt
# ou
pip install -e .[api]
```

---

## 📊 COMPARAÇÃO DOS ARQUIVOS

| Arquivo | Propósito | Dependências | Uso |
|---------|-----------|--------------|-----|
| `requirements.txt` | Sistema base | ~17 core | `pip install -r requirements.txt` |
| `requirements_api.txt` | APIs produção | ~15 específicas | `pip install -r requirements_api.txt` |
| `pyproject.toml` (raiz) | Projeto completo | Core + opcionais | `pip install -e .[grupo]` |
| `multi-agent-researcher/pyproject.toml` | Subsistema | ~12 específicas | `cd sub && pip install -e .` |

---

## 💡 RECOMENDAÇÕES

### **🚀 Para Uso Rápido**
```bash
python install.py
```

### **🏭 Para Produção**
```bash
pip install -e .[api,monitoring]
```

### **👨‍💻 Para Desenvolvimento**
```bash
pip install -e .[all]
```

### **🔬 Para Testes**
```bash
pip install -r requirements.txt
```

---

## 🎯 RESUMO

- ✅ **4 arquivos** de dependências organizados
- ✅ **Instalação automática** com `install.py`
- ✅ **Grupos opcionais** para diferentes casos de uso
- ✅ **Scripts CLI** para facilitar execução
- ✅ **Configuração completa** de ferramentas de desenvolvimento
- ✅ **Subsistema isolado** para multi-agente

**Sistema totalmente modular e flexível!** 🎉