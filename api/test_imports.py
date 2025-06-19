#!/usr/bin/env python3
"""
Teste simples para verificar se a aplicação FastAPI carrega
"""

try:
    print("1. Testando imports básicos...")
    from fastapi import FastAPI
    print("✅ FastAPI importado com sucesso")
    
    print("2. Testando config...")
    from api.core.config import config
    print("✅ Config importado com sucesso")
    
    print("3. Testando schemas...")
    from api.models.schemas import ResearchQuery, HealthResponse
    print("✅ Schemas importados com sucesso")
    
    print("4. Testando main...")
    from api.main import app
    print("✅ App principal importado com sucesso")
    
    print("✅ Todos os imports funcionaram!")
    
except Exception as e:
    print(f"❌ Erro no import: {e}")
    import traceback
    traceback.print_exc()
