#!/usr/bin/env python3
"""
Script para verificar documentos indexados no AstraDB
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from astrapy import DataAPIClient
from src.core.config import SystemConfig

def check_documents():
    """Verifica quantos documentos estão indexados"""
    try:
        # Carregar configuração
        load_dotenv()
        config = SystemConfig()
        
        # Validar configuração
        validation = config.validate_all()
        if not validation["rag_valid"]:
            print("❌ Configuração AstraDB inválida")
            return
        
        # Conectar ao AstraDB
        client = DataAPIClient(token=config.rag.astra_db_application_token)
        database = client.get_database(config.rag.astra_db_api_endpoint)
        collection = database.get_collection(config.rag.collection_name)
        
        print(f"🔍 Verificando collection: {config.rag.collection_name}")
        
        # Contar todos os documentos
        total_count = collection.count_documents({}, upper_bound=10000)
        print(f"📊 Total de documentos: {total_count}")
        
        if total_count > 0:
            # Verificar documentos por source
            # Buscar alguns documentos para ver a estrutura
            sample_docs = list(collection.find({}, limit=5, projection={"doc_source": 1, "page_num": 1, "_id": 1}))
            
            print(f"\n📋 Documentos encontrados (amostra):")
            doc_sources = set()
            for doc in sample_docs:
                doc_source = doc.get("doc_source", "unknown")
                page_num = doc.get("page_num", "?")
                doc_id = doc.get("_id", "no-id")
                print(f"  - {doc_id} (source: {doc_source}, page: {page_num})")
                doc_sources.add(doc_source)
            
            print(f"\n📚 Fontes únicas encontradas: {len(doc_sources)}")
            for source in sorted(doc_sources):
                source_count = collection.count_documents({"doc_source": source}, upper_bound=1000)
                print(f"  - {source}: {source_count} documentos")
        else:
            print("⚠️ Nenhum documento encontrado na collection")
            
    except Exception as e:
        print(f"❌ Erro ao verificar documentos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_documents()