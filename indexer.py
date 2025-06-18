#!/usr/bin/env python3
"""
Indexador simplificado para o sistema RAG Multi-Agente.
Processa PDFs de URLs, extrai texto e imagens, e indexa no AstraDB.
"""

import os
import re
import time
import logging
import asyncio
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

import requests
import voyageai
import pymupdf
import pymupdf4llm
from PIL import Image
from tqdm import tqdm
from astrapy import DataAPIClient
from astrapy.collection import Collection

from config import SystemConfig
from utils.validation import validate_document, validate_embedding
from utils.resource_manager import ResourceManager
from utils.metrics import ProcessingMetrics, measure_time

# Configuração
load_dotenv()
system_config = SystemConfig()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def create_doc_source_name(url: str) -> str:
    """Cria nome do documento a partir da URL"""
    fn = url.split("/")[-1]
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.splitext(fn)[0])

def pixel_token_count(img: Image.Image) -> int:
    """Calcula tokens aproximados de uma imagem"""
    return int((img.width * img.height) * system_config.processing.tokens_per_pixel)

def text_token_estimate(text: str) -> int:
    """Estima tokens de um texto"""
    return max(1, len(text) // system_config.processing.token_chars_ratio)

def download_pdf_with_retry(url: str) -> Optional[pymupdf.Document]:
    """Baixa PDF com retry em caso de falha"""
    max_retries = getattr(system_config.processing, 'max_retries', 3)
    for attempt in range(max_retries):
        try:
            if url.startswith(('http://', 'https://')):
                logger.info(f"Baixando PDF: {url}")
                download_timeout = getattr(system_config.processing, 'download_timeout', 30)
                with requests.get(url, stream=True, timeout=download_timeout) as r:
                    r.raise_for_status()
                    buf = BytesIO()
                    download_chunk_size = getattr(system_config.processing, 'download_chunk_size', 8192)
                    for chunk in r.iter_content(download_chunk_size):
                        buf.write(chunk)
                buf.seek(0)
                doc = pymupdf.open(stream=buf, filetype="pdf")
                logger.info(f"PDF baixado ({doc.page_count} páginas)")
                return doc
            else:
                # Arquivo local
                if os.path.exists(url):
                    logger.info(f"Abrindo PDF local: {url}")
                    doc = pymupdf.open(url)
                    logger.info(f"PDF carregado ({doc.page_count} páginas)")
                    return doc
                else:
                    raise FileNotFoundError(f"Arquivo não encontrado: {url}")
                    
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Falha ao baixar PDF após {max_retries} tentativas: {e}")
                return None
            
            retry_delay = getattr(system_config.processing, 'retry_delay', 1.0)
            delay = retry_delay * (2 ** attempt)
            logger.warning(f"Tentativa {attempt + 1} falhou: {e}. Tentando novamente em {delay:.1f}s...")
            time.sleep(delay)
    
    return None

def extract_page_content(pdf: pymupdf.Document, page_num: int, doc_source: str, img_dir: str) -> Optional[Dict]:
    """Extrai conteúdo de uma página do PDF"""
    try:
        page = pdf[page_num]
        
        # Extrair markdown
        md = pymupdf4llm.to_markdown(pdf, pages=[page_num])
        
        # Extrair imagem da página
        pixmap_scale = getattr(system_config.processing, 'pixmap_scale', 2)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(pixmap_scale, pixmap_scale))
        img_path = os.path.join(img_dir, f"{doc_source}_page_{page_num+1}.png")
        
        # Criar diretório se não existir
        os.makedirs(img_dir, exist_ok=True)
        pix.save(img_path)
        
        return {
            "id": f"{doc_source}_{page_num}",
            "page_num": page_num + 1,
            "markdown_text": md,
            "image_path": img_path,
            "doc_source": doc_source
        }
        
    except Exception as e:
        logger.error(f"Erro ao extrair página {page_num + 1}: {e}")
        return None

async def embed_page(semaphore: asyncio.Semaphore, client: voyageai.AsyncClient, doc: Dict) -> Optional[Dict]:
    """Gera embedding para uma página"""
    async with semaphore:
        try:
            # Carregar imagem como PIL Image
            from PIL import Image
            pil_image = Image.open(doc["image_path"])
            
            # Preparar conteúdo multimodal (formato correto para Voyage)
            content = [doc["markdown_text"], pil_image]
            
            # Gerar embedding
            result = await client.multimodal_embed(
                inputs=[content], 
                model=system_config.rag.multimodal_model
            )
            
            if result and result.embeddings:
                doc["embedding"] = result.embeddings[0]
                return doc
            else:
                logger.warning(f"Embedding vazio para {doc['id']}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao gerar embedding para {doc['id']}: {e}")
            return None

def connect_to_astra() -> Collection:
    """Conecta ao AstraDB e retorna a collection"""
    try:
        endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        
        if not endpoint or not token:
            raise RuntimeError("Variáveis ASTRA_DB_API_ENDPOINT e ASTRA_DB_APPLICATION_TOKEN devem estar definidas")
        
        # Criar cliente e conectar
        client = DataAPIClient()
        database = client.get_database(endpoint, token=token)
        
        logger.info(f"Conectado ao database: {database.info().name}")
        
        # Obter collection
        collection_name = system_config.rag.collection_name
        collection = database.get_collection(collection_name)
        
        logger.info(f"Usando collection: {collection_name}")
        return collection
        
    except Exception as e:
        logger.error(f"Erro ao conectar com AstraDB: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL DE INDEXAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def process_pdf_from_url(url: str, doc_source: str = None) -> bool:
    """
    Processa PDF de uma URL e indexa no AstraDB.
    
    Args:
        url: URL do PDF ou caminho local
        doc_source: Nome/identificador do documento
    
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        # Usar URL como doc_source se não fornecido
        if not doc_source:
            doc_source = create_doc_source_name(url)
        
        logger.info(f"🚀 Iniciando indexação: {doc_source}")
        logger.info(f"📄 PDF: {url}")
        
        # 1. Baixar/abrir PDF
        pdf = download_pdf_with_retry(url)
        if not pdf:
            logger.error("❌ Não foi possível carregar o PDF")
            return False
        
        # 2. Extrair conteúdo das páginas
        img_dir = getattr(system_config.processing, 'image_dir', 'pdf_images')
        os.makedirs(img_dir, exist_ok=True)
        
        logger.info(f"📊 Extraindo conteúdo de {pdf.page_count} páginas...")
        docs = []
        
        for i in tqdm(range(pdf.page_count), desc="Extraindo páginas"):
            content = extract_page_content(pdf, i, doc_source, img_dir)
            if content:
                docs.append(content)
        
        if not docs:
            logger.error("❌ Nenhum conteúdo extraído")
            return False
        
        logger.info(f"✅ Extraídas {len(docs)} páginas")
        
        # 3. Gerar embeddings
        logger.info(f"🧠 Gerando embeddings multimodais...")
        embedded_docs = asyncio.run(_generate_embeddings_async(docs))
        
        if not embedded_docs:
            logger.error("❌ Nenhum embedding gerado")
            return False
        
        logger.info(f"✅ Gerados {len(embedded_docs)} embeddings")
        
        # 4. Conectar ao AstraDB e inserir
        collection = connect_to_astra()
        
        # Remover documentos antigos do mesmo source
        try:
            del_result = collection.delete_many({"doc_source": doc_source})
            if del_result.deleted_count > 0:
                logger.info(f"🗑️ Removidos {del_result.deleted_count} documentos antigos")
        except Exception as e:
            logger.warning(f"⚠️ Aviso ao remover documentos antigos: {e}")
        
        # Preparar documentos para inserção
        documents = [
            {
                "_id": doc["id"],
                "page_num": doc["page_num"],
                "file_path": doc["image_path"],
                "doc_source": doc["doc_source"],
                "markdown_text": doc["markdown_text"],
                "$vector": doc["embedding"]
            } for doc in embedded_docs
        ]
        
        # Inserir em lotes
        logger.info(f"💾 Inserindo {len(documents)} documentos...")
        inserted_count = 0
        batch_size = getattr(system_config.processing, 'batch_size', 100)
        
        for i in tqdm(range(0, len(documents), batch_size), desc="Inserindo no AstraDB"):
            batch = documents[i:i+batch_size]
            try:
                result = collection.insert_many(batch)
                inserted_count += len(result.inserted_ids)
            except Exception as e:
                logger.warning(f"⚠️ Erro no lote {i//batch_size + 1}: {e}")
                # Tentar inserir individualmente
                for doc in batch:
                    try:
                        collection.insert_one(doc)
                        inserted_count += 1
                    except Exception as individual_error:
                        logger.error(f"❌ Erro ao inserir {doc['_id']}: {individual_error}")
        
        logger.info(f"✅ Indexação concluída!")
        logger.info(f"📊 Documentos inseridos: {inserted_count}/{len(documents)}")
        logger.info(f"🎯 Doc source: {doc_source}")
        
        return inserted_count > 0
        
    except Exception as e:
        logger.error(f"❌ Erro na indexação: {e}")
        return False

async def _generate_embeddings_async(docs: List[Dict]) -> List[Dict]:
    """Gera embeddings assíncronos para lista de documentos"""
    try:
        processing_concurrency = getattr(system_config.processing, 'processing_concurrency', 5)
        logger.info(f"🔄 Gerando embeddings com {processing_concurrency} workers...")
        
        semaphore = asyncio.Semaphore(processing_concurrency)
        async_client = voyageai.AsyncClient()
        
        try:
            tasks = [embed_page(semaphore, async_client, doc) for doc in docs]
            embedded = [doc for doc in await asyncio.gather(*tasks) if doc]
            
            # Validar embeddings
            valid_docs = []
            for doc in embedded:
                if validate_embedding(doc["embedding"], system_config.rag.voyage_embedding_dim):
                    valid_docs.append(doc)
                else:
                    logger.warning(f"⚠️ Embedding inválido para {doc['id']}")
            
            return valid_docs
            
        finally:
            # Fechar conexão do cliente
            if hasattr(async_client, "aclose"):
                await async_client.aclose()
                
    except Exception as e:
        logger.error(f"❌ Erro ao gerar embeddings: {e}")
        return []

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL PARA EXECUÇÃO DIRETA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Função principal para execução via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Indexar PDF no sistema RAG")
    parser.add_argument("url", help="URL ou caminho do PDF")
    parser.add_argument("--doc-source", help="Nome/identificador do documento")
    
    args = parser.parse_args()
    
    # Validar variáveis de ambiente
    required_vars = ["VOYAGE_API_KEY", "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
        return False
    
    # Executar indexação
    success = process_pdf_from_url(args.url, args.doc_source)
    
    if success:
        logger.info("🎉 Indexação realizada com sucesso!")
        return True
    else:
        logger.error("💥 Falha na indexação!")
        return False

if __name__ == "__main__":
    main()