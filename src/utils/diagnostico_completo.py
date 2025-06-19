#!/usr/bin/env python3
"""
Script de diagnóstico completo do sistema RAG conforme README
"""

import os
import sys
from datetime import datetime

def verificar_ambiente():
    """Verifica configuração do ambiente"""
    
    print("🔍 DIAGNÓSTICO DO AMBIENTE")
    print("=" * 40)
    
    # Python version
    print(f"🐍 Python: {sys.version}")
    
    # Variáveis de ambiente
    vars_necessarias = [
        "OPENAI_API_KEY",
        "VOYAGE_API_KEY", 
        "ASTRA_DB_API_ENDPOINT",
        "ASTRA_DB_APPLICATION_TOKEN"
    ]
    
    for var in vars_necessarias:
        valor = os.getenv(var)
        status = "✅" if valor else "❌"
        valor_exibido = valor[:10] + "..." if valor else "Não definida"
        print(f"{status} {var}: {valor_exibido}")

def verificar_dependencias():
    """Verifica dependências instaladas"""
    
    print("\n📦 DEPENDÊNCIAS")
    print("=" * 40)
    
    dependencias = [
        "openai", "voyageai", "astrapy", "pymupdf", "pydantic", "pillow",
        "python-dotenv", "requests", "tqdm"
    ]
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✅ {dep}: Instalado")
        except ImportError:
            print(f"❌ {dep}: Não instalado")

def verificar_arquivos():
    """Verifica se arquivos principais existem"""
    
    print("\n📁 ARQUIVOS PRINCIPAIS")
    print("=" * 40)
    
    arquivos_essenciais = [
        "config.py",
        "constants.py", 
        "search.py",
        "indexer.py",
        ".env",
        "requirements.txt"
    ]
    
    for arquivo in arquivos_essenciais:
        existe = os.path.exists(arquivo)
        status = "✅" if existe else "❌"
        print(f"{status} {arquivo}")

def testar_configuracao():
    """Testa se a configuração está funcionando"""
    
    print("\n⚙️ TESTE DE CONFIGURAÇÃO")
    print("=" * 40)
    
    try:
        from config import SystemConfig
        config = SystemConfig()
        validation = config.validate_all()
        
        if validation['valid']:
            print("✅ Configuração válida")
        else:
            print("❌ Problemas na configuração:")
            for error in validation['errors']:
                print(f"  • {error}")
        
        if validation['warnings']:
            print("⚠️  Avisos:")
            for warning in validation['warnings']:
                print(f"  • {warning}")
        
    except Exception as e:
        print(f"❌ Erro ao testar configuração: {e}")

def testar_rag_basico():
    """Testa funcionalidade básica do RAG"""
    
    print("\n🔍 TESTE RAG BÁSICO")
    print("=" * 40)
    
    try:
        from search import SimpleRAG
        rag = SimpleRAG()
        print("✅ Sistema RAG inicializado")
        
        # Teste sem fazer chamadas caras de API
        print("✅ Classes RAG carregadas corretamente")
        
    except Exception as e:
        print(f"❌ Erro no teste RAG: {e}")

def testar_multiagente():
    """Testa sistema multi-agente"""
    
    print("\n🤖 TESTE MULTI-AGENTE")
    print("=" * 40)
    
    try:
        sys.path.append('multi-agent-researcher/src')
        from researcher.agents.openai_lead_researcher import OpenAILeadResearcher
        print("✅ OpenAILeadResearcher importado")
        
        # Não inicializa para evitar custos de API
        print("✅ Classes multi-agente carregadas corretamente")
        
    except Exception as e:
        print(f"❌ Erro no teste multi-agente: {e}")

def main():
    """Executa diagnóstico completo"""
    
    print("🏥 DIAGNÓSTICO COMPLETO DO SISTEMA RAG")
    print("=" * 60)
    
    verificar_ambiente()
    verificar_dependencias()
    verificar_arquivos()
    testar_configuracao()
    testar_rag_basico()
    testar_multiagente()
    
    print(f"\n📋 RELATÓRIO GERADO EM: {datetime.now()}")
    print("=" * 60)
    print("💡 Se houver problemas:")
    print("1. Verifique se todas as dependências estão instaladas")
    print("2. Configure corretamente o arquivo .env")
    print("3. Teste conexões com as APIs")

if __name__ == "__main__":
    main()
