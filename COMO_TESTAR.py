#!/usr/bin/env python3
"""
🎯 COMO TESTAR O SISTEMA DE PONTA A PONTA

Passos para testar o sistema RAG Multi-Agente completo:
"""

print("🧪 COMO TESTAR O SISTEMA RAG MULTI-AGENTE")
print("="*60)
print()

print("📋 PASSOS PARA TESTAR:")
print()

print("1️⃣  TESTE BÁSICO DO RAG:")
print("   python search.py")
print("   → Digite: 'o que é zep?'")
print("   → Deve retornar informações sobre Zep dos documentos")
print()

print("2️⃣  TESTE DO SISTEMA MULTI-AGENTE:")
print("   python teste_simples.py")
print("   → Executa o sistema completo com ReAct reasoning")
print("   → Mostra todo o processo de raciocínio estruturado")
print()

print("3️⃣  TESTE AVANÇADO COM ZEP:")
print("   python test_zep_complete.py")
print("   → Teste completo com múltiplas perguntas sobre Zep")
print("   → Demonstra capacidades avançadas")
print()

print("4️⃣  VERIFICAR DOCUMENTOS:")
print("   python verify_zep_docs.py")
print("   → Confirma que há documentos sobre Zep na base")
print()

print("📊 O QUE VOCÊ DEVE VER:")
print()

print("✅ FLUXO COMPLETO:")
print("   Pergunta → OpenAI Lead Agent → ReAct Reasoning →")
print("   Query Decomposition → Sub-agentes RAG → Busca Docs →")
print("   Combine Results → Resposta Final")
print()

print("✅ RACIOCÍNIO REACT:")
print("   - Fact Gathering: coleta contexto")
print("   - Planning: quebra a pergunta")
print("   - Execution: executa sub-tarefas")
print("   - Validation: valida resultados")
print("   - Synthesis: combina tudo")
print()

print("✅ BUSCA DE DOCUMENTOS:")
print("   - Embedding da pergunta")
print("   - Busca por similaridade")
print("   - Re-ranking com GPT")
print("   - Documentos relevantes retornados")
print()

print("🔧 RESOLUÇÃO DE PROBLEMAS:")
print()
print("❌ Se aparecer 'Mock Document':")
print("   → A conexão real com o DB falhou")
print("   → Sistema usa dados fictícios como fallback")
print("   → Teste 'python search.py' primeiro")
print()

print("❌ Se der erro de API:")
print("   → Verifique OPENAI_API_KEY no .env")
print("   → Sistema vai usar decomposição heurística")
print()

print("❌ Se não encontrar documentos:")
print("   → Execute 'python indexer.py' para indexar PDFs")
print("   → Confirme conexão com Astra DB")
print()

print("🚀 COMANDO MAIS SIMPLES:")
print("   python search.py")
print("   (teste interativo básico)")
print()

# Teste de conectividade
print("🧪 TESTE DE CONECTIVIDADE:")
print("-" * 30)

try:
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    # Verificar variáveis importantes
    openai_key = os.getenv('OPENAI_API_KEY', '')
    astra_token = os.getenv('ASTRA_DB_APPLICATION_TOKEN', '')
    
    print(f"✅ OpenAI API Key: {'configurada' if openai_key else '❌ não encontrada'}")
    print(f"✅ Astra DB Token: {'configurada' if astra_token else '❌ não encontrada'}")
    
    # Teste de importação
    import sys
    sys.path.append('multi-agent-researcher/src')
    
    from researcher.agents.openai_lead import OpenAILeadResearcher
    print("✅ Sistema multi-agente: importado com sucesso")
    
    print()
    print("🎯 SISTEMA PRONTO PARA TESTE!")
    print()
    print("Execute: python search.py")
    
except Exception as e:
    print(f"❌ Erro na verificação: {e}")
    print("🔧 Verifique se todas as dependências estão instaladas")
