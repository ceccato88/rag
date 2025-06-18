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

import requests, voyageai, pymupdf, pymupdf4llm
from PIL import Image
from tqdm import tqdm
from astrapy import DataAPIClient
from astrapy.constants import VectorMetric
from astrapy.info import CollectionDefinition, CollectionVectorOptions
from astrapy.collection import Collection

@dataclass
class Config:
    PDF_URL: str = "https://arxiv.org/pdf/2501.13956"
    IMAGE_DIR: str = "pdf_images"
    VOYAGE_EMBEDDING_DIM: int = 1024
    MAX_TOKENS_PER_INPUT: int = 32_000
    TOKENS_PER_PIXEL: float = 1 / 560
    TOKEN_CHARS_RATIO: int = 4  # caracteres por token estimado
    CONCURRENCY: int = 5
    ERROR_ON_LIMIT: bool = True
    BATCH_SIZE: int = 100
    COLLECTION_NAME: str = "pdf_documents"
    DOWNLOAD_TIMEOUT: int = 30
    DOWNLOAD_CHUNK_SIZE: int = 8192
    PIXMAP_SCALE: int = 2
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # segundos
    CLEANUP_MAX_AGE: int = 24  # horas

def get_config():
    """Cria configuração com valores do ambiente"""
    pdf_url = os.getenv("PDF_URL", "https://arxiv.org/pdf/2501.13956")
    return Config(PDF_URL=pdf_url)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ───── Helpers ─────
def create_doc_source_name(url: str) -> str:
    fn = url.split("/")[-1]
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.splitext(fn)[0])

def pixel_token_count(img: Image.Image, config: Config) -> int:
    return int((img.width * img.height) * config.TOKENS_PER_PIXEL)

def text_token_estimate(text: str, config: Config) -> int:
    return max(1, len(text) // config.TOKEN_CHARS_RATIO)

def fits_limits(txt: str, img: Image.Image, config: Config) -> bool:
    return (text_token_estimate(txt, config) + pixel_token_count(img, config)) <= config.MAX_TOKENS_PER_INPUT

def download_pdf_with_retry(url_or_path: str, config: Config) -> Optional[pymupdf.Document]:
    """Baixa ou abre um PDF com retry em caso de falha."""
    for attempt in range(config.MAX_RETRIES):
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
                with requests.get(url_or_path, stream=True, timeout=config.DOWNLOAD_TIMEOUT) as r:
                    r.raise_for_status()
                    buf = BytesIO()
                    for chunk in r.iter_content(config.DOWNLOAD_CHUNK_SIZE):
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
            if attempt == config.MAX_RETRIES - 1:
                logger.error("Falha ao processar PDF após %d tentativas: %s", config.MAX_RETRIES, e)
                return None
            
            delay = config.RETRY_DELAY * (2 ** attempt)  # Backoff exponencial
            logger.warning(f"Tentativa {attempt + 1} falhou: {e}. Tentando novamente em {delay:.1f}s...")
            time.sleep(delay)

def extract_page_content(pdf: pymupdf.Document, n: int,
                         src: str, img_dir: str, config: Config) -> Optional[Dict]:
    try:
        page = pdf[n]
        md = pymupdf4llm.to_markdown(pdf, pages=[n])
        pix = page.get_pixmap(matrix=pymupdf.Matrix(config.PIXMAP_SCALE, config.PIXMAP_SCALE))
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

def connect_to_astra(config: Config) -> Collection:
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
        if config.COLLECTION_NAME not in existing_collections:
            # Criar collection com configuração de vetor
            logger.info(f"Collection '{config.COLLECTION_NAME}' não existe. Criando...")
            collection_definition = CollectionDefinition(
                vector=CollectionVectorOptions(
                    dimension=config.VOYAGE_EMBEDDING_DIM,
                    metric=VectorMetric.COSINE,
                )
            )
            collection = database.create_collection(
                config.COLLECTION_NAME,
                definition=collection_definition,
            )
            logger.info(f"Collection '{config.COLLECTION_NAME}' criada com sucesso")
        else:
            logger.info(f"Collection '{config.COLLECTION_NAME}' já existe")
        
        # Sempre obter a collection (independentemente se existia ou foi criada)
        collection = database.get_collection(config.COLLECTION_NAME)
        return collection
        
    except Exception as e:
        logger.error(f"Erro ao conectar com Astra DB: {e}")
        raise

# ───── Async embedding ─────
async def embed_page(sema: asyncio.Semaphore, client: voyageai.AsyncClient,
                     doc: Dict, config: Config) -> Optional[Dict]:
    async with sema:
        try:
            img = Image.open(doc["image_path"])
            if not fits_limits(doc["markdown_text"], img, config):
                msg = f"Pág {doc['page_num']} excede limite {config.MAX_TOKENS_PER_INPUT} tokens"
                if config.ERROR_ON_LIMIT:
                    raise ValueError(msg)
                logger.error(msg); return None

            res = await client.multimodal_embed(
                inputs=[[doc["markdown_text"], img]],
                model="voyage-multimodal-3",
                input_type="document")
            vec = res.embeddings[0]
            if len(vec) != config.VOYAGE_EMBEDDING_DIM:
                raise ValueError(f"Dimensão inesperada: esperado {config.VOYAGE_EMBEDDING_DIM}, obtido {len(vec)}")
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

    # Usa configuração com valores do ambiente
    config = get_config()
    resource_manager = ResourceManager(config.IMAGE_DIR)
    
    with measure_time(metrics, "setup"):
        src = create_doc_source_name(config.PDF_URL)
        logger.info("Indexando documento: %s", src)
        logger.info("PDF URL/Path: %s", config.PDF_URL)

        # Limpa arquivos temporários antigos
        resource_manager.cleanup(max_age_hours=config.CLEANUP_MAX_AGE)

    pdf_path = config.PDF_URL  # Store the original PDF path for cleanup
    with measure_time(metrics, "download"):
        pdf = download_pdf_with_retry(config.PDF_URL, config)
        if not pdf: 
            logger.error("Não foi possível carregar o PDF")
            return

    docs = [c for i in tqdm(range(pdf.page_count), desc="Páginas")
            if (c := extract_page_content(pdf, i, src, config.IMAGE_DIR, config))]
    if not docs:
        logger.error("Nada extraído"); return

    logger.info("Gerando embeddings (%d concorrentes)…", config.CONCURRENCY)
    sema = asyncio.Semaphore(config.CONCURRENCY)
    async_client = voyageai.AsyncClient()
    try:
        with measure_time(metrics, "embeddings"):
            tasks = [embed_page(sema, async_client, d, config) for d in docs]
            embedded = [d for d in await asyncio.gather(*tasks) if d]
    finally:
        # Fecha conexão HTTP do cliente
        if hasattr(async_client, "aclose"):
            await async_client.aclose()

    if not embedded:
        logger.error("Nenhum embedding gerado"); return

    # Validar embeddings
    invalid_docs = [d for d in embedded if not validate_embedding(d["embedding"], config.VOYAGE_EMBEDDING_DIM)]
    if invalid_docs:
        logger.error(f"{len(invalid_docs)} documentos com embeddings inválidos")
        embedded = [d for d in embedded if validate_embedding(d["embedding"], config.VOYAGE_EMBEDDING_DIM)]

    with measure_time(metrics, "database"):
        # Conectar ao Astra DB
        collection = connect_to_astra(config)
        
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
    logger.info("Inserindo em lotes de %d…", config.BATCH_SIZE)
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
    
    for i in tqdm(range(0, len(documents), config.BATCH_SIZE), desc="Astra DB"):
        batch = documents[i:i+config.BATCH_SIZE]
        batch_idx = i//config.BATCH_SIZE
        
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