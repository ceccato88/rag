# 📋 MANUAL DE BOAS PRÁTICAS - CONFIGURAÇÃO DO SISTEMA RAG

> **Versão**: 1.0  
> **Data**: 2025-06-20  
> **Status**: ✅ Ativo  
> **Escopo**: Sistema RAG Multi-Agente

---

## 🎯 **OBJETIVO**

Este manual garante que **TODAS** as alterações no código mantenham a **consistência e centralização** do sistema de configuração, evitando problemas como valores hardcoded, uso direto de variáveis de ambiente e desalinhamento entre arquivos.

---

## 📂 **ARQUIVOS CRÍTICOS DO SISTEMA**

### 🔧 **Arquivos de Configuração (SEMPRE VERIFICAR)**
1. **`.env.example`** - Template das variáveis de ambiente
2. **`src/core/config.py`** - Configuração centralizada do sistema
3. **`src/core/constants.py`** - Constantes e valores padrão
4. **`api/models/schemas.py`** - Validação Pydantic

### 📊 **Arquivo de Controle**
- **`VARIABLE_TRACKING.md`** - Mapeamento completo de todas as 72 variáveis

---

## ⚠️ **REGRAS OBRIGATÓRIAS**

### 🚫 **NUNCA FAÇA:**

#### ❌ **1. Valores Hardcoded**
```python
# ❌ ERRADO
temperature = 0.1
max_tokens = 4000
model = "gpt-4.1-mini"
```

#### ❌ **2. Uso Direto de os.getenv()**
```python
# ❌ ERRADO
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
```

#### ❌ **3. Constantes Diretas**
```python
# ❌ ERRADO
if len(query) > 1000:  # Valor hardcoded
    raise ValueError("Query muito longa")
```

### ✅ **SEMPRE FAÇA:**

#### ✅ **1. Use Configuração Centralizada**
```python
# ✅ CORRETO
from src.core.config import SystemConfig

config = SystemConfig()
temperature = config.rag.temperature
max_tokens = config.rag.max_tokens
model = config.rag.llm_model
```

#### ✅ **2. Use Constantes de Validação**
```python
# ✅ CORRETO
from src.core.constants import VALIDATION_CONFIG

if len(query) > VALIDATION_CONFIG['MAX_QUERY_LENGTH']:
    raise ValueError("Query muito longa")
```

---

## 📝 **CHECKLIST PARA MUDANÇAS**

### 🔍 **ANTES DE IMPLEMENTAR (Obrigatório)**

- [ ] **Verifique** se a variável já existe em `VARIABLE_TRACKING.md`
- [ ] **Confirme** se está em `src/core/constants.py`
- [ ] **Verifique** se está em `src/core/config.py`
- [ ] **Confirme** se está em `.env.example`

### ⚙️ **AO IMPLEMENTAR NOVA VARIÁVEL**

#### **Passo 1: Adicionar em constants.py**
```python
# Em src/core/constants.py
NOVA_CONFIG = {
    'NOVA_VARIAVEL': 'valor_padrao',
    # ...
}
```

#### **Passo 2: Integrar em config.py**
```python
# Em src/core/config.py
@dataclass
class ConfigClass:
    nova_variavel: str = os.getenv('NOVA_VARIAVEL', NOVA_CONFIG['NOVA_VARIAVEL'])
```

#### **Passo 3: Adicionar em .env.example**
```bash
# Em .env.example
NOVA_VARIAVEL=valor_padrao
```

#### **Passo 4: Usar no código**
```python
# No seu código
config = SystemConfig()
valor = config.categoria.nova_variavel
```

#### **Passo 5: Atualizar documentação**
- Adicionar linha em `VARIABLE_TRACKING.md`

### ✅ **APÓS IMPLEMENTAR (Obrigatório)**

- [ ] **Busque** por valores hardcoded relacionados: `rg -n "valor_antigo" --type py`
- [ ] **Substitua** todos os usos diretos pela configuração centralizada
- [ ] **Teste** se a variável é carregada corretamente
- [ ] **Atualize** `VARIABLE_TRACKING.md` se necessário

---

## 🔍 **COMANDOS DE VERIFICAÇÃO**

### **Buscar Valores Hardcoded**
```bash
# Buscar por valores numéricos suspeitos
rg -n "\b(0\.1|4000|1000|300)\b" --type py

# Buscar por strings hardcoded
rg -n "(gpt-4|voyage-)" --type py

# Buscar uso direto de os.getenv
rg -n "os\.getenv\(" --type py
```

### **Verificar Alinhamento**
```bash
# Verificar se variável existe em todos os arquivos
rg -n "NOVA_VARIAVEL" .env.example src/core/constants.py src/core/config.py
```

---

## 🏗️ **PADRÕES POR CATEGORIA**

### 🔑 **API Keys**
- **Local**: `config.rag.api_key_name`
- **Validação**: Obrigatória em produção
- **Exemplo**: `config.rag.openai_api_key`

### 🤖 **Modelos de IA**  
- **Local**: `config.rag.model_name`
- **Padrão**: gpt-4.1-mini, gpt-4.1, voyage-multimodal-3
- **Exemplo**: `config.rag.llm_model`

### ⚡ **Performance**
- **Local**: `config.multiagent.parametro`
- **Inclui**: timeouts, limites, concorrência
- **Exemplo**: `config.multiagent.max_subagents`

### 🔒 **Segurança**
- **Local**: `config.security.parametro`
- **Inclui**: tokens, rate limiting, CORS
- **Exemplo**: `config.security.enable_rate_limiting`

### 💾 **Cache**
- **Local**: `config.rag.cache_parametro`
- **Inclui**: tamanhos, TTL
- **Exemplo**: `config.rag.embedding_cache_size`

### 📊 **Logging**
- **Local**: `config.logging.parametro`
- **Inclui**: níveis, rotação, estruturação
- **Exemplo**: `config.logging.log_level`

### 🖥️ **Servidor**
- **Local**: `config.api_unified.parametro`
- **Inclui**: porta, workers, host
- **Exemplo**: `config.api_unified.api_port`

### 📁 **Arquivos**
- **Local**: `config.rag.diretorio_ou_limite`
- **Inclui**: diretórios, tamanhos máximos
- **Exemplo**: `config.rag.data_dir`

---

## 🚨 **CASOS ESPECIAIS**

### **Schemas Pydantic**
```python
# ✅ CORRETO - Use constantes
from src.core.constants import VALIDATION_CONFIG

class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=VALIDATION_CONFIG['MIN_QUERY_LENGTH'],
        max_length=VALIDATION_CONFIG['MAX_QUERY_LENGTH']
    )
```

### **Validações**
```python
# ✅ CORRETO - Use constantes de validação
from src.core.constants import FILE_LIMITS

if file_size > FILE_LIMITS['MAX_PDF_SIZE']:
    raise ValueError("Arquivo muito grande")
```

### **Chamadas de API**
```python
# ✅ CORRETO - Use configuração centralizada
response = client.chat.completions.create(
    model=system_config.rag.llm_model,
    max_tokens=system_config.rag.max_tokens,
    temperature=system_config.rag.temperature
)
```

---

## 🔧 **FERRAMENTAS DE DESENVOLVIMENTO**

### **Scripts de Verificação**
```bash
# Verificar consistência (criar script)
python scripts/verify_config_consistency.py

# Buscar problemas comuns
./scripts/find_hardcoded_values.sh
```

### **Pre-commit Hooks** (Recomendado)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-hardcoded-values
        name: Check for hardcoded values
        entry: scripts/check_hardcoded.py
        language: python
```

---

## 📚 **RECURSOS ADICIONAIS**

### **Documentação de Referência**
- `VARIABLE_TRACKING.md` - Mapeamento completo de variáveis
- `src/core/config.py` - Estrutura da configuração
- `src/core/constants.py` - Todas as constantes do sistema

### **Comandos Úteis**
```bash
# Ver todas as configurações carregadas
python -c "from src.core.config import SystemConfig; SystemConfig().print_config()"

# Validar configuração
python -c "from src.core.config import SystemConfig; print(SystemConfig().validate())"
```

---

## ⚡ **RESUMO RÁPIDO**

1. **🔍 SEMPRE** verifique `VARIABLE_TRACKING.md` antes de implementar
2. **🚫 NUNCA** use valores hardcoded ou `os.getenv()` direto
3. **✅ SEMPRE** use `SystemConfig()` para acessar configurações
4. **📝 SEMPRE** atualize os 4 arquivos críticos em conjunto
5. **🔧 SEMPRE** teste após implementar mudanças

---

## 📞 **EM CASO DE DÚVIDAS**

1. Consulte `VARIABLE_TRACKING.md` 
2. Verifique implementações similares existentes
3. Use os comandos de verificação deste manual
4. Siga os padrões por categoria definidos

---

**🎯 Lembre-se: Consistência é fundamental para a manutenibilidade do sistema!**