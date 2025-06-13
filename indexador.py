# indexador.py

import os, re, logging, asyncio
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

import requests, voyageai, pymupdf, pymupdf4llm
from PIL import Image
from tqdm import tqdm
from astrapy import DataAPIClient
from astrapy.constants import VectorMetric
from astrapy.info import CollectionDefinition, CollectionVectorOptions

# ───── Configs principais ─────
PDF_URL = "https://arxiv.org/pdf/2501.13956"
IMAGE_DIR = "pdf_images"
VOYAGE_EMBEDDING_DIM = 1024
MAX_TOKENS_PER_INPUT = 32_000
TOKENS_PER_PIXEL = 1 / 560
CONCURRENCY = 5
ERROR_ON_LIMIT = True
BATCH_SIZE = 100
COLLECTION_NAME = "pdf_documents"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ───── Helpers ─────
def create_doc_source_name(url: str) -> str:
    fn = url.split("/")[-1]
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.splitext(fn)[0])

def pixel_token_count(img: Image.Image) -> int:
    return int((img.width * img.height) * TOKENS_PER_PIXEL)

def text_token_estimate(text: str) -> int:
    return max(1, len(text) // 4)

def fits_limits(txt: str, img: Image.Image) -> bool:
    return (text_token_estimate(txt) + pixel_token_count(img)) <= MAX_TOKENS_PER_INPUT

def download_pdf(url: str) -> Optional[pymupdf.Document]:
    try:
        logger.info("Baixando PDF (streaming)…")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            buf = BytesIO()
            for chunk in r.iter_content(8192):
                buf.write(chunk)
        buf.seek(0)
        doc = pymupdf.open(stream=buf, filetype="pdf")
        logger.info("PDF baixado (%d páginas)", doc.page_count)
        return doc
    except Exception as e:
        logger.error("Falha download PDF: %s", e)
        return None

def extract_page_content(pdf: pymupdf.Document, n: int,
                         src: str, img_dir: str) -> Optional[Dict]:
    try:
        page = pdf[n]
        md = pymupdf4llm.to_markdown(pdf, pages=[n])
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        img_path = os.path.join(img_dir, f"{src}_page_{n+1}.png")
        pix.save(img_path)
        return {"id": f"{src}_{n}", "page_num": n+1, "markdown_text": md,
                "image_path": img_path, "doc_source": src}
    except Exception as e:
        logger.error("Erro página %d: %s", n+1, e)
        return None

def connect_to_astra() -> object:
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
        if COLLECTION_NAME not in existing_collections:
            # Criar collection com configuração de vetor
            logger.info(f"Collection '{COLLECTION_NAME}' não existe. Criando...")
            collection_definition = CollectionDefinition(
                vector=CollectionVectorOptions(
                    dimension=VOYAGE_EMBEDDING_DIM,
                    metric=VectorMetric.COSINE,
                )
            )
            collection = database.create_collection(
                COLLECTION_NAME,
                definition=collection_definition,
            )
            logger.info(f"Collection '{COLLECTION_NAME}' criada com sucesso")
        else:
            logger.info(f"Collection '{COLLECTION_NAME}' já existe")
        
        # Sempre obter a collection (independentemente se existia ou foi criada)
        collection = database.get_collection(COLLECTION_NAME)
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
                msg = f"Pág {doc['page_num']} excede limite 32k tokens"
                if ERROR_ON_LIMIT:
                    raise ValueError(msg)
                logger.error(msg); return None

            res = await client.multimodal_embed(
                inputs=[[doc["markdown_text"], img]],
                model="voyage-multimodal-3",
                input_type="document")
            vec = res.embeddings[0]
            if len(vec) != VOYAGE_EMBEDDING_DIM:
                raise ValueError("Dimensão inesperada")
            doc["embedding"] = vec
            return doc
        except Exception as e:
            logger.error("Embedding falhou pág %d: %s", doc["page_num"], e)
            return None

# ───── Main ─────
async def main() -> None:
    load_dotenv()
    if not (os.getenv("VOYAGE_API_KEY") and os.getenv("ASTRA_DB_API_ENDPOINT") and os.getenv("ASTRA_DB_APPLICATION_TOKEN")):
        logger.error("Variáveis de ambiente ausentes (VOYAGE_API_KEY, ASTRA_DB_API_ENDPOINT, ASTRA_DB_APPLICATION_TOKEN)"); return

    src = create_doc_source_name(PDF_URL)
    logger.info("Indexando documento: %s", src)

    pdf = download_pdf(PDF_URL)
    if not pdf: return
    Path(IMAGE_DIR).mkdir(exist_ok=True)

    docs = [c for i in tqdm(range(pdf.page_count), desc="Páginas")
            if (c := extract_page_content(pdf, i, src, IMAGE_DIR))]
    if not docs:
        logger.error("Nada extraído"); return

    logger.info("Gerando embeddings (%d concorrentes)…", CONCURRENCY)
    sema = asyncio.Semaphore(CONCURRENCY)
    async_client = voyageai.AsyncClient()
    try:
        tasks = [embed_page(sema, async_client, d) for d in docs]
        embedded = [d for d in await asyncio.gather(*tasks) if d]
    finally:
        # fecha conexão HTTP do cliente
        if hasattr(async_client, "aclose"):
            await async_client.aclose()

    if not embedded:
        logger.error("Nenhum embedding gerado"); return

    # Conectar ao Astra DB
    collection = connect_to_astra()
    
    # Remover documentos antigos do mesmo source (só se a collection existir e tiver dados)
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
    logger.info("Inserindo em lotes de %d…", BATCH_SIZE)
    inserted_count = 0
    for i in tqdm(range(0, len(documents), BATCH_SIZE), desc="Astra DB"):
        batch = documents[i:i+BATCH_SIZE]
        try:
            result = collection.insert_many(batch, ordered=False)
            inserted_count += len(result.inserted_ids)
            logger.info("Lote %d inserido com sucesso: %d documentos", i//BATCH_SIZE + 1, len(result.inserted_ids))
        except Exception as e:
            logger.error("Erro ao inserir lote %d: %s", i//BATCH_SIZE + 1, e)
            # Tentar inserir um por um se o lote falhar
            for j, doc in enumerate(batch):
                try:
                    single_result = collection.insert_one(doc)
                    inserted_count += 1
                    logger.debug("Documento individual inserido: %s", single_result.inserted_id)
                except Exception as single_e:
                    logger.error("Erro ao inserir documento individual %d do lote %d: %s", j+1, i//BATCH_SIZE + 1, single_e)

    logger.info("✅ Indexação finalizada: %d/%d páginas inseridas", inserted_count, pdf.page_count)
    pdf.close()

if __name__ == "__main__":
    asyncio.run(main())