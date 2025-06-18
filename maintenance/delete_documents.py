#!/usr/bin/env python3
"""
Script para deletar documentos da pasta documents do sistema RAG.

Este script permite:
1. Deletar todos os documentos da pasta
2. Deletar documentos por extensão específica
3. Deletar documentos por prefixo personalizado
4. Confirmar antes de deletar (modo interativo)
5. Executar em modo silencioso (sem confirmação)

Uso:
    python delete_documents.py                       # Menu interativo (recomendado)
    python delete_documents.py --all --yes          # Deleta tudo (silencioso)
    python delete_documents.py --ext pdf            # Deleta apenas PDFs
    python delete_documents.py --prefix "meu_"      # Deleta documentos que começam com "meu_"
    python delete_documents.py --help               # Mostra ajuda
"""

import os
import sys
import glob
import argparse
import logging
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DocumentCleaner:
    """Classe para limpar documentos da pasta documents"""
    
    def __init__(self):
        """Inicializa o limpador de documentos"""
        load_dotenv()
        self.documents_dir = "documents"  # Pasta padrão de documentos
        self._validate_directory()
    
    def _validate_directory(self):
        """Valida se o diretório existe"""
        if not os.path.exists(self.documents_dir):
            logger.warning(f"📂 Diretório '{self.documents_dir}' não existe")
            self.documents_dir_exists = False
        else:
            logger.info(f"📂 Diretório de documentos: {os.path.abspath(self.documents_dir)}")
            self.documents_dir_exists = True
    
    def get_all_documents(self) -> List[str]:
        """Retorna lista de todos os documentos na pasta"""
        if not self.documents_dir_exists:
            return []
        
        # Busca por arquivos de documento comuns
        document_extensions = [
            '*.pdf', '*.doc', '*.docx', '*.txt', '*.md', '*.rtf',
            '*.odt', '*.pages', '*.tex', '*.epub', '*.mobi'
        ]
        all_documents = []
        
        for ext in document_extensions:
            pattern = os.path.join(self.documents_dir, ext)
            all_documents.extend(glob.glob(pattern))
        
        # Também busca arquivos sem extensão
        for item in os.listdir(self.documents_dir):
            item_path = os.path.join(self.documents_dir, item)
            if os.path.isfile(item_path) and '.' not in item:
                all_documents.append(item_path)
        
        return sorted(all_documents)
    
    def get_documents_by_extension(self) -> Dict[str, List[str]]:
        """Agrupa documentos por extensão"""
        documents = self.get_all_documents()
        by_extension = {}
        
        for doc_path in documents:
            filename = os.path.basename(doc_path)
            if '.' in filename:
                ext = filename.split('.')[-1].lower()
            else:
                ext = 'sem_extensao'
            
            if ext not in by_extension:
                by_extension[ext] = []
            by_extension[ext].append(doc_path)
        
        return by_extension
    
    def get_document_prefixes(self) -> List[str]:
        """Extrai os prefixos únicos dos nomes dos documentos"""
        documents = self.get_all_documents()
        prefixes = set()
        
        for doc_path in documents:
            filename = os.path.basename(doc_path)
            # Remove extensão
            name_without_ext = os.path.splitext(filename)[0]
            
            # Tenta extrair prefixos com base em separadores comuns
            separators = ['_', '-', ' ', '.']
            for sep in separators:
                if sep in name_without_ext:
                    prefix = name_without_ext.split(sep)[0]
                    if len(prefix) > 0:
                        prefixes.add(prefix)
            
            # Também adiciona o nome completo como prefixo potencial
            if len(name_without_ext) > 0:
                prefixes.add(name_without_ext)
        
        return sorted(list(prefixes))
    
    def count_documents(self, extension: str = None, prefix: str = None) -> int:
        """Conta documentos na pasta"""
        if not self.documents_dir_exists:
            return 0
        
        documents = self.get_all_documents()
        
        if extension is None and prefix is None:
            count = len(documents)
            logger.info(f"📊 Total de documentos: {count}")
        elif extension:
            filtered_docs = [doc for doc in documents 
                           if doc.lower().endswith(f'.{extension.lower()}')]
            count = len(filtered_docs)
            logger.info(f"📊 Documentos .{extension}: {count}")
        elif prefix:
            filtered_docs = [doc for doc in documents 
                           if os.path.basename(doc).startswith(prefix)]
            count = len(filtered_docs)
            logger.info(f"📊 Documentos com prefixo '{prefix}': {count}")
        
        return count
    
    def count_documents_by_prefix(self, prefix: str) -> Tuple[int, List[str]]:
        """Conta documentos que começam com o prefixo especificado"""
        if not self.documents_dir_exists:
            return 0, []
        
        logger.info(f"📊 Buscando documentos com prefixo '{prefix}'...")
        
        documents = self.get_all_documents()
        matching_documents = []
        
        for doc_path in documents:
            filename = os.path.basename(doc_path)
            if filename.startswith(prefix):
                matching_documents.append(doc_path)
        
        count = len(matching_documents)
        
        if matching_documents:
            logger.info(f"📄 Encontrados {count} documentos:")
            for doc in matching_documents:
                filename = os.path.basename(doc)
                size_kb = os.path.getsize(doc) / 1024
                logger.info(f"   • {filename} ({size_kb:.1f} KB)")
        else:
            logger.info(f"📄 Nenhum documento encontrado com prefixo '{prefix}'")
        
        return count, [os.path.basename(doc) for doc in matching_documents]
    
    def delete_all_documents(self, confirm: bool = True) -> bool:
        """Deleta todos os documentos da pasta"""
        if not self.documents_dir_exists:
            logger.info("✅ Diretório de documentos não existe")
            return True
        
        documents = self.get_all_documents()
        count = len(documents)
        
        if count == 0:
            logger.info("✅ Pasta de documentos já está vazia")
            return True
        
        if confirm:
            logger.info(f"📁 Pasta: {os.path.abspath(self.documents_dir)}")
            by_ext = self.get_documents_by_extension()
            logger.info("📋 Documentos por tipo:")
            for ext, docs in by_ext.items():
                logger.info(f"   • .{ext}: {len(docs)} arquivos")
            
            response = input(f"⚠️  Tem certeza que deseja deletar TODOS os {count} documentos? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                logger.info("❌ Operação cancelada pelo usuário")
                return False
        
        logger.info(f"🗑️  Deletando {count} documentos...")
        
        deleted_count = 0
        errors = 0
        
        for doc_path in documents:
            try:
                os.remove(doc_path)
                deleted_count += 1
                logger.debug(f"✅ Deletado: {os.path.basename(doc_path)}")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Erro ao deletar {os.path.basename(doc_path)}: {e}")
        
        if errors == 0:
            logger.info(f"✅ {deleted_count} documentos deletados com sucesso")
        else:
            logger.warning(f"⚠️  {deleted_count} documentos deletados, {errors} erros")
        
        return errors == 0
    
    def delete_documents_by_extension(self, extension: str, confirm: bool = True) -> bool:
        """Deleta documentos de uma extensão específica"""
        if not self.documents_dir_exists:
            logger.info("✅ Diretório de documentos não existe")
            return True
        
        documents = self.get_all_documents()
        matching_documents = [doc for doc in documents 
                            if doc.lower().endswith(f'.{extension.lower()}')]
        count = len(matching_documents)
        
        if count == 0:
            logger.info(f"✅ Nenhum documento .{extension} encontrado")
            return True
        
        if confirm:
            logger.info(f"📁 Pasta: {os.path.abspath(self.documents_dir)}")
            logger.info(f"📋 Documentos .{extension} que serão deletados:")
            for doc in matching_documents:
                filename = os.path.basename(doc)
                size_kb = os.path.getsize(doc) / 1024
                logger.info(f"   • {filename} ({size_kb:.1f} KB)")
            
            response = input(f"⚠️  Tem certeza que deseja deletar {count} documentos .{extension}? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                logger.info("❌ Operação cancelada pelo usuário")
                return False
        
        logger.info(f"🗑️  Deletando {count} documentos .{extension}...")
        
        deleted_count = 0
        errors = 0
        
        for doc_path in matching_documents:
            try:
                os.remove(doc_path)
                deleted_count += 1
                logger.debug(f"✅ Deletado: {os.path.basename(doc_path)}")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Erro ao deletar {os.path.basename(doc_path)}: {e}")
        
        if errors == 0:
            logger.info(f"✅ {deleted_count} documentos deletados com sucesso")
        else:
            logger.warning(f"⚠️  {deleted_count} documentos deletados, {errors} erros")
        
        return errors == 0
    
    def delete_documents_by_prefix(self, prefix: str, confirm: bool = True) -> bool:
        """Deleta documentos cujo nome começa com o prefixo especificado"""
        if not self.documents_dir_exists:
            logger.info("✅ Diretório de documentos não existe")
            return True
        
        count, _ = self.count_documents_by_prefix(prefix)
        
        if count == 0:
            logger.info(f"✅ Nenhum documento encontrado com prefixo '{prefix}'")
            return True
        
        documents = self.get_all_documents()
        matching_documents = [doc for doc in documents 
                            if os.path.basename(doc).startswith(prefix)]
        
        if confirm:
            logger.info(f"📁 Pasta: {os.path.abspath(self.documents_dir)}")
            response = input(f"⚠️  Tem certeza que deseja deletar {count} documentos com prefixo '{prefix}'? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                logger.info("❌ Operação cancelada pelo usuário")
                return False
        
        logger.info(f"🗑️  Deletando {count} documentos com prefixo '{prefix}'...")
        
        deleted_count = 0
        errors = 0
        
        for doc_path in matching_documents:
            try:
                os.remove(doc_path)
                deleted_count += 1
                logger.debug(f"✅ Deletado: {os.path.basename(doc_path)}")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Erro ao deletar {os.path.basename(doc_path)}: {e}")
        
        if errors == 0:
            logger.info(f"✅ {deleted_count} documentos deletados com sucesso")
        else:
            logger.warning(f"⚠️  {deleted_count} documentos deletados, {errors} erros")
        
        return errors == 0
    
    def interactive_delete_menu(self):
        """Menu interativo para escolher o que deletar"""
        try:
            while True:
                print("\n" + "=" * 60)
                print("🗑️  MENU DE DELEÇÃO DE DOCUMENTOS INTERATIVO")
                print("=" * 60)
                
                if not self.documents_dir_exists:
                    print(f"❌ Diretório '{self.documents_dir}' não existe!")
                    return True
                
                # Mostra informações atuais
                total_count = self.count_documents()
                if total_count == 0:
                    print("✅ Pasta de documentos está vazia!")
                    return True
                
                by_extension = self.get_documents_by_extension()
                prefixes = self.get_document_prefixes()
                
                print(f"\n📂 Pasta: {os.path.abspath(self.documents_dir)}")
                print(f"📊 Total de documentos: {total_count}")
                
                if by_extension:
                    print("📄 Documentos por tipo:")
                    for ext, docs in sorted(by_extension.items()):
                        total_size = sum(os.path.getsize(doc) for doc in docs) / 1024
                        print(f"   • .{ext}: {len(docs)} arquivos ({total_size:.1f} KB)")
                
                print("\n🎯 Opções de deleção:")
                print("   a) Deletar TODOS os documentos")
                print("   b) Deletar por extensão específica")
                print("   c) Deletar por prefixo")
                print("   d) Sair sem deletar")
                
                choice = input("\n👉 Escolha uma opção (a/b/c/d): ").lower().strip()
                
                if choice == 'a':
                    return self.delete_all_documents(confirm=True)
                
                elif choice == 'b':
                    if not by_extension:
                        print("❌ Nenhuma extensão disponível")
                        continue
                    
                    print("\n📄 Extensões disponíveis:")
                    extensions = list(sorted(by_extension.keys()))
                    for i, ext in enumerate(extensions, 1):
                        count = len(by_extension[ext])
                        print(f"   {i}. .{ext} ({count} arquivos)")
                    
                    try:
                        ext_choice = input("👉 Digite o número da extensão ou a extensão: ").strip()
                        
                        # Tenta converter para número
                        if ext_choice.isdigit():
                            ext_idx = int(ext_choice) - 1
                            if 0 <= ext_idx < len(extensions):
                                selected_ext = extensions[ext_idx]
                            else:
                                print("❌ Número inválido")
                                continue
                        else:
                            # Remove ponto se foi digitado
                            selected_ext = ext_choice.lstrip('.')
                        
                        return self.delete_documents_by_extension(selected_ext, confirm=True)
                    
                    except (ValueError, IndexError):
                        print("❌ Entrada inválida")
                        continue
                
                elif choice == 'c':
                    if prefixes:
                        print("\n📝 Prefixos sugeridos:")
                        for i, prefix in enumerate(prefixes[:10], 1):  # Mostra apenas os primeiros 10
                            count = self.count_documents(prefix=prefix)
                            if count > 0:
                                print(f"   {i}. {prefix} ({count} arquivos)")
                    
                    prefix = input("👉 Digite o prefixo dos arquivos: ").strip()
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
    
    def show_documents_info(self):
        """Mostra informações sobre os documentos"""
        try:
            logger.info("=" * 60)
            logger.info(f"📋 INFORMAÇÕES DA PASTA DE DOCUMENTOS")
            logger.info("=" * 60)
            
            if not self.documents_dir_exists:
                logger.info(f"❌ Diretório '{self.documents_dir}' não existe")
                return
            
            logger.info(f"📂 Pasta: {os.path.abspath(self.documents_dir)}")
            
            # Conta total de documentos
            total_count = self.count_documents()
            logger.info(f"📊 Total de documentos: {total_count}")
            
            if total_count > 0:
                # Lista por extensão
                by_extension = self.get_documents_by_extension()
                
                if by_extension:
                    logger.info("📄 Documentos por tipo:")
                    for ext, docs in sorted(by_extension.items()):
                        total_size = sum(os.path.getsize(doc) for doc in docs) / 1024
                        logger.info(f"   • .{ext}: {len(docs)} arquivos ({total_size:.1f} KB)")
                
                # Calcula tamanho total
                all_docs = self.get_all_documents()
                total_size_mb = sum(os.path.getsize(doc) for doc in all_docs) / (1024 * 1024)
                logger.info(f"💾 Tamanho total: {total_size_mb:.2f} MB")
                
                # Mostra alguns exemplos de documentos
                logger.info("📄 Exemplos de documentos:")
                sample_docs = all_docs[:5]
                
                for doc_path in sample_docs:
                    filename = os.path.basename(doc_path)
                    size_kb = os.path.getsize(doc_path) / 1024
                    logger.info(f"   • {filename} ({size_kb:.1f} KB)")
                
                if len(sample_docs) < total_count:
                    logger.info(f"   • ... e mais {total_count - len(sample_docs)} documentos")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações dos documentos: {e}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Deleta documentos da pasta documents do sistema RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python delete_documents.py                        # Menu interativo (recomendado)
  python delete_documents.py --all --yes           # Deleta tudo (silencioso)
  python delete_documents.py --ext pdf             # Deleta apenas PDFs
  python delete_documents.py --ext txt --yes       # Deleta TXTs (silencioso)
  python delete_documents.py --prefix "meu_"       # Deleta documentos que começam com "meu_"
  python delete_documents.py --prefix zep --yes    # Deleta documentos com prefixo "zep" (silencioso)
  python delete_documents.py --info                # Apenas mostra informações
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Deleta todos os documentos da pasta"
    )
    
    parser.add_argument(
        "--ext", 
        type=str, 
        help="Deleta apenas documentos de uma extensão específica (sem o ponto)"
    )
    
    parser.add_argument(
        "--prefix", 
        type=str, 
        help="Deleta documentos cujo nome começa com o prefixo especificado"
    )
    
    parser.add_argument(
        "--yes", 
        action="store_true", 
        help="Confirma automaticamente (não pede confirmação)"
    )
    
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Apenas mostra informações dos documentos (não deleta nada)"
    )
    
    args = parser.parse_args()
    
    try:
        # Inicializa o cleaner
        cleaner = DocumentCleaner()
        
        # Mostra informações dos documentos
        cleaner.show_documents_info()
        
        # Se é apenas para mostrar info, sai aqui
        if args.info:
            return
        
        # Executa a operação solicitada
        if args.ext:
            # Deleta documentos de uma extensão específica
            success = cleaner.delete_documents_by_extension(args.ext, confirm=not args.yes)
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