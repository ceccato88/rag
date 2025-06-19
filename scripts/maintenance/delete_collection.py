#!/usr/bin/env python3
"""
Script simplificado para deletar documentos da collection AstraDB.

Uso:
    python delete_collection.py --all                    # Deleta TODOS os documentos
    python delete_collection.py --doc "arxiv_2024"       # Deleta apenas documentos com esse prefixo
"""

import os
import sys
import argparse
import logging
from typing import Optional

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from astrapy import DataAPIClient
from src.core.config import SystemConfig

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_documents(all_docs: bool = False, doc_prefix: str = None) -> dict:
    """
    Delete documentos da collection.
    
    Args:
        all_docs: Se True, deleta TODOS os documentos
        doc_prefix: Se fornecido, deleta apenas docs que começam com esse prefixo
    
    Returns:
        Dict com resultado da operação
    """
    try:
        # Carregar configuração
        load_dotenv()
        config = SystemConfig()
        
        # Validar configuração
        validation = config.validate_all()
        if not validation["rag_valid"]:
            raise Exception("Configuração AstraDB inválida")
        
        # Conectar ao AstraDB
        client = DataAPIClient(token=config.rag.astra_db_application_token)
        database = client.get_database(config.rag.astra_db_api_endpoint)
        collection = database.get_collection(config.rag.collection_name)
        
        # Determinar filtro
        if all_docs:
            filter_query = {}
            logger.info("🗑️ Deletando TODOS os documentos da collection")
        elif doc_prefix:
            filter_query = {"doc_source": {"$regex": f"^{doc_prefix}"}}
            logger.info(f"🗑️ Deletando documentos com prefixo: {doc_prefix}")
        else:
            raise ValueError("Especifique --all ou --doc <prefixo>")
        
        # Contar documentos antes
        count_before = collection.count_documents(filter_query, upper_bound=10000)
        logger.info(f"📊 Encontrados {count_before} documentos para deletar")
        
        if count_before == 0:
            return {"success": True, "deleted": 0, "message": "Nenhum documento encontrado"}
        
        # Deletar documentos
        result = collection.delete_many(filter_query)
        deleted_count = result.deleted_count
        
        # AstraDB pode retornar -1 quando deleta todos os documentos
        if deleted_count == -1:
            deleted_count = count_before
        
        logger.info(f"✅ Deletados {deleted_count} documentos com sucesso")
        
        return {
            "success": True,
            "deleted": deleted_count,
            "message": f"Deletados {deleted_count} documentos"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar documentos: {e}")
        return {"success": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Deletar documentos da collection AstraDB")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Deletar TODOS os documentos")
    group.add_argument("--doc", type=str, help="Prefixo do documento para deletar")
    
    args = parser.parse_args()
    
    # Confirmação de segurança
    if args.all:
        confirm = input("⚠️ ATENÇÃO: Isso vai deletar TODOS os documentos! Digite 'CONFIRMO' para continuar: ")
        if confirm != "CONFIRMO":
            print("❌ Operação cancelada")
            sys.exit(1)
    elif args.doc:
        confirm = input(f"⚠️ Deletar documentos com prefixo '{args.doc}'? Digite 'sim' para continuar: ")
        if confirm.lower() != "sim":
            print("❌ Operação cancelada")
            sys.exit(1)
    
    # Executar deleção
    result = delete_documents(all_docs=args.all, doc_prefix=args.doc)
    
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ Erro: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()