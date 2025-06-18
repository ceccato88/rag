#!/usr/bin/env python3
"""
🚀 INSTALADOR AUTOMÁTICO - Sistema RAG Multi-Agente
Instala automaticamente todas as dependências necessárias
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str = ""):
    """Executa comando e mostra resultado"""
    print(f"🔧 {description}")
    print(f"   Executando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"   ✅ Sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Erro: {e}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return False

def check_python_version():
    """Verifica versão do Python"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (compatível)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (mínimo: 3.11)")
        return False

def main():
    """Instalação principal"""
    
    print("🚀 INSTALADOR AUTOMÁTICO - SISTEMA RAG MULTI-AGENTE")
    print("="*60)
    
    # 1. Verificar Python
    print("\n1️⃣  VERIFICANDO PYTHON")
    if not check_python_version():
        print("💡 Instale Python 3.11+ antes de continuar")
        return False
    
    # 2. Verificar diretório
    print("\n2️⃣  VERIFICANDO DIRETÓRIO")
    if not Path("pyproject.toml").exists():
        print("❌ Execute este script na raiz do projeto (onde está o pyproject.toml)")
        return False
    print("✅ Diretório correto")
    
    # 3. Instalar dependências principais
    print("\n3️⃣  INSTALANDO DEPENDÊNCIAS PRINCIPAIS")
    commands = [
        ("pip install --upgrade pip", "Atualizando pip"),
        ("pip install -e .", "Instalando projeto em modo desenvolvimento"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Falha em: {description}")
            return False
    
    # 4. Instalar dependências opcionais
    print("\n4️⃣  INSTALANDO DEPENDÊNCIAS OPCIONAIS")
    
    optional_groups = {
        "api": "APIs de produção (FastAPI, WebSocket, etc.)",
        "dev": "Ferramentas de desenvolvimento (pytest, black, etc.)",
        "monitoring": "Observabilidade (OpenTelemetry, Prometheus, etc.)"
    }
    
    for group, description in optional_groups.items():
        print(f"\n   📦 {group.upper()}: {description}")
        response = input(f"   Instalar {group}? (s/N): ").lower().strip()
        
        if response in ['s', 'sim', 'y', 'yes']:
            if not run_command(f"pip install -e .[{group}]", f"Instalando grupo {group}"):
                print(f"⚠️  Falha ao instalar {group} (continuando...)")
    
    # 5. Verificar instalação
    print("\n5️⃣  VERIFICANDO INSTALAÇÃO")
    
    try:
        print("   🧪 Testando importações...")
        
        # Testar importações básicas
        import openai
        print("   ✅ OpenAI")
        
        import voyageai  
        print("   ✅ Voyage AI")
        
        import astrapy
        print("   ✅ Astra DB")
        
        from config import SystemConfig
        print("   ✅ Sistema de configuração")
        
        # Testar configuração
        config = SystemConfig()
        validation = config.validate_all()
        
        if validation["rag_valid"] and validation["multiagent_valid"]:
            print("   ✅ Configuração válida")
        else:
            print("   ⚠️  Configuração incompleta (configure .env)")
            
    except ImportError as e:
        print(f"   ❌ Erro na importação: {e}")
        return False
    
    # 6. Criar diretórios necessários
    print("\n6️⃣  CRIANDO DIRETÓRIOS")
    
    directories = ["logs", "temp", "pdf_images"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ {directory}")
    
    # 7. Verificar arquivo .env
    print("\n7️⃣  VERIFICANDO CONFIGURAÇÃO")
    
    if not Path(".env").exists():
        print("   ⚠️  Arquivo .env não encontrado")
        print("   💡 Copie .env.example para .env e configure suas chaves:")
        print("      cp .env.example .env")
        print("      # Edite .env com suas API keys")
    else:
        print("   ✅ Arquivo .env encontrado")
    
    # 8. Resumo final
    print("\n🎯 INSTALAÇÃO CONCLUÍDA!")
    print("="*60)
    
    print("\n✅ PRÓXIMOS PASSOS:")
    print("1. Configure suas API keys no arquivo .env")
    print("2. Execute o teste: python test_api_config.py")
    print("3. Inicie as APIs:")
    print("   • Sistema simples: python api_simple.py")
    print("   • Multi-agente: python api_multiagent.py")
    print("   • Docker: docker-compose up -d")
    
    print("\n📚 DOCUMENTAÇÃO:")
    print("• README.md - Documentação completa")
    print("• API_USAGE.md - Guia das APIs")
    print("• SETUP_FINAL.md - Resumo executivo")
    
    print("\n🔧 COMANDOS DISPONÍVEIS:")
    try:
        result = subprocess.run("pip show rag-multiagent-system", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("• rag-index - Indexar documentos")
            print("• rag-search - Buscar documentos")
            print("• rag-api-simple - API RAG simples")
            print("• rag-api-multiagent - API multi-agente")
    except:
        pass
    
    print(f"\n🎉 Sistema RAG Multi-Agente instalado com sucesso!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)