#!/usr/bin/env python3
"""
Script para deletar imagens da pasta de PDFs do sistema RAG.

Este script permite:
1. Deletar todas as imagens da pasta
2. Deletar imagens de um documento específico (por prefixo)
3. Deletar imagens por prefixo personalizado
4. Confirmar antes de deletar (modo interativo)
5. Executar em modo silencioso (sem confirmação)

Uso:
    python delete_images.py                       # Menu interativo (recomendado)
    python delete_images.py --all --yes          # Deleta tudo (silencioso)
    python delete_images.py --doc zep            # Deleta apenas imagens do "zep"
    python delete_images.py --prefix "meu_"      # Deleta imagens que começam com "meu_"
    python delete_images.py --help               # Mostra ajuda
"""

import os
import sys
import glob
import argparse
import logging
from typing import List, Tuple
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ImageCleaner:
    """Classe para limpar imagens da pasta de PDFs"""
    
    def __init__(self):
        """Inicializa o limpador de imagens"""
        load_dotenv()
        self.image_dir = os.getenv("IMAGE_DIR", "pdf_images")
        self._validate_directory()
    
    def _validate_directory(self):
        """Valida se o diretório existe"""
        if not os.path.exists(self.image_dir):
            logger.warning(f"📂 Diretório '{self.image_dir}' não existe")
            self.image_dir_exists = False
        else:
            logger.info(f"📂 Diretório de imagens: {os.path.abspath(self.image_dir)}")
            self.image_dir_exists = True
    
    def get_all_images(self) -> List[str]:
        """Retorna lista de todas as imagens na pasta"""
        if not self.image_dir_exists:
            return []
        
        # Busca por arquivos de imagem comuns
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.tiff']
        all_images = []
        
        for ext in image_extensions:
            pattern = os.path.join(self.image_dir, ext)
            all_images.extend(glob.glob(pattern))
        
        return sorted(all_images)
    
    def get_image_sources(self) -> List[str]:
        """Extrai os prefixos únicos dos nomes das imagens"""
        images = self.get_all_images()
        sources = set()
        
        for img_path in images:
            filename = os.path.basename(img_path)
            # Remove extensão e tenta extrair o prefixo antes de "_page_"
            name_without_ext = os.path.splitext(filename)[0]
            
            if "_page_" in name_without_ext:
                prefix = name_without_ext.split("_page_")[0]
                sources.add(prefix)
            else:
                # Se não tem "_page_", usa o nome completo como source
                sources.add(name_without_ext)
        
        return sorted(list(sources))
    
    def count_images(self, prefix: str = None) -> int:
        """Conta imagens na pasta"""
        if not self.image_dir_exists:
            return 0
        
        images = self.get_all_images()
        
        if prefix is None:
            count = len(images)
            logger.info(f"📊 Total de imagens: {count}")
        else:
            filtered_images = [img for img in images 
                             if os.path.basename(img).startswith(prefix)]
            count = len(filtered_images)
            logger.info(f"📊 Imagens com prefixo '{prefix}': {count}")
        
        return count
    
    def count_images_by_prefix(self, prefix: str) -> Tuple[int, List[str]]:
        """Conta imagens que começam com o prefixo especificado"""
        if not self.image_dir_exists:
            return 0, []
        
        logger.info(f"📊 Buscando imagens com prefixo '{prefix}'...")
        
        images = self.get_all_images()
        matching_images = []
        matching_sources = set()
        
        for img_path in images:
            filename = os.path.basename(img_path)
            if filename.startswith(prefix):
                matching_images.append(img_path)
                # Extrai o source da imagem
                name_without_ext = os.path.splitext(filename)[0]
                if "_page_" in name_without_ext:
                    source = name_without_ext.split("_page_")[0]
                else:
                    source = name_without_ext
                matching_sources.add(source)
        
        count = len(matching_images)
        sources_list = sorted(list(matching_sources))
        
        if sources_list:
            logger.info(f"📄 Encontradas {count} imagens de {len(sources_list)} sources:")
            for source in sources_list:
                source_count = sum(1 for img in matching_images 
                                 if os.path.basename(img).startswith(source))
                logger.info(f"   • {source}: {source_count} imagens")
        else:
            logger.info(f"📄 Nenhuma imagem encontrada com prefixo '{prefix}'")
        
        return count, sources_list
    
    def delete_all_images(self, confirm: bool = True) -> bool:
        """Deleta todas as imagens da pasta"""
        if not self.image_dir_exists:
            logger.info("✅ Diretório de imagens não existe")
            return True
        
        images = self.get_all_images()
        count = len(images)
        
        if count == 0:
            logger.info("✅ Pasta de imagens já está vazia")
            return True
        
        if confirm:
            logger.info(f"📁 Pasta: {os.path.abspath(self.image_dir)}")
            response = input(f"⚠️  Tem certeza que deseja deletar TODAS as {count} imagens? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                logger.info("❌ Operação cancelada pelo usuário")
                return False
        
        logger.info(f"🗑️  Deletando {count} imagens...")
        
        deleted_count = 0
        errors = 0
        
        for img_path in images:
            try:
                os.remove(img_path)
                deleted_count += 1
                logger.debug(f"✅ Deletado: {os.path.basename(img_path)}")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Erro ao deletar {os.path.basename(img_path)}: {e}")
        
        if errors == 0:
            logger.info(f"✅ {deleted_count} imagens deletadas com sucesso")
        else:
            logger.warning(f"⚠️  {deleted_count} imagens deletadas, {errors} erros")
        
        return errors == 0
    
    def delete_images_by_source(self, source: str, confirm: bool = True) -> bool:
        """Deleta imagens de um source específico"""
        if not self.image_dir_exists:
            logger.info("✅ Diretório de imagens não existe")
            return True
        
        images = self.get_all_images()
        matching_images = [img for img in images 
                          if os.path.basename(img).startswith(source)]
        count = len(matching_images)
        
        if count == 0:
            logger.info(f"✅ Nenhuma imagem encontrada para o source '{source}'")
            return True
        
        if confirm:
            logger.info(f"📁 Pasta: {os.path.abspath(self.image_dir)}")
            logger.info(f"📋 Imagens que serão deletadas:")
            for img in matching_images[:5]:  # Mostra apenas os primeiros 5
                logger.info(f"   • {os.path.basename(img)}")
            if count > 5:
                logger.info(f"   • ... e mais {count - 5} imagens")
            
            response = input(f"⚠️  Tem certeza que deseja deletar {count} imagens do source '{source}'? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                logger.info("❌ Operação cancelada pelo usuário")
                return False
        
        logger.info(f"🗑️  Deletando {count} imagens do source '{source}'...")
        
        deleted_count = 0
        errors = 0
        
        for img_path in matching_images:
            try:
                os.remove(img_path)
                deleted_count += 1
                logger.debug(f"✅ Deletado: {os.path.basename(img_path)}")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Erro ao deletar {os.path.basename(img_path)}: {e}")
        
        if errors == 0:
            logger.info(f"✅ {deleted_count} imagens deletadas com sucesso")
        else:
            logger.warning(f"⚠️  {deleted_count} imagens deletadas, {errors} erros")
        
        return errors == 0
    
    def delete_images_by_prefix(self, prefix: str, confirm: bool = True) -> bool:
        """Deleta imagens cujo nome começa com o prefixo especificado"""
        if not self.image_dir_exists:
            logger.info("✅ Diretório de imagens não existe")
            return True
        
        count, matching_sources = self.count_images_by_prefix(prefix)
        
        if count == 0:
            logger.info(f"✅ Nenhuma imagem encontrada com prefixo '{prefix}'")
            return True
        
        images = self.get_all_images()
        matching_images = [img for img in images 
                          if os.path.basename(img).startswith(prefix)]
        
        if confirm:
            logger.info(f"📁 Pasta: {os.path.abspath(self.image_dir)}")
            logger.info(f"📋 Sources que serão deletados:")
            for source in matching_sources:
                logger.info(f"   • {source}")
            
            logger.info(f"📋 Exemplos de imagens:")
            for img in matching_images[:3]:  # Mostra apenas os primeiros 3
                logger.info(f"   • {os.path.basename(img)}")
            if count > 3:
                logger.info(f"   • ... e mais {count - 3} imagens")
            
            response = input(f"⚠️  Tem certeza que deseja deletar {count} imagens com prefixo '{prefix}'? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                logger.info("❌ Operação cancelada pelo usuário")
                return False
        
        logger.info(f"🗑️  Deletando {count} imagens com prefixo '{prefix}'...")
        
        deleted_count = 0
        errors = 0
        
        for img_path in matching_images:
            try:
                os.remove(img_path)
                deleted_count += 1
                logger.debug(f"✅ Deletado: {os.path.basename(img_path)}")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Erro ao deletar {os.path.basename(img_path)}: {e}")
        
        if errors == 0:
            logger.info(f"✅ {deleted_count} imagens deletadas com sucesso")
        else:
            logger.warning(f"⚠️  {deleted_count} imagens deletadas, {errors} erros")
        
        return errors == 0
    
    def interactive_delete_menu(self):
        """Menu interativo para escolher o que deletar"""
        try:
            while True:
                print("\n" + "=" * 60)
                print("🗑️  MENU DE DELEÇÃO DE IMAGENS INTERATIVO")
                print("=" * 60)
                
                if not self.image_dir_exists:
                    print(f"❌ Diretório '{self.image_dir}' não existe!")
                    return True
                
                # Mostra informações atuais
                total_count = self.count_images()
                if total_count == 0:
                    print("✅ Pasta de imagens está vazia!")
                    return True
                
                sources = self.get_image_sources()
                
                print(f"\n📂 Pasta: {os.path.abspath(self.image_dir)}")
                print(f"📊 Total de imagens: {total_count}")
                
                if sources:
                    print("📚 Sources disponíveis:")
                    for i, source in enumerate(sources, 1):
                        source_count = self.count_images(source)
                        print(f"   {i}. {source} ({source_count} imagens)")
                
                print("\n🎯 Opções de deleção:")
                print("   a) Deletar TODAS as imagens")
                print("   b) Deletar por source específico")
                print("   c) Deletar por prefixo")
                print("   d) Sair sem deletar")
                
                choice = input("\n👉 Escolha uma opção (a/b/c/d): ").lower().strip()
                
                if choice == 'a':
                    return self.delete_all_images(confirm=True)
                
                elif choice == 'b':
                    if not sources:
                        print("❌ Nenhum source disponível")
                        continue
                    
                    print("\n📚 Sources disponíveis:")
                    for i, source in enumerate(sources, 1):
                        source_count = self.count_images(source)
                        print(f"   {i}. {source} ({source_count} imagens)")
                    
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
                        
                        return self.delete_images_by_source(selected_source, confirm=True)
                    
                    except (ValueError, IndexError):
                        print("❌ Entrada inválida")
                        continue
                
                elif choice == 'c':
                    prefix = input("👉 Digite o prefixo dos arquivos: ").strip()
                    if not prefix:
                        print("❌ Prefixo não pode estar vazio")
                        continue
                    
                    return self.delete_images_by_prefix(prefix, confirm=True)
                
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
    
    def show_images_info(self):
        """Mostra informações sobre as imagens"""
        try:
            logger.info("=" * 60)
            logger.info(f"📋 INFORMAÇÕES DA PASTA DE IMAGENS")
            logger.info("=" * 60)
            
            if not self.image_dir_exists:
                logger.info(f"❌ Diretório '{self.image_dir}' não existe")
                return
            
            logger.info(f"📂 Pasta: {os.path.abspath(self.image_dir)}")
            
            # Conta total de imagens
            total_count = self.count_images()
            logger.info(f"📊 Total de imagens: {total_count}")
            
            if total_count > 0:
                # Lista sources
                sources = self.get_image_sources()
                
                if sources:
                    logger.info("📚 Sources por imagens:")
                    for source in sources:
                        source_count = self.count_images(source)
                        logger.info(f"   • {source}: {source_count} imagens")
                
                # Mostra alguns exemplos de imagens
                logger.info("📄 Exemplos de imagens:")
                sample_images = self.get_all_images()[:5]
                
                for img_path in sample_images:
                    filename = os.path.basename(img_path)
                    size_kb = os.path.getsize(img_path) / 1024
                    logger.info(f"   • {filename} ({size_kb:.1f} KB)")
                
                if len(sample_images) < total_count:
                    logger.info(f"   • ... e mais {total_count - len(sample_images)} imagens")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações das imagens: {e}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Deleta imagens da pasta de PDFs do sistema RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python delete_images.py                        # Menu interativo (recomendado)
  python delete_images.py --all --yes           # Deleta tudo (silencioso)
  python delete_images.py --doc zep             # Deleta apenas imagens do "zep"
  python delete_images.py --prefix "meu_"       # Deleta imagens que começam com "meu_"
  python delete_images.py --prefix zep --yes    # Deleta imagens com prefixo "zep" (silencioso)
  python delete_images.py --info                # Apenas mostra informações
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Deleta todas as imagens da pasta"
    )
    
    parser.add_argument(
        "--doc", 
        type=str, 
        help="Deleta apenas imagens de um source específico"
    )
    
    parser.add_argument(
        "--prefix", 
        type=str, 
        help="Deleta imagens cujo nome começa com o prefixo especificado"
    )
    
    parser.add_argument(
        "--yes", 
        action="store_true", 
        help="Confirma automaticamente (não pede confirmação)"
    )
    
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Apenas mostra informações das imagens (não deleta nada)"
    )
    
    args = parser.parse_args()
    
    try:
        # Inicializa o cleaner
        cleaner = ImageCleaner()
        
        # Mostra informações das imagens
        cleaner.show_images_info()
        
        # Se é apenas para mostrar info, sai aqui
        if args.info:
            return
        
        # Executa a operação solicitada
        if args.doc:
            # Deleta imagens de um source específico
            success = cleaner.delete_images_by_source(args.doc, confirm=not args.yes)
        elif args.prefix:
            # Deleta imagens por prefixo
            success = cleaner.delete_images_by_prefix(args.prefix, confirm=not args.yes)
        elif args.all:
            # Deleta todas as imagens
            success = cleaner.delete_all_images(confirm=not args.yes)
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