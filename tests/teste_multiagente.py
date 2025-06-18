#!/usr/bin/env python3
"""
Teste do sistema multi-agente conforme README
"""

import asyncio
import sys
import os

# Adicionar path do multi-agente
sys.path.append('multi-agent-researcher/src')

async def teste_multiagente():
    """Testa o sistema multi-agente"""
    print("🤖 Iniciando teste do sistema multi-agente...")
    
    try:
        from researcher.agents.openai_lead_researcher import OpenAILeadResearcher
        print("✅ Importação do OpenAILeadResearcher bem-sucedida")
        
        # Inicializar o lead researcher
        lead = OpenAILeadResearcher()
        print("✅ OpenAILeadResearcher inicializado")
        
        # Fazer uma pesquisa simples
        query = "O que é Zep e quais são suas principais características?"
        print(f"\n❓ Query: {query}")
        
        print("🔍 Executando pesquisa multi-agente...")
        resultado = await lead.research(
            query=query,
            objective="Análise básica do Zep"
        )
        
        print("\n📋 Resultado:")
        print(f"Status: {resultado.state}")
        print(f"Conteúdo: {resultado.content[:200]}...")
        print(f"Tempo de execução: {resultado.execution_time:.2f}s")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    sucesso = asyncio.run(teste_multiagente())
    if sucesso:
        print("\n✅ Teste multi-agente concluído com sucesso!")
    else:
        print("\n❌ Teste multi-agente falhou!")
