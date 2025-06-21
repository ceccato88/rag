# 📋 MANUAL DE BOAS PRÁTICAS - CONFIGURAÇÃO CENTRALIZADA

> **Versão**: 2.0  
> **Data**: 2025-06-21  
> **Status**: ✅ Ativo  
> **Escopo**: Sistema RAG Multi-Agente CENTRALIZADO

---

## 🎯 **OBJETIVO**

Este manual garante que **TODAS** as alterações no código mantenham a **centralização TOTAL** do sistema de configuração. Após a refatoração v2.0, **TUDO** está centralizado em `src/core/constants.py` com **ZERO duplicação**.

---

## 📂 **NOVA ARQUITETURA CENTRALIZADA**

### 🏛️ **FONTE ÚNICA DA VERDADE**
**`src/core/constants.py`** - **TODAS** as configurações em um só lugar

### 🔧 **Arquivos do Sistema (Ordem de Prioridade)**
1. **`src/core/constants.py`** - 🏆 **PRINCIPAL** - Todas as configurações
2. **`src/core/config.py`** - Sistema de configuração que usa constants.py
3. **`.env`** - **APENAS** variáveis específicas do ambiente (67 linhas)
4. **`.env.example`** - Template limpo (91 linhas)

### 🌉 **Pontes de Compatibilidade**
- **`multi-agent-researcher/src/researcher/enhanced/enhanced_config.py`** - Ponte para constants.py
- **`multi-agent-researcher/src/researcher/enhanced/enhanced_unified_config.py`** - Adaptador

---

## 🏗️ **CONFIGURAÇÕES CENTRALIZADAS EM constants.py**

### 📊 **Estrutura Completa:**
```python
# =============================================================================
# TODAS AS CONFIGURAÇÕES EM UM SÓ LUGAR
# =============================================================================

# 🤖 Modelos IA
DEFAULT_MODELS = {...}
MODEL_CONFIG = {...}

# 🔧 Tokens e Limites
TOKEN_LIMITS = {...}
ENHANCED_TOKEN_LIMITS = {...}  # Específicas do sistema enhanced

# ⚡ Performance e Cache
CACHE_CONFIG = {...}
TIMEOUT_CONFIG = {...}
PROCESSING_CONFIG = {...}

# 🎭 Sistema Multi-Agente
MULTIAGENT_CONFIG = {...}
ENHANCED_SIMILARITY_THRESHOLDS = {...}  # Por complexidade
DYNAMIC_MAX_CANDIDATES = {...}          # Por complexidade
ENHANCED_SUFFICIENCY_CRITERIA = {...}
ENHANCED_ITERATION_LIMITS = {...}
ENHANCED_SPECIALIST_OPTIMIZATIONS = {...}  # Por especialista

# 🔒 Segurança e Produção
SECURITY_CONFIG = {...}
PRODUCTION_CONFIG = {...}

# 📊 Logging e Monitoring
LOGGING_CONFIG = {...}

# 📁 Arquivos e Validação
FILE_LIMITS = {...}
VALIDATION_CONFIG = {...}

# 🎯 Função Unificada Enhanced
def get_enhanced_config(complexity: str, specialist_type: str = None) -> dict
```

---

## ⚠️ **REGRAS OBRIGATÓRIAS v2.0**

### 🚫 **NUNCA FAÇA:**

#### ❌ **1. Duplicar Configurações**
```python
# ❌ ERRADO - Criar config em arquivo separado
# Não crie mais enhanced_config.py, rag_config.py, etc.
# TUDO vai em constants.py
```

#### ❌ **2. Valores Hardcoded**
```python
# ❌ ERRADO
max_candidates = 3
similarity_threshold = 0.65
temperature = 0.1
```

#### ❌ **3. Uso Direto de os.getenv()**
```python
# ❌ ERRADO
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
```

### ✅ **SEMPRE FAÇA:**

#### ✅ **1. Use Configuração Centralizada**
```python
# ✅ CORRETO - Para sistema geral
from src.core.config import SystemConfig
config = SystemConfig()
temperature = config.rag.temperature

# ✅ CORRETO - Para sistema enhanced
from src.core.constants import get_enhanced_config
enhanced_config = get_enhanced_config('COMPLEX', 'TECHNICAL')
max_candidates = enhanced_config['max_candidates']  # 4 para COMPLEX
```

#### ✅ **2. Use Constantes Específicas**
```python
# ✅ CORRETO - Para configurações específicas
from src.core.constants import DYNAMIC_MAX_CANDIDATES, ENHANCED_SIMILARITY_THRESHOLDS

# Para sistema por complexidade
max_candidates = DYNAMIC_MAX_CANDIDATES['COMPLEX']  # 4
threshold = ENHANCED_SIMILARITY_THRESHOLDS['COMPLEX']  # 0.55
```

#### ✅ **3. Use Função Enhanced Unificada**
```python
# ✅ CORRETO - Melhor prática para sistema enhanced
from src.core.constants import get_enhanced_config

def create_subagent_task(complexity: str, specialist: str):
    config = get_enhanced_config(complexity, specialist)
    return {
        'max_candidates': config['max_candidates'],      # Baseado na complexidade
        'similarity_threshold': config['similarity_threshold'], # Otimizado por especialista
        'max_iterations': config['max_iterations'],
        'sufficiency_criteria': config['sufficiency_criteria']
    }
```

---

## 📝 **CHECKLIST PARA MUDANÇAS v2.0**

### 🔍 **ANTES DE IMPLEMENTAR (Obrigatório)**

- [ ] **Verifique** se a configuração já existe em `src/core/constants.py`
- [ ] **Confirme** se não está duplicada em outros arquivos
- [ ] **Identifique** qual seção do constants.py deve receber a nova config

### ⚙️ **AO IMPLEMENTAR NOVA CONFIGURAÇÃO**

#### **Passo 1: Adicionar APENAS em constants.py**
```python
# Em src/core/constants.py - Seção apropriada
NOVA_CATEGORIA_CONFIG = {
    'NOVA_VARIAVEL': 'valor_padrao',
    'OUTRA_VARIAVEL': 123,
    # ...
}
```

#### **Passo 2: Integrar em config.py (se necessário)**
```python
# Em src/core/config.py - APENAS se for variável de ambiente
@dataclass
class ConfigClass:
    nova_variavel: str = os.getenv('NOVA_VARIAVEL', NOVA_CATEGORIA_CONFIG['NOVA_VARIAVEL'])
```

#### **Passo 3: Adicionar em .env APENAS se específico do ambiente**
```bash
# Em .env.example - APENAS se varia por ambiente
# NOVA_VARIAVEL=valor_customizado  # Uncomment para override
```

#### **Passo 4: Usar no código**
```python
# No seu código
from src.core.constants import NOVA_CATEGORIA_CONFIG
valor = NOVA_CATEGORIA_CONFIG['NOVA_VARIAVEL']

# OU para enhanced
from src.core.constants import get_enhanced_config
config = get_enhanced_config(complexity, specialist)
```

### ✅ **APÓS IMPLEMENTAR (Obrigatório)**

- [ ] **Busque** por configurações duplicadas: `rg -n "NOVA_VARIAVEL" --type py`
- [ ] **Remova** duplicações em outros arquivos
- [ ] **Teste** se a configuração é carregada corretamente
- [ ] **Verifique** que pontes de compatibilidade funcionam

---

## 🔍 **COMANDOS DE VERIFICAÇÃO v2.0**

### **Buscar Duplicações (CRÍTICO)**
```bash
# Buscar configurações duplicadas
rg -n "MAX_CANDIDATES|SIMILARITY_THRESHOLD" --type py

# Verificar se algo não está em constants.py
rg -n "(0\.1|4000|1000)" --type py | grep -v constants.py

# Buscar uso direto de os.getenv
rg -n "os\.getenv\(" --type py | grep -v config.py
```

### **Verificar Centralização**
```bash
# Testar configuração centralizada
python -c "
from src.core.constants import get_enhanced_config, DYNAMIC_MAX_CANDIDATES
print('✅ Centralização:', DYNAMIC_MAX_CANDIDATES)
config = get_enhanced_config('COMPLEX', 'TECHNICAL') 
print('✅ Enhanced Config:', config)
"
```

---

## 🏗️ **PADRÕES v2.0 POR CATEGORIA**

### 🎭 **Sistema Enhanced (PRINCIPAL)**
```python
# ✅ PADRÃO v2.0 - Função unificada
from src.core.constants import get_enhanced_config

config = get_enhanced_config(complexity='COMPLEX', specialist_type='TECHNICAL')
# Retorna: {'max_candidates': 4, 'similarity_threshold': 0.65, ...}
```

### 🔑 **API Keys**
- **Local**: `config.rag.api_key_name`
- **Centralizado em**: `constants.py` (valores padrão)
- **Exemplo**: `config.rag.openai_api_key`

### 🤖 **Modelos de IA**  
- **Local**: `constants.DEFAULT_MODELS` ou `config.rag.model_name`
- **Centralizados**: gpt-4.1-mini, gpt-4.1, voyage-multimodal-3
- **Exemplo**: `config.rag.llm_model`

### ⚡ **Performance Enhanced**
- **Local**: `constants.ENHANCED_TIMEOUTS`, `DYNAMIC_MAX_CANDIDATES`
- **Função**: `get_enhanced_config(complexity, specialist)`
- **Exemplo**: Complexidade COMPLEX = 4 candidatos

### 🔒 **Segurança**
- **Local**: `constants.SECURITY_CONFIG`
- **Integração**: `config.security.parametro`
- **Exemplo**: `config.security.enable_rate_limiting`

---

## 🚨 **CASOS ESPECIAIS v2.0**

### **Sistema Enhanced Multi-Agente**
```python
# ✅ PADRÃO v2.0 - Configuração por complexidade e especialista
from src.core.constants import get_enhanced_config

def create_subagent(complexity: str, specialist_type: str):
    config = get_enhanced_config(complexity, specialist_type)
    
    return SubAgent(
        max_candidates=config['max_candidates'],        # 2-5 baseado na complexidade
        similarity_threshold=config['similarity_threshold'], # Otimizado por especialista
        max_iterations=config['max_iterations'],        # 1-3 baseado na complexidade
        sufficiency_criteria=config['sufficiency_criteria']
    )
```

### **Configurações por Complexidade**
```python
# ✅ CORRETO - Usar mapeamento direto
from src.core.constants import DYNAMIC_MAX_CANDIDATES, ENHANCED_SIMILARITY_THRESHOLDS

def determine_search_params(query_complexity: str):
    return {
        'max_candidates': DYNAMIC_MAX_CANDIDATES[query_complexity],  # SIMPLE=2, COMPLEX=4
        'threshold': ENHANCED_SIMILARITY_THRESHOLDS[query_complexity] # SIMPLE=0.70, COMPLEX=0.55
    }
```

### **Compatibilidade com Sistema Legacy**
```python
# ✅ PONTE - enhanced_config.py redireciona para constants.py
from researcher.enhanced.enhanced_config import get_optimized_config  # Aponta para constants.py
config = get_optimized_config('COMPLEX', 'TECHNICAL')  # Usa get_enhanced_config()
```

---

## 🔧 **MIGRAÇÃO DE CÓDIGO EXISTENTE**

### **ANTES (Duplicado)**
```python
# ❌ CÓDIGO ANTIGO - Duplicado em vários arquivos
MAX_CANDIDATES = {'SIMPLE': 2, 'COMPLEX': 4}  # em enhanced_config.py
SIMILARITY_THRESHOLDS = {'SIMPLE': 0.70}      # em enhanced_config.py
```

### **DEPOIS (Centralizado)**
```python
# ✅ CÓDIGO v2.0 - Tudo em constants.py
from src.core.constants import DYNAMIC_MAX_CANDIDATES, ENHANCED_SIMILARITY_THRESHOLDS

max_candidates = DYNAMIC_MAX_CANDIDATES['COMPLEX']  # 4
threshold = ENHANCED_SIMILARITY_THRESHOLDS['COMPLEX']  # 0.55
```

---

## 📊 **MÉTRICAS DA CENTRALIZAÇÃO**

### **Redução Alcançada:**
- **`.env`**: 131 → 67 linhas (**49% redução**)
- **Arquivos de config**: 3 → 1 (**67% redução**)
- **Duplicações**: 100% → 0% (**eliminação total**)
- **Função unificada**: `get_enhanced_config()` para tudo

### **Benefícios:**
- ✅ **Zero duplicação** de configurações
- ✅ **Fonte única da verdade** em `constants.py`
- ✅ **Compatibilidade mantida** com código existente
- ✅ **Função enhanced unificada** para complexidade + especialista

---

## ⚡ **RESUMO RÁPIDO v2.0**

1. **🏛️ TUDO** em `src/core/constants.py` - fonte única da verdade
2. **🚫 ZERO** duplicação entre arquivos  
3. **✅ FUNÇÃO** `get_enhanced_config(complexity, specialist)` para sistema enhanced
4. **🌉 PONTES** de compatibilidade mantidas para código existente
5. **📝 .env** apenas com variáveis específicas do ambiente
6. **🔧 TESTE** sempre: `python -c "from src.core.constants import get_enhanced_config; print(get_enhanced_config('COMPLEX', 'TECHNICAL'))"`

---

## 📞 **EM CASO DE DÚVIDAS v2.0**

1. **Configuração Enhanced**: Use `get_enhanced_config(complexity, specialist_type)`
2. **Configuração Geral**: Use `SystemConfig()` 
3. **Verificar Duplicação**: `rg -n "SUA_CONFIG" --type py`
4. **Testar Centralização**: Execute os comandos de verificação

---

**🎯 v2.0: Uma configuração, um local, zero duplicação!**