#!/usr/bin/env python3
"""
Indexador Refatorado v2.0.0 - Sistema RAG Multi-Agente

Indexador simplificado e otimizado que integra com as APIs refatoradas.
Usa modelos nativos e factory patterns para consistência com o sistema.
"""

import os
import re
import time
import logging
import asyncio
from io import BytesIO
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

import requests
import voyageai
import pymupdf
import pymupdf4llm
from PIL import Image
from tqdm import tqdm
from astrapy import DataAPIClient
from astrapy.collection import Collection

from .config import SystemConfig
from .constants import NATIVE_MODELS_CONFIG, API_REFACTORED_CONFIG, VALIDATION_CONFIG
from ..utils.validation import validate_document, validate_embedding
from ..utils.resource_manager import ResourceManager
from ..utils.metrics import ProcessingMetrics
# from utils.metrics import measure_time  # Temporariamente removido

# Configuração
load_dotenv()
system_config = SystemConfig()

# Setup de logging otimizado
logging.basicConfig(
    level=getattr(logging, system_config.production.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# MODELOS DE DADOS NATIVOS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IndexingResult:
    """Resultado nativo de indexação usando padrões das APIs refatoradas"""
    success: bool
    doc_source: str
    pages_processed: int = 0
    chunks_created: int = 0
    images_extracted: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PageContent:
    """Conteúdo de página usando estrutura nativa"""
    id: str
    page_num: int
    markdown_text: str
    image_path: str
    doc_source: str
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None
    processing_time: Optional[float] = None

# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY PARA RESULTADOS DE INDEXAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

class IndexingResultFactory:
    """Factory para criar resultados de indexação consistentes"""
    
    @staticmethod
    def create_success_result(
        doc_source: str,
        pages_processed: int,
        chunks_created: int,
        processing_time: float,
        images_extracted: int = None,
        **kwargs
    ) -> IndexingResult:
        """Cria resultado de sucesso"""
        # Se não especificado, assumir 1 imagem por página como padrão
        if images_extracted is None:
            images_extracted = pages_processed
            
        return IndexingResult(
            success=True,
            doc_source=doc_source,
            pages_processed=pages_processed,
            chunks_created=chunks_created,
            images_extracted=images_extracted,
            processing_time=processing_time,
            metadata={
                "indexer_version": "2.0.0",
                "model_used": system_config.rag.multimodal_model,
                "embedding_dimension": system_config.rag.voyage_embedding_dim,
                "native_processing": True,
                **kwargs
            }
        )
    
    @staticmethod
    def create_error_result(
        doc_source: str,
        error: str,
        processing_time: float = 0.0,
        **kwargs
    ) -> IndexingResult:
        """Cria resultado de erro"""
        return IndexingResult(
            success=False,
            doc_source=doc_source,
            error=error,
            processing_time=processing_time,
            metadata={
                "indexer_version": "2.0.0",
                "error_occurred": True,
                **kwargs
            }
        )

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDADOR NATIVO INTEGRADO
# ═══════════════════════════════════════════════════════════════════════════════

class IndexingValidator:
    """Validador usando configurações nativas do sistema"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Valida URL ou caminho de arquivo"""
        if not url or len(url.strip()) < 3:
            return False
        
        # URL HTTP/HTTPS
        if url.startswith(('http://', 'https://')):
            return True
        
        # Arquivo local
        if os.path.exists(url) and url.lower().endswith('.pdf'):
            return True
        
        return False
    
    @staticmethod
    def validate_doc_source(doc_source: str) -> bool:
        """Valida nome do documento"""
        if not doc_source:
            return False
        
        # Verificar tamanho
        if len(doc_source) > 100:
            return False
        
        # Verificar caracteres válidos
        return bool(re.match(r'^[a-zA-Z0-9_.-]+$', doc_source))
    
    @staticmethod
    def validate_environment() -> Tuple[bool, List[str]]:
        """Valida variáveis de ambiente necessárias"""
        required_vars = VALIDATION_CONFIG['REQUIRED_ENV_VARS']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        return len(missing_vars) == 0, missing_vars

# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSADOR NATIVO OTIMIZADO
# ═══════════════════════════════════════════════════════════════════════════════

class NativeIndexingProcessor:
    """Processador principal usando configurações nativas"""
    
    def __init__(self):
        self.config = system_config
        self.metrics = ProcessingMetrics()
        # self.resource_manager = ResourceManager()  # Temporariamente removido
        
    def create_doc_source_name(self, url: str) -> str:
        """Cria nome do documento a partir da URL"""
        fn = url.split("/")[-1]
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.splitext(fn)[0])
        
        # Validar resultado
        if not IndexingValidator.validate_doc_source(clean_name):
            # Fallback para timestamp se inválido
            clean_name = f"doc_{int(time.time())}"
        
        return clean_name
    
    def calculate_token_count(self, content: PageContent) -> int:
        """Calcula contagem de tokens usando configurações nativas"""
        text_tokens = len(content.markdown_text) // self.config.processing.token_chars_ratio
        
        # Tokens da imagem (se existir)
        image_tokens = 0
        if os.path.exists(content.image_path):
            try:
                with Image.open(content.image_path) as img:
                    image_tokens = int((img.width * img.height) * self.config.processing.tokens_per_pixel)
            except Exception:
                image_tokens = 0
        
        return max(1, text_tokens + image_tokens)
    
    def download_pdf_with_retry(self, url: str) -> Optional[pymupdf.Document]:
        """Baixa PDF com retry usando configurações nativas"""
        max_retries = self.config.multiagent.max_retries
        
        for attempt in range(max_retries):
            try:
                if url.startswith(('http://', 'https://')):
                    logger.info(f"📥 Baixando PDF: {url}")
                    
                    with requests.get(
                        url, 
                        stream=True, 
                        timeout=self.config.processing.download_timeout
                    ) as r:
                        r.raise_for_status()
                        buf = BytesIO()
                        
                        for chunk in r.iter_content(self.config.processing.download_chunk_size):
                            buf.write(chunk)
                    
                    buf.seek(0)
                    doc = pymupdf.open(stream=buf, filetype="pdf")
                    logger.info(f"✅ PDF baixado ({doc.page_count} páginas)")
                    return doc
                else:
                    # Arquivo local
                    if os.path.exists(url):
                        logger.info(f"📂 Abrindo PDF local: {url}")
                        doc = pymupdf.open(url)
                        logger.info(f"✅ PDF carregado ({doc.page_count} páginas)")
                        return doc
                    else:
                        raise FileNotFoundError(f"Arquivo não encontrado: {url}")
                        
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"❌ Falha ao baixar PDF após {max_retries} tentativas: {e}")
                    return None
                
                delay = self.config.multiagent.retry_delay * (2 ** attempt)
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {e}. Retry em {delay:.1f}s...")
                time.sleep(delay)
        
        return None
    
    def extract_page_content(self, pdf: pymupdf.Document, page_num: int, doc_source: str) -> Optional[PageContent]:
        """Extrai conteúdo de uma página usando estrutura nativa"""
        start_time = time.time()
        
        try:
            page = pdf[page_num]
            
            # Extrair markdown
            md = pymupdf4llm.to_markdown(pdf, pages=[page_num])
            
            # Extrair imagem da página
            img_dir = self.config.processing.image_dir
            os.makedirs(img_dir, exist_ok=True)
            
            pixmap_scale = self.config.processing.pixmap_scale
            pix = page.get_pixmap(matrix=pymupdf.Matrix(pixmap_scale, pixmap_scale))
            img_path = os.path.join(img_dir, f"{doc_source}_page_{page_num+1}.png")
            pix.save(img_path)
            
            # Criar objeto nativo
            content = PageContent(
                id=f"{doc_source}_{page_num}",
                page_num=page_num + 1,
                markdown_text=md,
                image_path=img_path,
                doc_source=doc_source,
                processing_time=time.time() - start_time
            )
            
            # Calcular tokens
            content.token_count = self.calculate_token_count(content)
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair página {page_num + 1}: {e}")
            return None
    
    async def generate_embedding(self, semaphore: asyncio.Semaphore, client: voyageai.AsyncClient, content: PageContent) -> bool:
        """Gera embedding para conteúdo usando cliente nativo"""
        async with semaphore:
            try:
                # Carregar imagem
                pil_image = Image.open(content.image_path)
                
                # Preparar conteúdo multimodal
                multimodal_content = [content.markdown_text, pil_image]
                
                # Gerar embedding
                result = await client.multimodal_embed(
                    inputs=[multimodal_content], 
                    model=self.config.rag.multimodal_model
                )
                
                if result and result.embeddings:
                    content.embedding = result.embeddings[0]
                    
                    # Validar embedding
                    if validate_embedding(content.embedding, self.config.rag.voyage_embedding_dim):
                        return True
                    else:
                        logger.warning(f"⚠️ Embedding inválido para {content.id}")
                        return False
                else:
                    logger.warning(f"⚠️ Embedding vazio para {content.id}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erro ao gerar embedding para {content.id}: {e}")
                return False
    
    def connect_to_astra(self) -> Collection:
        """Conecta ao AstraDB usando configurações nativas"""
        try:
            endpoint = self.config.rag.astra_db_api_endpoint
            token = self.config.rag.astra_db_application_token
            
            if not endpoint or not token:
                raise RuntimeError("Configurações do AstraDB não encontradas")
            
            # Criar cliente
            client = DataAPIClient()
            database = client.get_database(endpoint, token=token)
            
            logger.info(f"🔌 Conectado ao database: {database.info().name}")
            
            # Obter collection
            collection_name = self.config.rag.collection_name
            collection = database.get_collection(collection_name)
            
            logger.info(f"📚 Usando collection: {collection_name}")
            return collection
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com AstraDB: {e}")
            raise
    
    def prepare_documents_for_insertion(self, contents: List[PageContent]) -> List[Dict[str, Any]]:
        """Prepara documentos para inserção usando estrutura nativa"""
        documents = []
        
        for content in contents:
            if content.embedding:
                doc = {
                    "_id": content.id,
                    "page_num": content.page_num,
                    "file_path": content.image_path,
                    "doc_source": content.doc_source,
                    "markdown_text": content.markdown_text,
                    "$vector": content.embedding,
                    "token_count": content.token_count,
                    "processing_time": content.processing_time,
                    "indexed_at": datetime.utcnow().isoformat(),
                    "indexer_version": "2.0.0"
                }
                documents.append(doc)
        
        return documents

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES GLOBAIS
# ═══════════════════════════════════════════════════════════════════════════════

def create_doc_source_name(url: str) -> str:
    """Cria nome do documento a partir da URL (função global para compatibilidade)"""
    processor = NativeIndexingProcessor()
    return processor.create_doc_source_name(url)

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL REFATORADA
# ═══════════════════════════════════════════════════════════════════════════════

def process_pdf_from_url(url: str, doc_source: str = None) -> Tuple[bool, int, int, int]:
    """
    Função principal refatorada para processar PDF usando modelos nativos.
    
    Args:
        url: URL do PDF ou caminho local
        doc_source: Nome/identificador do documento
    
    Returns:
        Tuple[bool, int, int, int]: (sucesso, páginas_processadas, chunks_criados, imagens_extraídas)
    """
    processor = NativeIndexingProcessor()
    start_time = time.time()
    
    try:
        # Validações usando validador nativo
        if not IndexingValidator.validate_url(url):
            logger.error(f"❌ URL inválida: {url}")
            return False, 0, 0, 0
        
        env_valid, missing_vars = IndexingValidator.validate_environment()
        if not env_valid:
            logger.error(f"❌ Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
            return False, 0, 0, 0
        
        # Criar doc_source se não fornecido
        if not doc_source:
            doc_source = processor.create_doc_source_name(url)
        elif not IndexingValidator.validate_doc_source(doc_source):
            logger.error(f"❌ Nome de documento inválido: {doc_source}")
            return False, 0, 0, 0
        
        logger.info(f"🚀 Iniciando indexação refatorada v2.0.0: {doc_source}")
        logger.info(f"📄 PDF: {url}")
        
        # 1. Baixar/abrir PDF
        pdf = processor.download_pdf_with_retry(url)
        if not pdf:
            logger.error("❌ Não foi possível carregar o PDF")
            return False, 0, 0, 0
        
        # 2. Extrair conteúdo das páginas
        logger.info(f"📊 Extraindo conteúdo de {pdf.page_count} páginas...")
        contents = []
        pages_processed = pdf.page_count
        images_extracted = 0
        
        for i in tqdm(range(pdf.page_count), desc="Extraindo páginas"):
            content = processor.extract_page_content(pdf, i, doc_source)
            if content:
                contents.append(content)
                # Contar imagens se houver
                if hasattr(content, 'image_data') and content.image_data:
                    images_extracted += 1
        
        if not contents:
            logger.error("❌ Nenhum conteúdo extraído")
            return False, 0, 0, 0
        
        logger.info(f"✅ Extraídas {len(contents)} páginas")
        
        # 3. Gerar embeddings assíncronos
        logger.info(f"🧠 Gerando embeddings multimodais...")
        embedded_contents = asyncio.run(_generate_embeddings_native(processor, contents))
        
        if not embedded_contents:
            logger.error("❌ Nenhum embedding gerado")
            return False, 0, 0, 0
        
        logger.info(f"✅ Gerados {len(embedded_contents)} embeddings")
        
        # 4. Conectar ao AstraDB e inserir
        collection = processor.connect_to_astra()
        
        # Remover documentos antigos
        try:
            del_result = collection.delete_many({"doc_source": doc_source})
            if del_result.deleted_count > 0:
                logger.info(f"🗑️ Removidos {del_result.deleted_count} documentos antigos")
        except Exception as e:
            logger.warning(f"⚠️ Aviso ao remover documentos antigos: {e}")
        
        # Preparar e inserir documentos
        documents = processor.prepare_documents_for_insertion(embedded_contents)
        
        logger.info(f"💾 Inserindo {len(documents)} documentos...")
        inserted_count = 0
        batch_size = processor.config.processing.batch_size
        
        for i in tqdm(range(0, len(documents), batch_size), desc="Inserindo no AstraDB"):
            batch = documents[i:i+batch_size]
            try:
                result = collection.insert_many(batch)
                inserted_count += len(result.inserted_ids)
            except Exception as e:
                logger.warning(f"⚠️ Erro no lote {i//batch_size + 1}: {e}")
                # Inserção individual como fallback
                for doc in batch:
                    try:
                        collection.insert_one(doc)
                        inserted_count += 1
                    except Exception as individual_error:
                        logger.error(f"❌ Erro ao inserir {doc['_id']}: {individual_error}")
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Indexação refatorada concluída!")
        logger.info(f"📊 Documentos inseridos: {inserted_count}/{len(documents)}")
        logger.info(f"⏱️ Tempo de processamento: {processing_time:.2f}s")
        logger.info(f"🎯 Doc source: {doc_source}")
        
        chunks_created = len(embedded_contents)  # Cada conteúdo embedded é um chunk
        success = inserted_count > 0
        return success, pages_processed, chunks_created, images_extracted
        
    except Exception as e:
        logger.error(f"❌ Erro na indexação refatorada: {e}")
        return False, 0, 0, 0

async def _generate_embeddings_native(processor: NativeIndexingProcessor, contents: List[PageContent]) -> List[PageContent]:
    """Gera embeddings usando processador nativo"""
    try:
        processing_concurrency = processor.config.processing.processing_concurrency
        logger.info(f"🔄 Gerando embeddings com {processing_concurrency} workers...")
        
        semaphore = asyncio.Semaphore(processing_concurrency)
        async_client = voyageai.AsyncClient()
        
        try:
            tasks = [processor.generate_embedding(semaphore, async_client, content) for content in contents]
            results = await asyncio.gather(*tasks)
            
            # Filtrar apenas conteúdos com embeddings válidos
            embedded_contents = [content for content, success in zip(contents, results) if success]
            
            return embedded_contents
            
        finally:
            # Fechar conexão
            if hasattr(async_client, "aclose"):
                await async_client.aclose()
                
    except Exception as e:
        logger.error(f"❌ Erro ao gerar embeddings nativos: {e}")
        return []

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL COM RESULTADO NATIVO
# ═══════════════════════════════════════════════════════════════════════════════

def index_pdf_native(url: str, doc_source: str = None) -> IndexingResult:
    """
    Função de indexação que retorna resultado nativo para integração com APIs.
    
    Args:
        url: URL do PDF ou caminho local
        doc_source: Nome/identificador do documento
    
    Returns:
        IndexingResult: Resultado nativo da indexação
    """
    start_time = time.time()
    processor = NativeIndexingProcessor()
    
    if not doc_source:
        doc_source = processor.create_doc_source_name(url)
    
    try:
        success, pages_processed, chunks_created, images_extracted = process_pdf_from_url(url, doc_source)
        processing_time = time.time() - start_time
        
        if success:
            return IndexingResultFactory.create_success_result(
                doc_source=doc_source,
                pages_processed=pages_processed,
                chunks_created=chunks_created,
                images_extracted=images_extracted,
                processing_time=processing_time
            )
        else:
            return IndexingResultFactory.create_error_result(
                doc_source=doc_source,
                error="Falha no processamento do PDF",
                processing_time=processing_time
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        return IndexingResultFactory.create_error_result(
            doc_source=doc_source,
            error=str(e),
            processing_time=processing_time
        )

# ═══════════════════════════════════════════════════════════════════════════════
# CLI E EXECUÇÃO DIRETA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Função principal para execução via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Indexador Refatorado v2.0.0 - Sistema RAG Multi-Agente")
    parser.add_argument("url", help="URL ou caminho do PDF")
    parser.add_argument("--doc-source", help="Nome/identificador do documento")
    parser.add_argument("--native-result", action="store_true", help="Retornar resultado nativo detalhado")
    
    args = parser.parse_args()
    
    if args.native_result:
        # Usar função que retorna resultado nativo
        result = index_pdf_native(args.url, args.doc_source)
        
        print(f"\n📊 RESULTADO DA INDEXAÇÃO:")
        print(f"✅ Sucesso: {result.success}")
        print(f"📄 Doc Source: {result.doc_source}")
        print(f"📊 Páginas: {result.pages_processed}")
        print(f"🧩 Chunks: {result.chunks_created}")
        print(f"⏱️ Tempo: {result.processing_time:.2f}s")
        
        if result.error:
            print(f"❌ Erro: {result.error}")
        
        return result.success
    else:
        # Usar função tradicional
        success = process_pdf_from_url(args.url, args.doc_source)
        
        if success:
            logger.info("🎉 Indexação realizada com sucesso!")
            return True
        else:
            logger.error("💥 Falha na indexação!")
            return False

if __name__ == "__main__":
    exit(0 if main() else 1)