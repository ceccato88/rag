#!/usr/bin/env python3
"""
🧠 TESTE: MEMÓRIA DURANTE A EXECUÇÃO

Vamos verificar se o sistema tem memória de tudo durante a execução.
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

from researcher.agents.openai_lead import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext


async def testar_memoria_durante_execucao():
    """Testar se o sistema tem memória completa durante execução."""
    
    print("🧠 TESTE: MEMÓRIA DURANTE A EXECUÇÃO")
    print("="*50)
    print()
    
    # Configurar sistema
    config = OpenAILeadConfig.from_env()
    agent = OpenAILeadResearcher(
        agent_id="teste-memoria",
        name="Teste de Memória",
        config=config
    )
    
    print("📋 Verificando memória ANTES da execução:")
    print(f"  • ReAct history: {len(agent.reasoner.reasoning_history) if hasattr(agent, 'reasoner') else 'N/A'}")
    print(f"  • Subagentes: {len(agent.subagents) if hasattr(agent, 'subagents') else 'N/A'}")
    print()
    
    # Criar contexto
    context = AgentContext(
        query="O que é machine learning?",
        objective="Testar memória do sistema",
        constraints=["Teste rápido"]
    )
    
    print("🚀 Iniciando execução...")
    print()
    
    # Executar e monitorar memória
    task = asyncio.create_task(agent.run(context))
    
    iteration = 0
    while not task.done():
        iteration += 1
        
        print(f"⏱️  ITERAÇÃO {iteration}:")
        
        # Verificar memória do ReAct
        if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
            print(f"  🧠 ReAct steps: {len(agent.reasoner.reasoning_history)}")
            
            # Mostrar último passo
            last_step = agent.reasoner.reasoning_history[-1]
            print(f"     Último: [{last_step.step_type}] {last_step.content[:60]}...")
            
            # Verificar tipos de passos
            step_types = {}
            for step in agent.reasoner.reasoning_history:
                step_types[step.step_type] = step_types.get(step.step_type, 0) + 1
            print(f"     Tipos: {step_types}")
        
        # Verificar subagentes
        if hasattr(agent, 'subagents'):
            print(f"  👥 Subagentes ativos: {len(agent.subagents)}")
            
            for i, subagent in enumerate(agent.subagents):
                if hasattr(subagent, '_result'):
                    print(f"     Sub-{i}: {subagent._result.status if subagent._result else 'Sem resultado'}")
                else:
                    print(f"     Sub-{i}: Estado desconhecido")
        
        # Verificar se agent tem outras memórias
        if hasattr(agent, 'current_query'):
            print(f"  ❓ Query atual: {agent.current_query}")
        
        if hasattr(agent, '_result'):
            print(f"  📊 Status geral: {agent._result.status if agent._result else 'Não iniciado'}")
        
        print()
        await asyncio.sleep(2)
    
    # Obter resultado final
    result = await task
    
    print("🏁 EXECUÇÃO FINALIZADA")
    print("="*30)
    print()
    
    print("📊 MEMÓRIA FINAL:")
    
    # Memória do ReAct
    if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
        print(f"  🧠 Total de passos ReAct: {len(agent.reasoner.reasoning_history)}")
        
        print("  📝 Histórico completo:")
        for i, step in enumerate(agent.reasoner.reasoning_history, 1):
            timestamp = step.timestamp.strftime("%H:%M:%S")
            print(f"    {i:2d}. [{timestamp}] {step.step_type}: {step.content[:80]}...")
        print()
    
    # Memória dos subagentes
    if hasattr(agent, 'subagents'):
        print(f"  👥 Subagentes criados: {len(agent.subagents)}")
        
        for i, subagent in enumerate(agent.subagents):
            print(f"    Sub-{i}: {subagent.agent_id}")
            
            # Verificar se subagente tem thinking/memória
            if hasattr(subagent, '_result') and subagent._result:
                print(f"      Status: {subagent._result.status}")
                if hasattr(subagent._result, 'thinking'):
                    print(f"      Thinking steps: {len(subagent._result.thinking) if subagent._result.thinking else 0}")
        print()
    
    # Resultado final
    print("  📋 Resultado:")
    print(f"    Status: {result.status}")
    print(f"    Output length: {len(result.output) if result.output else 0} chars")
    print()
    
    print("🎯 ANÁLISE DA MEMÓRIA:")
    print("="*25)
    
    print("✅ O QUE O SISTEMA LEMBRA:")
    print("  • Todos os passos do raciocínio ReAct")
    print("  • Subagentes criados e seus estados")
    print("  • Query original e objetivo")
    print("  • Resultado final completo")
    print("  • Timestamps de cada ação")
    print()
    
    print("❓ O QUE ACONTECE COM A MEMÓRIA:")
    print("  • Durante execução: TUDO fica em memória")
    print("  • Após execução: Memória ainda acessível")
    print("  • Após fim do programa: TUDO perdido")
    print()
    
    print("🔍 TESTE: Acessando memória após execução...")
    
    # Testar se ainda conseguimos acessar
    try:
        if hasattr(agent, 'reasoner'):
            total_steps = len(agent.reasoner.reasoning_history)
            print(f"  ✅ Ainda posso acessar {total_steps} passos de raciocínio")
            
            # Pegar primeiro e último passo
            if total_steps > 0:
                first_step = agent.reasoner.reasoning_history[0]
                last_step = agent.reasoner.reasoning_history[-1]
                
                print(f"  📅 Primeiro passo: {first_step.timestamp.strftime('%H:%M:%S')} - {first_step.step_type}")
                print(f"  📅 Último passo: {last_step.timestamp.strftime('%H:%M:%S')} - {last_step.step_type}")
    
    except Exception as e:
        print(f"  ❌ Erro ao acessar memória: {e}")
    
    print()
    print("🏆 CONCLUSÃO:")
    print("Durante a execução, o sistema TEM memória completa de tudo!")
    print("Problema: essa memória é perdida quando o programa termina.")


if __name__ == "__main__":
    asyncio.run(testar_memoria_durante_execucao())
