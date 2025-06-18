# 🛠️ Scripts de Manutenção

Scripts utilitários simplificados para limpeza e manutenção do sistema RAG Multi-Agente.

## 📋 Scripts Disponíveis

### 🗑️ Limpeza de Dados

- **`delete_collection.py`** - Remove documentos da collection AstraDB
- **`delete_documents.py`** - Remove documentos específicos do AstraDB  
- **`delete_images.py`** - Limpa imagens extraídas dos PDFs

## 🚨 Aviso Importante

**⚠️ ATENÇÃO**: Estes scripts fazem alterações **IRREVERSÍVEIS** nos dados!

- Sempre faça backup antes de executar
- Use apenas em ambiente de desenvolvimento
- Confirmação obrigatória antes de executar

## 🔧 Como Usar

### Limpar TODOS os Documentos
```bash
cd maintenance
python delete_collection.py --all        # Deleta TUDO da collection
python delete_documents.py --all         # Deleta TODOS os documentos
python delete_images.py --all            # Deleta TODAS as imagens
```

### Limpar por Prefixo de Documento
```bash
cd maintenance
python delete_collection.py --doc "arxiv_2024"    # Deleta docs com prefixo
python delete_documents.py --doc "paper_2024"     # Deleta docs específicos
python delete_images.py --doc "arxiv_2024"        # Deleta imagens do doc
```

## 📋 Pré-requisitos

- Variáveis de ambiente configuradas (`.env`)
- Conexão com AstraDB funcionando
- Permissões de escrita nos diretórios

## 🔒 Segurança

- Scripts verificam variáveis de ambiente
- Requerem confirmação explícita (`--confirm`)
- Fazem logging de todas as operações
- Validam conexões antes de executar

## 📝 Logs

Todos os scripts geram logs detalhados:
- Operações executadas
- Itens removidos
- Erros encontrados
- Tempo de execução