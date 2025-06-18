# indexer.py

import os
import re
import time
import logging
import asyncio
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from utils.validation import validate_document, validate_embedding
from utils.resource_manager import ResourceManager
from utils.metrics import ProcessingMetrics, measure_time
from config import SystemConfig

import requests, voyageai, pymupdf, pymupdf4llm
from PIL import Image
from tqdm import tqdm
from astrapy import DataAPIClient
from astrapy.constants import VectorMetric
from astrapy.info import CollectionDefinition, CollectionVectorOptions
from astrapy.collection import Collection

# Configuração centralizada
system_config = SystemConfig()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ───── Helpers ─────
def create_doc_source_name(url: str) -> str:
    fn = url.split("/")[-1]
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.splitext(fn)[0])

def pixel_token_count(img: Image.Image) -> int:
    return int((img.width * img.height) * system_config.processing.tokens_per_pixel)

def text_token_estimate(text: str) -> int:
    return max(1, len(text) // system_config.processing.token_chars_ratio)

def fits_limits(txt: str, img: Image.Image) -> bool:
    return (text_token_estimate(txt) + pixel_token_count(img)) <= system_config.rag.max_tokens_per_input

def download_pdf_with_retry(url_or_path: str) -> Optional[pymupdf.Document]:
    """Baixa ou abre um PDF com retry em caso de falha."""
    for attempt in range(system_config.processing.max_retries):
        try:
            # Detecta se é arquivo local ou URL
            is_url = url_or_path.startswith(('http://', 'https://'))
            is_local_path = not is_url and (
                os.path.exists(url_or_path) or 
                url_or_path.startswith(('./', '../', '/')) or
                os.path.sep in url_or_path
            )
            
            if is_local_path:
                # Arquivo local
                if not os.path.exists(url_or_path):
                    raise FileNotFoundError(f"Arquivo não encontrado: {url_or_path}")
                
                logger.info("Abrindo PDF local: %s", url_or_path)
                doc = pymupdf.open(url_or_path)
                logger.info("PDF carregado (%d páginas)", doc.page_count)
                return doc
                
            elif is_url:
                # Download da URL
                logger.info("Baixando PDF da URL: %s", url_or_path)
                with requests.get(url_or_path, stream=True, timeout=system_config.processing.download_timeout) as r:
                    r.raise_for_status()
                    buf = BytesIO()
                    for chunk in r.iter_content(system_config.processing.download_chunk_size):
                        buf.write(chunk)
                buf.seek(0)
                doc = pymupdf.open(stream=buf, filetype="pdf")
                logger.info("PDF baixado (%d páginas)", doc.page_count)
                return doc
                
            else:
                # Tentativa de interpretar como arquivo local primeiro, depois como URL
                if os.path.exists(url_or_path):
                    logger.info("Abrindo PDF local: %s", url_or_path)
                    doc = pymupdf.open(url_or_path)
                    logger.info("PDF carregado (%d páginas)", doc.page_count)
                    return doc
                else:
                    raise ValueError(f"Caminho inválido: '{url_or_path}'. Use um caminho local válido ou URL completa (http/https)")
                    
        except Exception as e:
            if attempt == system_config.multiagent.max_retries - 1:
                logger.error("Falha ao processar PDF após %d tentativas: %s", system_config.multiagent.max_retries, e)
                return None
            
            delay = system_config.multiagent.retry_delay * (2 ** attempt)  # Backoff exponencial
            logger.warning(f"Tentativa {attempt + 1} falhou: {e}. Tentando novamente em {delay:.1f}s...")
            time.sleep(delay)

def extract_page_content(pdf: pymupdf.Document, n: int,
                         src: str, img_dir: str) -> Optional[Dict]:
    try:
        page = pdf[n]
        md = pymupdf4llm.to_markdown(pdf, pages=[n])
        pix = page.get_pixmap(matrix=pymupdf.Matrix(system_config.processing.pixmap_scale, system_config.processing.pixmap_scale))
        img_path = os.path.join(img_dir, f"{src}_page_{n+1}.png")
        pix.save(img_path)
        return {"id": f"{src}_{n}", "page_num": n+1, "markdown_text": md,
                "image_path": img_path, "doc_source": src}
    except Exception as e:
        logger.error("Erro página %d: %s", n+1, e)
        return None

def validate_env_vars() -> None:
    """Valida se todas as variáveis de ambiente necessárias estão definidas"""
    required_vars = [
        "VOYAGE_API_KEY",
        "ASTRA_DB_API_ENDPOINT", 
        "ASTRA_DB_APPLICATION_TOKEN"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise RuntimeError(
            f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}"
        )

def connect_to_astra() -> Collection:
    """Conecta ao Astra DB e retorna a collection"""
    try:
        endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        
        if not endpoint or not token:
            raise RuntimeError("Variáveis ASTRA_DB_API_ENDPOINT e ASTRA_DB_APPLICATION_TOKEN devem estar definidas")
        
        # Criar cliente e conectar ao database
        client = DataAPIClient()
        database = client.get_database(endpoint, token=token)
        
        logger.info(f"Conectado ao database {database.info().name}")
        
        # Listar collections existentes
        existing_collections = database.list_collection_names()
        logger.info(f"Collections existentes: {existing_collections}")
        
        # Verificar se collection existe e criar se necessário
        if system_config.rag.collection_name not in existing_collections:
            # Criar collection com configuração de vetor
            logger.info(f"Collection '{system_config.rag.collection_name}' não existe. Criando...")
            collection_definition = CollectionDefinition(
                vector=CollectionVectorOptions(
                    dimension=system_config.rag.voyage_embedding_dim,
                    metric=VectorMetric.COSINE,
                )
            )
            collection = database.create_collection(
                system_config.rag.collection_name,
                definition=collection_definition,
            )
            logger.info(f"Collection '{system_config.rag.collection_name}' criada com sucesso")
        else:
            logger.info(f"Collection '{system_config.rag.collection_name}' já existe")
        
        # Sempre obter a collection (independentemente se existia ou foi criada)
        collection = database.get_collection(system_config.rag.collection_name)
        return collection
        
    except Exception as e:
        logger.error(f"Erro ao conectar com Astra DB: {e}")
        raise

# ───── Async embedding ─────
async def embed_page(sema: asyncio.Semaphore, client: voyageai.AsyncClient,
                     doc: Dict) -> Optional[Dict]:
    async with sema:
        try:
            img = Image.open(doc["image_path"])
            if not fits_limits(doc["markdown_text"], img):
                msg = f"Pág {doc['page_num']} excede limite {system_config.rag.max_tokens_per_input} tokens"
                logger.error(msg)
                return None

            res = await client.multimodal_embed(
                inputs=[[doc["markdown_text"], img]],
                model=system_config.rag.multimodal_model,
                input_type="document")
            vec = res.embeddings[0]
            if len(vec) != system_config.rag.voyage_embedding_dim:
                raise ValueError(f"Dimensão inesperada: esperado {system_config.rag.voyage_embedding_dim}, obtido {len(vec)}")
            doc["embedding"] = vec
            return doc
        except Exception as e:
            logger.error("Embedding falhou pág %d: %s", doc["page_num"], e)
            return None

# ───── Main ─────
async def main() -> None:
    load_dotenv()
    metrics = ProcessingMetrics()
    
    try:
        validate_env_vars()
    except RuntimeError as e:
        logger.error(str(e))
        return

    # Sistema usa configuração centralizada
    resource_manager = ResourceManager(system_config.processing.image_dir)
    
    with measure_time(metrics, "setup"):
        src = create_doc_source_name(system_config.processing.default_pdf_url)
        logger.info("Indexando documento: %s", src)
        logger.info("PDF URL/Path: %s", system_config.processing.default_pdf_url)

        # Limpa arquivos temporários antigos
        resource_manager.cleanup(max_age_hours=system_config.processing.cleanup_max_age)

    pdf_path = system_config.processing.default_pdf_url  # Store the original PDF path for cleanup
    with measure_time(metrics, "download"):
        pdf = download_pdf_with_retry(system_config.processing.default_pdf_url)
        if not pdf: 
            logger.error("Não foi possível carregar o PDF")
            return

    docs = [c for i in tqdm(range(pdf.page_count), desc="Páginas")
            if (c := extract_page_content(pdf, i, src, system_config.processing.image_dir))]
    if not docs:
        logger.error("Nada extraído"); return

    logger.info("Gerando embeddings (%d concorrentes)…", system_config.processing.processing_concurrency)
    sema = asyncio.Semaphore(system_config.processing.processing_concurrency)
    async_client = voyageai.AsyncClient()
    try:
        with measure_time(metrics, "embeddings"):
            tasks = [embed_page(sema, async_client, d) for d in docs]
            embedded = [d for d in await asyncio.gather(*tasks) if d]
    finally:
        # Fecha conexão HTTP do cliente
        if hasattr(async_client, "aclose"):
            await async_client.aclose()

    if not embedded:
        logger.error("Nenhum embedding gerado"); return

    # Validar embeddings
    invalid_docs = [d for d in embedded if not validate_embedding(d["embedding"], system_config.rag.voyage_embedding_dim)]
    if invalid_docs:
        logger.error(f"{len(invalid_docs)} documentos com embeddings inválidos")
        embedded = [d for d in embedded if validate_embedding(d["embedding"], system_config.rag.voyage_embedding_dim)]

    with measure_time(metrics, "database"):
        # Conectar ao Astra DB
        collection = connect_to_astra()
        
        # Remover documentos antigos do mesmo source
        try:
            del_result = collection.delete_many({"doc_source": src})
            if del_result.deleted_count > 0:
                logger.info("Removidos %d documentos antigos (%s)", del_result.deleted_count, src)
            else:
                logger.info("Nenhum documento antigo encontrado para remover (%s)", src)
        except Exception as e:
            logger.warning("Aviso ao tentar remover documentos antigos: %s", e)

    # Preparar documentos para inserção
    documents = [
        {
            "_id": d["id"],
            "page_num": d["page_num"],
            "file_path": d["image_path"],
            "doc_source": d["doc_source"],
            "markdown_text": d["markdown_text"],
            "$vector": d["embedding"]
        } for d in embedded
    ]

    # Inserir em lotes
    logger.info("Inserindo em lotes de %d…", system_config.processing.batch_size)
    inserted_count = 0
    
    def insert_document_fallback(doc: Dict, batch_idx: int, doc_idx: int) -> bool:
        """Tenta inserir documento individual como fallback"""
        try:
            collection.insert_one(doc)
            logger.debug("Documento individual inserido: %s", doc["_id"])
            return True
        except Exception as e:
            logger.error("Erro ao inserir documento individual %d do lote %d: %s", doc_idx+1, batch_idx+1, e)
            return False
    
    for i in tqdm(range(0, len(documents), system_config.processing.batch_size), desc="Astra DB"):
        batch = documents[i:i+system_config.processing.batch_size]
        batch_idx = i//system_config.processing.batch_size
        
        try:
            result = collection.insert_many(batch, ordered=False)
            inserted_count += len(result.inserted_ids)
            logger.info("Lote %d inserido com sucesso: %d documentos", batch_idx + 1, len(result.inserted_ids))
        except Exception as e:
            logger.error("Erro ao inserir lote %d: %s", batch_idx + 1, e)
            # Fallback: inserir um por um
            for j, doc in enumerate(batch):
                if insert_document_fallback(doc, batch_idx, j):
                    inserted_count += 1

    # Finaliza métricas e mostra resumo
    metrics.finish()
    metrics.log_summary()

    logger.info("✅ Indexação finalizada: %d/%d páginas inseridas", inserted_count, pdf.page_count)
    pdf.close()
    
    # Remove o arquivo PDF temporário se foi criado a partir de upload
    if os.path.exists(pdf_path) and pdf_path.startswith('/tmp/') or pdf_path.startswith('./temp_'):
        try:
            os.remove(pdf_path)
            logger.info("🗑️ PDF temporário removido: %s", pdf_path)
        except Exception as e:
            logger.warning("⚠️ Erro ao remover PDF temporário: %s", e)

if __name__ == "__main__":
    asyncio.run(main())