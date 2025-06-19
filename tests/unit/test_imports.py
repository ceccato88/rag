#!/usr/bin/env python3
"""
Teste simples para verificar se a aplicação FastAPI carrega
"""

try:
    print("1. Testando imports básicos...")
    from fastapi import FastAPI
    print("✅ FastAPI importado com sucesso")
    
    print("2. Testando config...")
    from src.apis.v2.core.config import src.core.config as config
    print("✅ Config importado com sucesso")
    
    print("3. Testando schemas...")
    from src.apis.v2.models.schemas import ResearchQuery, HealthResponse
    print("✅ Schemas importados com sucesso")
    
    print("4. Testando main...")
    from src.apis.v2.main import app
    print("✅ App principal importado com sucesso")
    
    print("✅ Todos os imports funcionaram!")
    
except Exception as e:
    print(f"❌ Erro no import: {e}")
    import traceback
    traceback.print_exc()
