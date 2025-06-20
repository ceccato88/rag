# 🧪 Guia de Testes

## 🎯 Visão Geral

O sistema RAG Multi-Agent possui uma estrutura abrangente de testes para garantir qualidade e confiabilidade em todos os níveis.

## 📁 Estrutura de Testes

### `/tests/` - Diretório Principal de Testes

- **`test_api.py`** - Teste completo da API com relatório detalhado
- **`test_full_pipeline.py`** - Teste completo do pipeline com dados reais

## 🔧 Scripts de Teste

### `tests/test_api.py`
Teste completo da API com relatório detalhado.

**Funcionalidades:**
- Health check e autenticação
- Busca simples e multi-agente  
- Focus areas automaticamente
- Stress test e performance
- Relatório JSON em `/logs/`

```bash
# Teste completo
python tests/test_api.py

# Teste rápido (apenas essenciais)
python tests/test_api.py --quick

# Com configurações customizadas
python tests/test_api.py --url http://localhost:8000 --token your-token
```

### `tests/test_full_pipeline.py`
Teste completo do pipeline com dados reais.

**Funcionalidades:**
- Indexação de documentos reais (Zep paper)
- Verificação da indexação
- Busca RAG simples
- Sistema multi-agente completo
- Continuidade do reasoning
- Métricas de performance
- Relatório abrangente com recomendações

```bash
# Pipeline completo
python tests/test_full_pipeline.py

# Com configurações customizadas  
python tests/test_full_pipeline.py --url http://localhost:8000 --token your-token
```

## 🚀 Executando Testes

### Testes de API
```bash
# Teste completo da API
python tests/test_api.py

# Teste rápido (apenas essenciais)
python tests/test_api.py --quick
```

### Testes de Pipeline Completo
```bash
# Pipeline completo com indexação e busca
python tests/test_full_pipeline.py

# Com collection customizada
python tests/test_full_pipeline.py --collection my_test_collection
```

## 📊 Relatórios de Teste

### Localização
Todos os relatórios são salvos em `/logs/`:

- **`api_test_report.json`** - Relatório do test_api.py
- **`full_pipeline_report.json`** - Relatório do test_full_pipeline.py

### Estrutura do Relatório
```json
{
  "pipeline_test_summary": {
    "timestamp": "2025-06-20 00:15:30",
    "total_tests": 15,
    "passed_tests": 13,
    "success_rate": 86.7
  },
  "category_breakdown": {
    "Health": {"success_rate": 100.0, "avg_duration": 0.02},
    "Multi-Agent": {"success_rate": 80.0, "avg_duration": 25.3}
  },
  "recommendations": [
    "Sistema multi-agente lento - considerar otimizações"
  ]
}
```

## 🎯 Estratégia de Testes

### Pirâmide de Testes
1. **Base: Testes Unitários (70%)**
   - Componentes isolados
   - Execução rápida
   - Alta cobertura

2. **Meio: Testes de Integração (20%)**
   - Interação entre componentes
   - Fluxos principais
   - Configurações reais

3. **Topo: Testes E2E (10%)**
   - Cenários de usuário
   - Dados reais
   - Performance

### Critérios de Qualidade
- **Taxa de sucesso**: > 80% para aprovação
- **Performance**: < 30s para busca simples, < 60s para multi-agente
- **Cobertura**: > 70% para componentes críticos

## 🔍 Testando Funcionalidades Específicas

### ReAct Reasoning
```bash
python -m pytest tests/unit/test_reasoning.py::TestReActReasoner::test_full_reasoning_cycle -v
```

### Sistema Multi-Agente
```bash
python -m pytest tests/unit/test_agents.py::TestOpenAILeadResearcher -v
```

### Focus Areas
```bash
python tests/test_api.py
# Observar logs para verificar seleção automática de focus areas
```

### Modelo Coordinator
```bash
# Verificar se síntese usa gpt-4.1
curl -X POST "http://localhost:8000/api/v1/research" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Test coordinator model", "use_multiagent": true}'
  
# Buscar por "gpt-4.1" na resposta
```

## 🐛 Debug de Testes

### Logs Detalhados
```bash
# Com logs de debug
python -m pytest tests/unit/ -v -s --log-cli-level=DEBUG

# Salvar logs em arquivo
python -m pytest tests/unit/ -v > test_output.log 2>&1
```

### Isolamento de Problemas
```bash
# Teste individual
python -m pytest tests/unit/test_config.py::TestRAGConfig::test_default_config_values -v

# Pular testes lentos
python -m pytest tests/unit/ -v -m "not slow"
```

## ⚡ Performance Testing

### Métricas Importantes
- **Latência de busca simples**: < 5s
- **Latência multi-agente**: < 30s  
- **Taxa de sucesso**: > 95%
- **Memory usage**: < 2GB para 3 subagentes

### Stress Testing
```bash
# Múltiplas requisições simultâneas
python tests/test_api.py  # Inclui stress test

# Load testing manual
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/simple" \\
    -H "Authorization: Bearer TOKEN" \\
    -H "Content-Type: application/json" \\
    -d '{"query": "Test '$i'"}' &
done
wait
```

## 🔧 Configuração de Teste

### Variáveis de Ambiente para Testes
```env
# .env.test
PYTEST_TIMEOUT=300
TEST_COLLECTION_NAME=test_collection
MOCK_AI_RESPONSES=false
ENABLE_TEST_ENDPOINTS=true
```

### Setup de CI/CD
```yaml
# .github/workflows/tests.yml
- name: Run Unit Tests
  run: python -m pytest tests/unit/ -v --cov=src

- name: Run API Tests  
  run: python tests/test_api.py --quick

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## 📝 Troubleshooting

### Problemas Comuns

**Erro: "Module not found"**
```bash
# Instalar dependências de teste
pip install -r config/requirements/dev.txt
```

**Erro: "API não responde"**
```bash
# Verificar se API está rodando
curl http://localhost:8000/api/v1/health
```

**Testes lentos**
```bash
# Verificar timeout configurations
grep -r "timeout" tests/
```

### Logs de Debug
```bash
# Logs estruturados
export LOG_LEVEL=DEBUG
python -m pytest tests/unit/ -v -s
```

---

## 📚 Links Relacionados

- [📖 Guia Completo](README.md)
- [🏗️ Arquitetura](architecture.md)
- [🤖 Sistema Multi-Agente](multi-agent.md)  
- [📝 API Guide](api-guide.md)
- [⚡ Quick Start](quick-start.md)