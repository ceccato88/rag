#!/usr/bin/env python3
"""
🚀 SISTEMA RAG MULTI-AGENTE - VERSÃO SIMPLIFICADA

Teste direto sem modo interativo, apenas executa uma pergunta e mostra resultado.
"""

import asyncio
import sys
from pathlib import Path

# Configurar caminhos
sys.path.append('multi-agent-researcher/src')
sys.path.append('/workspaces/rag')

# Carregar configurações
from dotenv import load_dotenv, find_dotenv
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)
    print(f"✅ Configurações carregadas de: {env_file}")

from researcher.agents.openai_lead_researcher import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext


async def teste_direto():
    """Teste direto do sistema multi-agente com streaming."""
    
    print("🚀 TESTE DIRETO DO SISTEMA RAG MULTI-AGENTE")
    print("="*60)
    
    # Configurar sistema
    config = OpenAILeadConfig.from_env()
    agent = OpenAILeadResearcher(
        agent_id="teste-direto",
        name="Sistema RAG Multi-Agente",
        config=config
    )
    
    print(f"📊 Configuração:")
    print(f"  • Modelo: {config.model}")
    print(f"  • Max subagentes: {config.max_subagents}")
    print(f"  • API Key: {'✅' if config.api_key else '❌'}")
    print()
    
    # Pergunta de teste
    pergunta = "O que é Zep e como funciona a camada de memória?"
    
    print(f"❓ Pergunta: {pergunta}")
    print()
    print("🧠 Raciocínio em tempo real:")
    print("-" * 50)
    
    # Criar contexto
    context = AgentContext(
        query=pergunta,
        objective="Entender o conceito e funcionamento do Zep memory layer",
        constraints=["Foco em aspectos técnicos"]
    )
    
    # Executar com streaming manual
    task = asyncio.create_task(agent.run(context))
    last_len = 0
    
    while not task.done():
        if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
            trace = agent.reasoner.reasoning_history
            # Mostrar novos passos
            for step in trace[last_len:]:
                timestamp = step.timestamp.strftime("%H:%M:%S")
                print(f"[{timestamp}] [{step.step_type.upper()}] {step.content}")
                if step.observations:
                    print(f"           💡 {step.observations}")
                if step.next_action:
                    print(f"           ➡️  {step.next_action}")
                print()
            last_len = len(trace)
        
        await asyncio.sleep(0.5)
    
    # Obter resultado
    result = await task
    
    # Mostrar passos finais se houver
    if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
        trace = agent.reasoner.reasoning_history
        for step in trace[last_len:]:
            timestamp = step.timestamp.strftime("%H:%M:%S")
            print(f"[{timestamp}] [{step.step_type.upper()}] {step.content}")
            if step.observations:
                print(f"           💡 {step.observations}")
            if step.next_action:
                print(f"           ➡️  {step.next_action}")
            print()
    
    print("="*60)
    print("🎉 RESULTADO FINAL:")
    print("="*60)
    print(f"Status: {result.status}")
    print()
    print("📝 Resposta:")
    print(result.output[:1000])  # Primeiros 1000 caracteres
    if len(result.output) > 1000:
        print("...")
    print()
    
    # Estatísticas
    if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
        total_steps = len(agent.reasoner.reasoning_history)
        step_types = {}
        for step in agent.reasoner.reasoning_history:
            step_types[step.step_type] = step_types.get(step.step_type, 0) + 1
        
        print("📊 Estatísticas do Raciocínio:")
        print(f"  • Total de passos: {total_steps}")
        for step_type, count in step_types.items():
            print(f"  • {step_type}: {count}")
    
    print("\n✅ Teste concluído!")


async def teste_busca_direta():
    """Teste direto da busca RAG para verificar se dados reais estão funcionando."""
    
    print("\n🔍 TESTE DIRETO DA BUSCA RAG")
    print("="*40)
    
    try:
        # Testar se consegue importar e usar o search.py diretamente
        sys.path.append('/workspaces/rag')
        from search import ProductionConversationalRAG
        
        print("📋 Testando conexão com banco de dados...")
        rag = ProductionConversationalRAG()
        
        # Fazer busca direta
        resultado = rag.search_and_answer("Zep memory layer")
        resultado_str = resultado.get('answer', str(resultado))
        
        print("✅ Busca executada com sucesso!")
        print(f"📄 Resultado (preview):")
        print(resultado_str[:500])
        if len(resultado_str) > 500:
            print("...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na busca direta: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 SISTEMA RAG MULTI-AGENTE - TESTE SIMPLIFICADO")
    print("="*60)
    
    # Primeiro testar busca direta
    sucesso_busca = asyncio.run(teste_busca_direta())
    
    if sucesso_busca:
        print("\n✅ Busca RAG funcionando! Prosseguindo com teste completo...")
        # Testar sistema completo
        asyncio.run(teste_direto())
    else:
        print("\n❌ Busca RAG não está funcionando. Verificar conexão com banco de dados.")
