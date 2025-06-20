# 🔧 SISTEMA DE CONFIGURAÇÃO RAG - GUIA RÁPIDO

> **Sistema totalmente centralizado e validado com 72 variáveis mapeadas**

## 📋 **ARQUIVOS PRINCIPAIS**

| Arquivo | Função | Status |
|---------|--------|--------|
| **`BOAS_PRATICAS_CONFIGURACAO.md`** | 📖 Manual completo de boas práticas | ✅ Ativo |
| **`VARIABLE_TRACKING.md`** | 🗺️ Mapeamento de todas as 72 variáveis | ✅ 100% |
| **`src/core/config.py`** | 🎛️ Configuração centralizada | ✅ Integrado |
| **`src/core/constants.py`** | 📊 Constantes e valores padrão | ✅ Completo |
| **`.env.example`** | 🔑 Template de variáveis | ✅ Atualizado |

## ⚡ **COMANDOS RÁPIDOS**

### 🔍 **Verificação de Consistência**
```bash
# Verificação completa do sistema
python scripts/verify_config_consistency.py

# Buscar valores hardcoded
./scripts/find_hardcoded_values.sh

# Buscar variável específica
rg -n "NOME_VARIAVEL" --type py
```

### 📊 **Visualizar Configuração**
```bash
# Ver todas as configurações carregadas
python -c "from src.core.config import SystemConfig; SystemConfig().print_config()"

# Validar configuração atual
python -c "from src.core.config import SystemConfig; print(SystemConfig().validate())"
```

## ✅ **REGRAS ESSENCIAIS**

### **❌ NUNCA FAÇA:**
- Valores hardcoded: `temperature = 0.1`
- Uso direto: `os.getenv('API_KEY')`
- Constantes diretas: `if size > 1000:`

### **✅ SEMPRE FAÇA:**
- Use configuração: `config.rag.temperature`
- Use constantes: `VALIDATION_CONFIG['MAX_SIZE']`
- Siga os padrões por categoria

## 🎯 **PROCESSO PARA NOVAS VARIÁVEIS**

1. **📝 Adicionar em `constants.py`**
2. **🔧 Integrar em `config.py`**  
3. **📋 Incluir em `.env.example`**
4. **💻 Usar no código via `SystemConfig()`**
5. **📊 Atualizar `VARIABLE_TRACKING.md`**

## 🏗️ **CATEGORIAS DO SISTEMA**

| Categoria | Localização | Exemplo |
|-----------|-------------|---------|
| 🔑 **API Keys** | `config.rag.*_api_key` | `config.rag.openai_api_key` |
| 🤖 **Modelos** | `config.rag.*_model` | `config.rag.llm_model` |
| ⚡ **Performance** | `config.multiagent.*` | `config.multiagent.max_subagents` |
| 🔒 **Segurança** | `config.security.*` | `config.security.enable_rate_limiting` |
| 💾 **Cache** | `config.rag.*_cache_*` | `config.rag.embedding_cache_size` |
| 📊 **Logging** | `config.logging.*` | `config.logging.log_level` |
| 🖥️ **Servidor** | `config.api_unified.*` | `config.api_unified.api_port` |
| 📁 **Arquivos** | `config.rag.*_dir` | `config.rag.data_dir` |

## 🎊 **STATUS ATUAL**

✅ **Sistema 100% Alinhado**
- **72/72 variáveis** analisadas e integradas
- **8 problemas** encontrados e corrigidos
- **Configuração centralizada** funcionando
- **Scripts de verificação** implementados
- **Documentação completa** disponível

---

**💡 Para implementação detalhada, consulte `BOAS_PRATICAS_CONFIGURACAO.md`**