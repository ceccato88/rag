#!/usr/bin/env python3
"""
Diagnóstico simplificado do sistema RAG
"""

def main():
    print("🏥 DIAGNÓSTICO DO SISTEMA RAG")
    print("=" * 40)
    
    # Teste 1: Dependências básicas
    try:
        import os, sys
        from datetime import datetime
        print("✅ Bibliotecas padrão: OK")
    except Exception as e:
        print(f"❌ Bibliotecas padrão: {e}")
        return
    
    # Teste 2: Dependências externas
    dependencias = ["openai", "voyageai", "astrapy", "pymupdf", "pydantic"]
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✅ {dep}: Instalado")
        except ImportError:
            print(f"❌ {dep}: Não instalado")
    
    # Teste 3: Arquivos do projeto
    arquivos = ["config.py", "constants.py", "search.py", "indexer.py", ".env"]
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            print(f"✅ {arquivo}: Existe")
        else:
            print(f"❌ {arquivo}: Não encontrado")
    
    # Teste 4: Variáveis de ambiente
    env_vars = ["OPENAI_API_KEY", "VOYAGE_API_KEY", "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN"]
    for var in env_vars:
        valor = os.getenv(var)
        if valor:
            print(f"✅ {var}: Configurado")
        else:
            print(f"❌ {var}: Não configurado")
    
    # Teste 5: Configuração do sistema
    try:
        from config import SystemConfig
        config = SystemConfig()
        validation = config.validate_all()
        if validation['valid']:
            print("✅ Configuração do sistema: Válida")
        else:
            print("❌ Configuração do sistema: Problemas encontrados")
            for error in validation.get('errors', []):
                print(f"   • {error}")
    except Exception as e:
        print(f"❌ Configuração do sistema: Erro ao carregar ({e})")
    
    # Teste 6: Importação do RAG
    try:
        from search import SimpleRAG
        print("✅ Sistema RAG: Módulos carregados")
    except Exception as e:
        print(f"❌ Sistema RAG: Erro ao carregar ({e})")
    
    print(f"\n📋 Diagnóstico concluído em {datetime.now()}")

if __name__ == "__main__":
    main()
