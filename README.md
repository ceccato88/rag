# Projeto RAG

Este repositório contém um sistema de *Retrieval Augmented Generation* (RAG) em Português. O objetivo é indexar documentos PDF e permitir consultas através de uma aplicação web feita com Streamlit.

## Componentes principais

- **`indexador.py`**: faz o download do PDF, converte cada página em texto/imagem, gera embeddings com a API da Voyage e armazena tudo em uma collection do Astra DB.
- **`buscador_conversacional_producao.py`**: implementa a lógica de busca e geração de respostas, utilizando modelos da OpenAI e da Voyage.
- **`streamlit_rag_app_producao.py`**: interface web com autenticação de usuários, histórico de conversa e painéis administrativos.
- **`manage_production_users.py`**: utilitário para gestão de usuários em modo texto.

## Instalação

1. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
```

2. Instale as dependências listadas em `pyproject.toml`:

```bash
pip install astrapy>=2.0.1 \
            llama-index>=0.12.42 \
            numpy>=2.3.0 \
            openai>=1.86.0 \
            pandas>=2.2.3 \
            pillow>=11.2.1 \
            pymupdf>=1.26.1 \
            pymupdf4llm>=0.0.24 \
            python-dotenv>=1.1.0 \
            requests>=2.32.4 \
            streamlit>=1.45.1 \
            tqdm>=4.67.1 \
            upstash-vector>=0.8.0 \
            voyageai>=0.3.2
```

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as chaves necessárias:

- `OPENAI_API_KEY` &ndash; chave para acesso à API da OpenAI.
- `VOYAGE_API_KEY` &ndash; chave para embeddings multimodais da Voyage.
- `ASTRA_DB_API_ENDPOINT` &ndash; endpoint do Astra DB onde os documentos serão salvos.
- `ASTRA_DB_APPLICATION_TOKEN` &ndash; token de autenticação do Astra DB.
- `PDF_URL` (opcional) &ndash; caminho local ou URL do PDF que será indexado pelo `indexador.py`.

Exemplo de `.env`:

```ini
OPENAI_API_KEY=sk-...
VOYAGE_API_KEY=voyage-...
ASTRA_DB_API_ENDPOINT=https://db-id.us-east-1.apps.astra.datastax.com
ASTRA_DB_APPLICATION_TOKEN=token...
PDF_URL=https://exemplo.com/arquivo.pdf
```

## Executando o indexador

Depois de definir as variáveis de ambiente, basta executar:

```bash
python indexador.py
```

O script fará o download do PDF definido em `PDF_URL`, gerando embeddings de cada página e armazenando no Astra DB.

## Executando a aplicação Streamlit

Com as dependências instaladas e os documentos indexados, inicie a interface web:

```bash
streamlit run streamlit_rag_app_producao.py
```

A aplicação abrirá no navegador padrão em `http://localhost:8501`, permitindo login e consulta ao conteúdo indexado.

## Gerenciamento de usuários

Os dados de autenticação ficam salvos em `production_users.json`, arquivo que **não** é versionado por conter informações sensíveis. Para facilitar a configuração inicial, fornecemos um exemplo em `production_users.example.json` que ilustra o formato esperado:

```json
{
  "adminuser": {
    "password_hash": "examplehash123",
    "name": "Admin User",
    "role": "Admin",
    "organization": "Example Corp",
    "created_at": "2025-01-01T00:00:00",
    "last_login": "",
    "total_conversations": 0,
    "successful_queries": 0,
    "failed_queries": 0,
    "active": true,
    "notes": ""
  }
}
```

