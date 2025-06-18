#!/usr/bin/env python3
"""
Script simplificado para deletar imagens extraídas dos PDFs.

Uso:
    python delete_images.py --all                    # Deleta TODAS as imagens
    python delete_images.py --doc "arxiv_2024"       # Deleta imagens com esse prefixo
"""

import os
import sys
import argparse
import logging
import glob
from pathlib import Path

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from config import SystemConfig

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_images(all_images: bool = False, doc_prefix: str = None) -> dict:
    """
    Delete imagens extraídas dos PDFs.
    
    Args:
        all_images: Se True, deleta TODAS as imagens
        doc_prefix: Se fornecido, deleta apenas imagens que começam com esse prefixo
    
    Returns:
        Dict com resultado da operação
    """
    try:
        # Carregar configuração
        load_dotenv()
        
        # Diretório de imagens (padrão: pdf_images)
        images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pdf_images")
        
        if not os.path.exists(images_dir):
            return {"success": True, "deleted": 0, "message": "Diretório de imagens não existe"}
        
        # Determinar padrão de arquivos
        if all_images:
            pattern = os.path.join(images_dir, "*")
            logger.info(f"🗑️ Deletando TODAS as imagens de: {images_dir}")
        elif doc_prefix:
            pattern = os.path.join(images_dir, f"{doc_prefix}*")
            logger.info(f"🗑️ Deletando imagens com prefixo: {doc_prefix}")
        else:
            raise ValueError("Especifique --all ou --doc <prefixo>")
        
        # Encontrar arquivos
        files_to_delete = glob.glob(pattern)
        
        # Filtrar apenas arquivos (não diretórios)
        files_to_delete = [f for f in files_to_delete if os.path.isfile(f)]
        
        logger.info(f"📊 Encontrados {len(files_to_delete)} arquivos para deletar")
        
        if len(files_to_delete) == 0:
            return {"success": True, "deleted": 0, "message": "Nenhum arquivo encontrado"}
        
        # Mostrar lista de arquivos (primeiros 10)
        logger.info("📋 Arquivos que serão deletados:")
        for i, file_path in enumerate(files_to_delete[:10]):
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            logger.info(f"   {i+1}. {filename} ({file_size} bytes)")
        
        if len(files_to_delete) > 10:
            logger.info(f"   ... e mais {len(files_to_delete) - 10} arquivos")
        
        # Deletar arquivos
        deleted_count = 0
        deleted_files = []
        
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_count += 1
                deleted_files.append(os.path.basename(file_path))
                logger.debug(f"Deletado: {file_path}")
            except Exception as e:
                logger.warning(f"Erro ao deletar {file_path}: {e}")
        
        logger.info(f"✅ Deletados {deleted_count} arquivos com sucesso")
        
        return {
            "success": True,
            "deleted": deleted_count,
            "files": deleted_files,
            "message": f"Deletados {deleted_count} arquivos de imagem"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar imagens: {e}")
        return {"success": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Deletar imagens extraídas dos PDFs")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Deletar TODAS as imagens")
    group.add_argument("--doc", type=str, help="Prefixo do documento para deletar imagens")
    
    args = parser.parse_args()
    
    # Confirmação de segurança
    if args.all:
        confirm = input("⚠️ ATENÇÃO: Isso vai deletar TODAS as imagens! Digite 'CONFIRMO' para continuar: ")
        if confirm != "CONFIRMO":
            print("❌ Operação cancelada")
            sys.exit(1)
    elif args.doc:
        confirm = input(f"⚠️ Deletar imagens com prefixo '{args.doc}'? Digite 'sim' para continuar: ")
        if confirm.lower() != "sim":
            print("❌ Operação cancelada")
            sys.exit(1)
    
    # Executar deleção
    result = delete_images(all_images=args.all, doc_prefix=args.doc)
    
    if result["success"]:
        print(f"✅ {result['message']}")
        if "files" in result and len(result["files"]) <= 10:
            print("📋 Arquivos deletados:")
            for file in result["files"]:
                print(f"   • {file}")
    else:
        print(f"❌ Erro: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()