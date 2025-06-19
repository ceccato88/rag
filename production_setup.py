#!/usr/bin/env python3
"""
Script de inicialização para ambiente de produção
Valida configurações e aplica otimizações antes de iniciar a API
"""

import os
import sys
import logging
from typing import Dict, Any

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SystemConfig
from constants import validate_production_config, get_production_config
from utils.logging_config import setup_production_logging


def validate_environment() -> Dict[str, Any]:
    """Valida ambiente de produção"""
    print("🔍 VALIDANDO AMBIENTE DE PRODUÇÃO")
    print("=" * 50)
    
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config_valid": False
    }
    
    # Verificar variáveis de ambiente críticas
    required_vars = [
        "OPENAI_API_KEY",
        "VOYAGE_API_KEY", 
        "ASTRA_DB_API_ENDPOINT",
        "ASTRA_DB_APPLICATION_TOKEN"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            validation_result["errors"].append(f"Variável de ambiente {var} não definida")
            validation_result["valid"] = False
        else:
            print(f"✅ {var}: Definida")
    
    # Validar configurações do sistema
    try:
        config = SystemConfig()
        config_validation = config.validate_all()
        
        if config_validation["valid"]:
            print("✅ Configurações do sistema válidas")
            validation_result["config_valid"] = True
        else:
            print("❌ Problemas nas configurações:")
            for error in config_validation["errors"]:
                print(f"  • {error}")
                validation_result["errors"].append(error)
            validation_result["valid"] = False
        
        if config_validation["warnings"]:
            print("⚠️  Avisos de configuração:")
            for warning in config_validation["warnings"]:
                print(f"  • {warning}")
                validation_result["warnings"].append(warning)
        
        # Validações específicas de produção
        prod_warnings = validate_production_config()
        if prod_warnings:
            print("⚠️  Avisos específicos de produção:")
            for warning in prod_warnings:
                print(f"  • {warning}")
                validation_result["warnings"].extend(prod_warnings)
        
    except Exception as e:
        error_msg = f"Erro na validação do sistema: {e}"
        print(f"❌ {error_msg}")
        validation_result["errors"].append(error_msg)
        validation_result["valid"] = False
    
    return validation_result


def setup_production_environment():
    """Configura ambiente de produção"""
    print("\n🚀 CONFIGURANDO AMBIENTE DE PRODUÇÃO")
    print("=" * 50)
    
    # Configurar logging
    try:
        log_config = setup_production_logging()
        if log_config["configured"]:
            print("✅ Logging de produção configurado")
        else:
            print(f"❌ Erro no logging: {log_config.get('error', 'Desconhecido')}")
    except Exception as e:
        print(f"❌ Erro ao configurar logging: {e}")
    
    # Definir variáveis de ambiente para produção se não estiverem definidas
    prod_env_vars = {
        "PRODUCTION_MODE": "true",
        "DEBUG_MODE": "false", 
        "VERBOSE_LOGGING": "false",
        "ENABLE_PERFORMANCE_METRICS": "true",
        "LOG_LEVEL": "INFO",
        "ENABLE_RATE_LIMITING": "true",
        "MONITORING_ENABLED": "true"
    }
    
    for var, value in prod_env_vars.items():
        if not os.getenv(var):
            os.environ[var] = value
            print(f"✅ {var} definido como {value}")
    
    # Configurações específicas de produção
    prod_config = get_production_config()
    print(f"✅ Configurações de produção carregadas: {len(prod_config)} itens")


def print_production_summary():
    """Imprime resumo das configurações de produção"""
    print("\n📊 RESUMO DE PRODUÇÃO")
    print("=" * 50)
    
    try:
        config = SystemConfig()
        
        print(f"🚀 Modo Produção: {'✅' if config.production.production_mode else '❌'}")
        print(f"🐛 Debug Mode: {'❌' if not config.production.debug_mode else '⚠️'}")
        print(f"📝 Log Level: {config.production.log_level}")
        print(f"🛡️  Rate Limiting: {'✅' if config.production.enable_rate_limiting else '❌'}")
        print(f"📊 Monitoramento: {'✅' if config.production.monitoring_enabled else '❌'}")
        print(f"🤖 Max Subagentes: {config.multiagent.max_subagents}")
        print(f"⏱️  Timeout Subagentes: {config.multiagent.subagent_timeout}s")
        print(f"💾 Cache Global: {config.memory.global_cache_size} itens")
        print(f"🔄 Max Requests/min: {config.production.max_requests_per_minute}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar resumo: {e}")


def main():
    """Função principal de inicialização"""
    print("🎯 INICIALIZAÇÃO DO SISTEMA RAG MULTI-AGENTE")
    print("=" * 60)
    
    # Validar ambiente
    validation = validate_environment()
    
    if not validation["valid"]:
        print(f"\n❌ FALHA NA VALIDAÇÃO:")
        for error in validation["errors"]:
            print(f"  • {error}")
        print("\n🛑 Não é possível continuar. Corrija os erros acima.")
        sys.exit(1)
    
    if validation["warnings"]:
        print(f"\n⚠️  AVISOS ENCONTRADOS:")
        for warning in validation["warnings"]:
            print(f"  • {warning}")
    
    # Configurar produção
    setup_production_environment()
    
    # Resumo final
    print_production_summary()
    
    print("\n🎉 SISTEMA PRONTO PARA PRODUÇÃO!")
    print("Para iniciar a API, execute:")
    print("  uvicorn api_multiagent:app --host 0.0.0.0 --port 8000 --workers 4")
    print("\nOu use o script de produção:")
    print("  ./production-start.sh")


if __name__ == "__main__":
    main()
