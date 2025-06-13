# indexador.py

import os, re, logging, asyncio
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

import requests, voyageai, pymupdf, pymupdf4llm
from PIL import Image
from tqdm import tqdm
from upstash_vector import Index

# ───── Configs principais ─────
PDF_URL = "https://arxiv.org/pdf/2501.13956"
IMAGE_DIR = "pdf_images"
VOYAGE_EMBEDDING_DIM = 1024
MAX_TOKENS_PER_INPUT = 32_000
TOKENS_PER_PIXEL = 1 / 560
CONCURRENCY = 5
ERROR_ON_LIMIT = True
BATCH_SIZE = 100

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
    if not (os.getenv("VOYAGE_API_KEY") and os.getenv("UPSTASH_VECTOR_REST_URL")):
        logger.error("Variáveis de ambiente ausentes"); return

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

    upstash = Index.from_env()
    del_res = upstash.delete(filter=f"doc_source = '{src}'")
    logger.info("Removidos %d vetores antigos (%s)", del_res.deleted, src)

    vectors: List[Tuple[str, List[float], Dict]] = [
        (
            d["id"], d["embedding"],
            {"page_num": d["page_num"], "file_path": d["image_path"],
             "doc_source": d["doc_source"], "markdown_text": d["markdown_text"]}
        ) for d in embedded
    ]

    logger.info("Upsert em lotes de %d…", BATCH_SIZE)
    for i in tqdm(range(0, len(vectors), BATCH_SIZE), desc="Upstash"):
        upstash.upsert(vectors=vectors[i:i+BATCH_SIZE])

    logger.info("✅ Indexação finalizada: %d/%d páginas", len(embedded), pdf.page_count)
    pdf.close()

if __name__ == "__main__":
    asyncio.run(main())
