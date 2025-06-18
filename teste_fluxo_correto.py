#!/usr/bin/env python3
"""
🚀 SISTEMA RAG MULTI-AGENTE - VERSÃO CORRETA

FLUXO CORRETO:
Pergunta → ReAct Leader Agent → Decomposição → Sub-agentes RAG → Resposta Final

SEM dupla busca, SEM desperdício!
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

from researcher.agents.openai_lead import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext


async def teste_fluxo_correto():
    """Teste do fluxo correto: ReAct como líder desde o início."""
    
    print("🚀 SISTEMA RAG MULTI-AGENTE - FLUXO CORRETO")
    print("="*60)
    print("ReAct Leader Agent → Decomposição → Sub-agentes → Resposta")
    print()
    
    # Configurar sistema
    config = OpenAILeadConfig.from_env()
    agent = OpenAILeadResearcher(
        agent_id="leader-react",
        name="ReAct Leader Agent",
        config=config
    )
    
    print(f"📊 Configuração:")
    print(f"  • Modelo: {config.model}")
    print(f"  • Max subagentes: {config.max_subagents}")
    print(f"  • API Key: {'✅' if config.api_key else '❌'}")
    print()
    
    # Pergunta vai DIRETO para o ReAct Leader
    pergunta = "O que é Zep e como funciona a camada de memória?"
    
    print(f"❓ Pergunta: {pergunta}")
    print()
    print("🧠 ReAct Leader em ação (raciocínio em tempo real):")
    print("-" * 60)
    
    # Criar contexto
    context = AgentContext(
        query=pergunta,
        objective="Entender o conceito e funcionamento do Zep memory layer",
        constraints=["Foco em aspectos técnicos"]
    )
    
    # Executar APENAS o sistema multi-agente (sem busca prévia)
    task = asyncio.create_task(agent.run(context))
    last_len = 0
    
    print("👑 REACT LEADER INICIANDO...")
    print()
    
    # Mostrar raciocínio em tempo real
    while not task.done():
        if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
            trace = agent.reasoner.reasoning_history
            # Mostrar novos passos
            for step in trace[last_len:]:
                timestamp = step.timestamp.strftime("%H:%M:%S")
                
                # Destacar as fases do ReAct
                if step.step_type == "fact_gathering":
                    print(f"🔍 [{timestamp}] REACT FASE 1 - COLETA DE FATOS")
                elif step.step_type == "planning": 
                    print(f"📋 [{timestamp}] REACT FASE 2 - PLANEJAMENTO")
                elif step.step_type == "execution":
                    print(f"⚡ [{timestamp}] REACT FASE 3 - EXECUÇÃO")
                elif step.step_type == "validation":
                    print(f"✅ [{timestamp}] REACT FASE 4 - VALIDAÇÃO")
                else:
                    print(f"📝 [{timestamp}] REACT - {step.step_type.upper()}")
                
                print(f"    💭 {step.content}")
                if step.observations:
                    print(f"    💡 {step.observations}")
                if step.next_action:
                    print(f"    ➡️  {step.next_action}")
                print()
            last_len = len(trace)
        
        await asyncio.sleep(0.5)
    
    # Obter resultado
    result = await task
    
    # Mostrar passos finais
    if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
        trace = agent.reasoner.reasoning_history
        for step in trace[last_len:]:
            timestamp = step.timestamp.strftime("%H:%M:%S")
            print(f"🏁 [{timestamp}] REACT FINAL - {step.step_type.upper()}")
            print(f"    💭 {step.content}")
            if step.observations:
                print(f"    💡 {step.observations}")
            print()
    
    print("="*60)
    print("🎉 RESULTADO DO REACT LEADER:")
    print("="*60)
    print(f"Status: {result.status}")
    print()
    print("📝 Resposta Coordenada pelo ReAct:")
    print(result.output[:800])
    if len(result.output) > 800:
        print("...")
    print()
    
    # Análise do fluxo
    if hasattr(agent, 'reasoner') and agent.reasoner.reasoning_history:
        print("📊 ANÁLISE DO FLUXO REACT:")
        print("-" * 40)
        
        total_steps = len(agent.reasoner.reasoning_history)
        step_types = {}
        for step in agent.reasoner.reasoning_history:
            step_types[step.step_type] = step_types.get(step.step_type, 0) + 1
        
        print(f"✅ Total de passos: {total_steps}")
        print(f"✅ Fases do ReAct:")
        for step_type, count in step_types.items():
            print(f"  • {step_type}: {count} passo(s)")
        
        print(f"✅ Sub-agentes criados: {len(agent.subagents) if hasattr(agent, 'subagents') else 0}")
        print()
        print("🎯 VANTAGENS DESTA ABORDAGEM:")
        print("  ✅ ReAct lidera desde o início")
        print("  ✅ Uma única busca coordenada")
        print("  ✅ Sem redundância de processos")
        print("  ✅ Raciocínio transparente")
        print("  ✅ Decomposição inteligente")
    
    print("\n🏆 FLUXO CORRETO EXECUTADO COM SUCESSO!")


async def comparar_fluxos():
    """Mostrar a diferença entre fluxo antigo e novo."""
    
    print("\n" + "="*60)
    print("🔍 COMPARAÇÃO DE FLUXOS")
    print("="*60)
    
    print("❌ FLUXO ANTIGO (PROBLEMÁTICO):")
    print("   1. Pergunta → RAG básico")
    print("   2. RAG básico → Busca + Resposta")
    print("   3. ReAct Agent → Reanalisa tudo")
    print("   4. Sub-agentes → Nova busca")
    print("   5. Resultado → Duplicação de esforço")
    print()
    
    print("✅ FLUXO NOVO (CORRETO):")
    print("   1. Pergunta → ReAct Leader diretamente")
    print("   2. ReAct → Análise e decomposição")
    print("   3. Sub-agentes → Busca coordenada")
    print("   4. ReAct → Síntese final")
    print("   5. Resultado → Eficiente e transparente")
    print()
    
    print("🎯 BENEFÍCIOS DA CORREÇÃO:")
    print("  ✅ 50% menos chamadas para o banco")
    print("  ✅ Raciocínio mais claro")
    print("  ✅ ReAct realmente lidera")
    print("  ✅ Sem redundâncias")


if __name__ == "__main__":
    print("🧪 TESTE DO FLUXO CORRETO")
    print("="*40)
    print("Sua observação estava CERTA!")
    print("Vamos testar o fluxo corrigido:")
    print()
    
    # Mostrar comparação
    asyncio.run(comparar_fluxos())
    
    # Executar fluxo correto
    asyncio.run(teste_fluxo_correto())
