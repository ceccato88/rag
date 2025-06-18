#!/usr/bin/env python3
"""
Script para deletar todos os documentos da collection do sistema RAG.

Este script permite:
1. Deletar todos os documentos da collection
2. Deletar documentos de um documento específico (por doc_source)
3. Confirmar antes de deletar (modo interativo)
4. Executar em modo silencioso (sem confirmação)

Uso:
    python delete_collection.py                    # Deleta tudo (interativo)
    python delete_collection.py --all --yes       # Deleta tudo (silencioso)
    python delete_collection.py --doc zep         # Deleta apenas documentos do "zep"
    python delete_collection.py --help            # Mostra ajuda
"""

import os
import sys
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv
from astrapy import DataAPIClient
from astrapy.exceptions import DataAPIException

# Importa utilitários
from utils.metrics import ProcessingMetrics, measure_time
from utils.resource_manager import ResourceManager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CollectionCleaner:
    """Classe para limpar documentos da collection"""
    
    def __init__(self):
        """Inicializa conexão com Astra DB"""
        load_dotenv()
        self._validate_environment()
        self._connect_to_database()
    
    def _validate_environment(self):
        """Valida se as variáveis de ambiente estão definidas"""
        required_vars = [
            "ASTRA_DB_API_ENDPOINT",
            "ASTRA_DB_APPLICATION_TOKEN"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"❌ Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
            sys.exit(1)
    
    def _connect_to_database(self):
        """Conecta ao Astra DB"""
        try:
            endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
            token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
            collection_name = os.getenv("COLLECTION_NAME", "pdf_documents")
            
            logger.info("🔌 Conectando ao Astra DB...")
            
            client = DataAPIClient(token)
            self.database = client.get_database(endpoint)
            self.collection = self.database.get_collection(collection_name)
            self.collection_name = collection_name
            
            # Testa a conexão
            self.collection.find({}, limit=1)
            logger.info(f"✅ Conectado à collection '{collection_name}'")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Astra DB: {e}")
            sys.exit(1)
    
    def count_documents(self, doc_source: Optional[str] = None) -> int:
        """Conta documentos na collection"""
        try:
            if doc_source:
                # Conta documentos de um doc_source específico
                filter_query = {"doc_source": doc_source}
                logger.info(f"📊 Contando documentos do source '{doc_source}'...")
            else:
                # Conta todos os documentos
                filter_query = {}
                logger.info("📊 Contando todos os documentos...")
            
            # Usar find com limit alto para contar
            docs = list(self.collection.find(filter_query, limit=10000))
            count = len(docs)
            
            if doc_source:
                logger.info(f"📄 Encontrados {count} documentos do source '{doc_source}'")
            else:
                logger.info(f"📄 Encontrados {count} documentos na collection")
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Erro ao contar documentos: {e}")
            return 0
    
    def list_document_sources(self) -> list:
        """Lista todos os doc_sources disponíveis"""
        try:
            logger.info("🔍 Buscando sources de documentos...")
            
            # Busca alguns documentos para ver os sources
            docs = list(self.collection.find({}, limit=1000, projection={"doc_source": True}))
            
            sources = list(set(doc.get("doc_source") for doc in docs if doc.get("doc_source")))
            sources.sort()
            
            if sources:
                logger.info(f"📚 Sources encontrados: {', '.join(sources)}")
            else:
                logger.info("📚 Nenhum source encontrado")
            
            return sources
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar sources: {e}")
            return []
    
    def delete_all_documents(self, confirm: bool = True) -> bool:
        """Deleta todos os documentos da collection"""
        try:
            count = self.count_documents()
            
            if count == 0:
                logger.info("✅ Collection já está vazia")
                return True
            
            if confirm:
                response = input(f"⚠️  Tem certeza que deseja deletar TODOS os {count} documentos? (sim/não): ")
                if response.lower() not in ['sim', 's', 'yes', 'y']:
                    logger.info("❌ Operação cancelada pelo usuário")
                    return False
            
            logger.info(f"🗑️  Deletando todos os {count} documentos...")
            
            # Deleta todos os documentos (filtro vazio)
            result = self.collection.delete_many({})
            
            deleted_count = result.deleted_count
            if deleted_count == -1:
                logger.info("✅ Todos os documentos foram deletados com sucesso")
            else:
                logger.info(f"✅ {deleted_count} documentos deletados com sucesso")
            
            return True
            
        except DataAPIException as e:
            logger.error(f"❌ Erro da API do Astra DB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao deletar documentos: {e}")
            return False
    
    def delete_documents_by_source(self, doc_source: str, confirm: bool = True) -> bool:
        """Deleta documentos de um doc_source específico"""
        try:
            count = self.count_documents(doc_source)
            
            if count == 0:
                logger.info(f"✅ Nenhum documento encontrado para o source '{doc_source}'")
                return True
            
            if confirm:
                response = input(f"⚠️  Tem certeza que deseja deletar {count} documentos do source '{doc_source}'? (sim/não): ")
                if response.lower() not in ['sim', 's', 'yes', 'y']:
                    logger.info("❌ Operação cancelada pelo usuário")
                    return False
            
            logger.info(f"🗑️  Deletando {count} documentos do source '{doc_source}'...")
            
            # Deleta documentos pelo doc_source
            result = self.collection.delete_many({"doc_source": doc_source})
            
            deleted_count = result.deleted_count
            logger.info(f"✅ {deleted_count} documentos deletados com sucesso")
            
            return True
            
        except DataAPIException as e:
            logger.error(f"❌ Erro da API do Astra DB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao deletar documentos: {e}")
            return False
    
    def count_documents_by_prefix(self, prefix: str) -> tuple[int, list]:
        """Conta documentos que começam com o prefixo especificado"""
        try:
            logger.info(f"📊 Buscando documentos com prefixo '{prefix}'...")
            
            # Busca todos os documentos e filtra por prefixo
            all_docs = list(self.collection.find({}, limit=10000, projection={"doc_source": True}))
            
            matching_sources = []
            matching_docs = []
            
            for doc in all_docs:
                doc_source = doc.get("doc_source", "")
                if doc_source.startswith(prefix):
                    matching_docs.append(doc)
                    if doc_source not in matching_sources:
                        matching_sources.append(doc_source)
            
            count = len(matching_docs)
            matching_sources.sort()
            
            if matching_sources:
                logger.info(f"📄 Encontrados {count} documentos de {len(matching_sources)} sources:")
                for source in matching_sources:
                    source_count = sum(1 for doc in matching_docs if doc.get("doc_source") == source)
                    logger.info(f"   • {source}: {source_count} documentos")
            else:
                logger.info(f"📄 Nenhum documento encontrado com prefixo '{prefix}'")
            
            return count, matching_sources
            
        except Exception as e:
            logger.error(f"❌ Erro ao contar documentos por prefixo: {e}")
            return 0, []
    
    def delete_documents_by_prefix(self, prefix: str, confirm: bool = True) -> bool:
        """Deleta documentos cujo doc_source começa com o prefixo especificado"""
        try:
            count, matching_sources = self.count_documents_by_prefix(prefix)
            
            if count == 0:
                logger.info(f"✅ Nenhum documento encontrado com prefixo '{prefix}'")
                return True
            
            if confirm:
                logger.info(f"📋 Sources que serão deletados:")
                for source in matching_sources:
                    logger.info(f"   • {source}")
                
                response = input(f"⚠️  Tem certeza que deseja deletar {count} documentos com prefixo '{prefix}'? (sim/não): ")
                if response.lower() not in ['sim', 's', 'yes', 'y']:
                    logger.info("❌ Operação cancelada pelo usuário")
                    return False
            
            logger.info(f"🗑️  Deletando {count} documentos com prefixo '{prefix}'...")
            
            # Busca todos os documentos e deleta os que correspondem ao prefixo
            deleted_total = 0
            for source in matching_sources:
                try:
                    result = self.collection.delete_many({"doc_source": source})
                    deleted_count = result.deleted_count
                    deleted_total += deleted_count
                    logger.info(f"   ✅ {source}: {deleted_count} documentos deletados")
                except Exception as e:
                    logger.error(f"   ❌ Erro ao deletar {source}: {e}")
            
            logger.info(f"✅ Total de {deleted_total} documentos deletados com prefixo '{prefix}'")
            
            return True
            
        except DataAPIException as e:
            logger.error(f"❌ Erro da API do Astra DB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao deletar documentos por prefixo: {e}")
            return False
    
    def interactive_delete_menu(self):
        """Menu interativo para escolher o que deletar"""
        try:
            while True:
                print("\n" + "=" * 60)
                print("🗑️  MENU DE DELEÇÃO INTERATIVO")
                print("=" * 60)
                
                # Mostra informações atuais
                total_count = self.count_documents()
                if total_count == 0:
                    print("✅ Collection está vazia!")
                    return True
                
                sources = self.list_document_sources()
                
                print(f"\n📊 Total de documentos: {total_count}")
                if sources:
                    print("📚 Sources disponíveis:")
                    for i, source in enumerate(sources, 1):
                        source_count = self.count_documents(source)
                        print(f"   {i}. {source} ({source_count} docs)")
                
                print("\n🎯 Opções de deleção:")
                print("   a) Deletar TODOS os documentos")
                print("   b) Deletar por source específico")
                print("   c) Deletar por prefixo")
                print("   d) Sair sem deletar")
                
                choice = input("\n👉 Escolha uma opção (a/b/c/d): ").lower().strip()
                
                if choice == 'a':
                    return self.delete_all_documents(confirm=True)
                
                elif choice == 'b':
                    if not sources:
                        print("❌ Nenhum source disponível")
                        continue
                    
                    print("\n📚 Sources disponíveis:")
                    for i, source in enumerate(sources, 1):
                        source_count = self.count_documents(source)
                        print(f"   {i}. {source} ({source_count} docs)")
                    
                    try:
                        source_choice = input("👉 Digite o número do source ou o nome exato: ").strip()
                        
                        # Tenta converter para número
                        if source_choice.isdigit():
                            source_idx = int(source_choice) - 1
                            if 0 <= source_idx < len(sources):
                                selected_source = sources[source_idx]
                            else:
                                print("❌ Número inválido")
                                continue
                        else:
                            # Usa o nome diretamente
                            selected_source = source_choice
                        
                        return self.delete_documents_by_source(selected_source, confirm=True)
                    
                    except (ValueError, IndexError):
                        print("❌ Entrada inválida")
                        continue
                
                elif choice == 'c':
                    prefix = input("👉 Digite o prefixo dos sources: ").strip()
                    if not prefix:
                        print("❌ Prefixo não pode estar vazio")
                        continue
                    
                    return self.delete_documents_by_prefix(prefix, confirm=True)
                
                elif choice == 'd':
                    print("👋 Saindo sem deletar")
                    return True
                
                else:
                    print("❌ Opção inválida. Use a, b, c ou d")
                    continue
        
        except KeyboardInterrupt:
            print("\n❌ Operação cancelada pelo usuário (Ctrl+C)")
            return False
        except Exception as e:
            logger.error(f"❌ Erro no menu interativo: {e}")
            return False
    
    def show_collection_info(self):
        """Mostra informações sobre a collection"""
        try:
            logger.info("=" * 60)
            logger.info(f"📋 INFORMAÇÕES DA COLLECTION '{self.collection_name}'")
            logger.info("=" * 60)
            
            # Conta total de documentos
            total_count = self.count_documents()
            logger.info(f"📊 Total de documentos: {total_count}")
            
            if total_count > 0:
                # Lista sources
                sources = self.list_document_sources()
                
                if sources:
                    logger.info("📚 Sources por documento:")
                    for source in sources:
                        source_count = self.count_documents(source)
                        logger.info(f"   • {source}: {source_count} documentos")
                
                # Mostra alguns exemplos de documentos
                logger.info("📄 Exemplos de documentos:")
                sample_docs = list(self.collection.find({}, limit=3, projection={
                    "doc_source": True, 
                    "page_num": True,
                    "_id": True
                }))
                
                for doc in sample_docs:
                    logger.info(f"   • ID: {doc.get('_id', 'N/A')}, Source: {doc.get('doc_source', 'N/A')}, Página: {doc.get('page_num', 'N/A')}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações da collection: {e}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Deleta documentos da collection do sistema RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python delete_collection.py                        # Menu interativo (recomendado)
  python delete_collection.py --all --yes           # Deleta tudo (silencioso)
  python delete_collection.py --doc zep             # Deleta apenas documentos do "zep"
  python delete_collection.py --prefix "meu_"       # Deleta documentos que começam com "meu_"
  python delete_collection.py --prefix zep --yes    # Deleta documentos com prefixo "zep" (silencioso)
  python delete_collection.py --info                # Apenas mostra informações
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Deleta todos os documentos da collection"
    )
    
    parser.add_argument(
        "--doc", 
        type=str, 
        help="Deleta apenas documentos de um doc_source específico"
    )
    
    parser.add_argument(
        "--prefix", 
        type=str, 
        help="Deleta documentos cujo doc_source começa com o prefixo especificado"
    )
    
    parser.add_argument(
        "--yes", 
        action="store_true", 
        help="Confirma automaticamente (não pede confirmação)"
    )
    
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Apenas mostra informações da collection (não deleta nada)"
    )
    
    args = parser.parse_args()
    
    try:
        # Inicializa o cleaner
        cleaner = CollectionCleaner()
        
        # Mostra informações da collection
        cleaner.show_collection_info()
        
        # Se é apenas para mostrar info, sai aqui
        if args.info:
            return
        
        # Executa a operação solicitada
        if args.doc:
            # Deleta documentos de um source específico
            success = cleaner.delete_documents_by_source(args.doc, confirm=not args.yes)
        elif args.prefix:
            # Deleta documentos por prefixo
            success = cleaner.delete_documents_by_prefix(args.prefix, confirm=not args.yes)
        elif args.all:
            # Deleta todos os documentos
            success = cleaner.delete_all_documents(confirm=not args.yes)
        else:
            # Comportamento padrão: menu interativo
            success = cleaner.interactive_delete_menu()
        
        if success:
            logger.info("🎉 Operação concluída com sucesso!")
        else:
            logger.error("❌ Operação falhou")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n❌ Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()