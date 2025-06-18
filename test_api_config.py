#!/usr/bin/env python3
"""
🧪 TESTE DE CONFIGURAÇÃO DAS APIs
Verifica se todas as configurações estão corretas para execução das APIs
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def test_api_configuration():
    """Testa configuração das APIs"""
    print("🧪 TESTE DE CONFIGURAÇÃO DAS APIs")
    print("=" * 60)
    
    # 1. Carregar variáveis de ambiente
    print("\n📋 1. CARREGANDO CONFIGURAÇÕES")
    load_dotenv()
    
    # 2. Verificar variáveis obrigatórias
    print("\n🔑 2. VERIFICANDO VARIÁVEIS OBRIGATÓRIAS")
    required_vars = [
        "OPENAI_API_KEY",
        "VOYAGE_API_KEY", 
        "ASTRA_DB_API_ENDPOINT",
        "ASTRA_DB_APPLICATION_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: AUSENTE")
        elif value in ["your-key-here", "sk-...", "pa-...", "AstraCS:..."]:
            missing_vars.append(var)
            print(f"⚠️  {var}: VALOR PLACEHOLDER")
        else:
            print(f"✅ {var}: CONFIGURADO")
    
    if missing_vars:
        print(f"\n❌ Variáveis faltando: {', '.join(missing_vars)}")
        print("💡 Configure essas variáveis no arquivo .env")
        return False
    
    # 3. Testar importações do sistema
    print("\n📦 3. TESTANDO IMPORTAÇÕES DO SISTEMA")
    try:
        from config import SystemConfig
        print("✅ config.py importado")
        
        system_config = SystemConfig()
        print("✅ SystemConfig instanciado")
        
        validation = system_config.validate_all()
        if validation["rag_valid"] and validation["multiagent_valid"]:
            print("✅ Configuração válida")
        else:
            print("⚠️  Configuração parcialmente válida")
            print(f"   RAG: {'✅' if validation['rag_valid'] else '❌'}")
            print(f"   Multi-Agente: {'✅' if validation['multiagent_valid'] else '❌'}")
        
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return False
    
    # 4. Verificar configurações das APIs
    print("\n🔧 4. VERIFICANDO CONFIGURAÇÕES DAS APIs")
    
    api_configs = {
        "API_HOST": os.getenv("API_HOST", "0.0.0.0"),
        "API_PORT_SIMPLE": os.getenv("API_PORT_SIMPLE", "8000"),
        "API_PORT_MULTIAGENT": os.getenv("API_PORT_MULTIAGENT", "8001"),
        "API_LOG_LEVEL": os.getenv("API_LOG_LEVEL", "info"),
        "API_WORKERS": os.getenv("API_WORKERS", "1")
    }
    
    for key, value in api_configs.items():
        print(f"✅ {key}: {value}")
    
    # 5. Verificar dependências opcionais
    print("\n📦 5. VERIFICANDO DEPENDÊNCIAS OPCIONAIS")
    
    optional_packages = {
        "fastapi": "FastAPI framework",
        "uvicorn": "ASGI server", 
        "redis": "Cache Redis",
        "websockets": "WebSocket support"
    }
    
    for package, description in optional_packages.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"⚠️  {package}: {description} (não instalado)")
    
    # 6. Verificar diretórios
    print("\n📁 6. VERIFICANDO DIRETÓRIOS")
    
    directories = [
        os.getenv("LOG_DIR", "logs"),
        os.getenv("TEMP_DIR", "temp"),
        os.getenv("IMAGE_DIR", "pdf_images")
    ]
    
    for directory in directories:
        path = Path(directory)
        if path.exists():
            print(f"✅ {directory}: existe")
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ {directory}: criado")
            except Exception as e:
                print(f"❌ {directory}: erro ao criar - {e}")
    
    # 7. Testar conectividade básica
    print("\n🌐 7. TESTANDO CONECTIVIDADE BÁSICA")
    
    try:
        import requests
        # Teste básico de conectividade com timeout
        response = requests.get("https://api.openai.com", timeout=5)
        print("✅ Conectividade com OpenAI: OK")
    except Exception as e:
        print(f"⚠️  Conectividade com OpenAI: {e}")
    
    try:
        response = requests.get("https://api.voyageai.com", timeout=5)
        print("✅ Conectividade com Voyage AI: OK")
    except Exception as e:
        print(f"⚠️  Conectividade com Voyage AI: {e}")
    
    # 8. Resumo final
    print("\n🎯 8. RESUMO DA CONFIGURAÇÃO")
    print("=" * 60)
    
    if not missing_vars:
        print("✅ CONFIGURAÇÃO COMPLETA!")
        print("🚀 As APIs estão prontas para execução")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Instalar dependências: pip install -r requirements_api.txt")
        print("   2. Executar API Simples: python api_simple.py")
        print("   3. Executar API Multi-Agente: python api_multiagent.py")
        print("   4. Ou usar Docker: docker-compose up -d")
        return True
    else:
        print("⚠️  CONFIGURAÇÃO INCOMPLETA")
        print(f"❌ Configure estas variáveis: {', '.join(missing_vars)}")
        return False

def test_api_startup_simulation():
    """Simula inicialização das APIs"""
    print("\n🚀 SIMULAÇÃO DE INICIALIZAÇÃO DAS APIs")
    print("-" * 40)
    
    try:
        # Testar importações críticas
        from config import SystemConfig
        system_config = SystemConfig()
        
        print(f"✅ Modelo RAG: {system_config.rag.llm_model}")
        print(f"✅ Modelo Multi-Agente: {system_config.multiagent.model}")
        print(f"✅ Collection: {system_config.rag.collection_name}")
        print(f"✅ Max Candidatos: {system_config.rag.max_candidates}")
        print(f"✅ Timeout: {system_config.multiagent.subagent_timeout}s")
        
        print("\n🎯 APIs prontas para inicialização!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na simulação: {e}")
        return False

if __name__ == "__main__":
    success = test_api_configuration()
    
    if success:
        test_api_startup_simulation()
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        sys.exit(0)
    else:
        print("\n💥 TESTE FALHOU - CONFIGURE AS VARIÁVEIS AUSENTES")
        sys.exit(1)