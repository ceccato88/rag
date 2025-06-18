"""
Teste do sistema ReAct corrigido com Pydantic fix.
"""

import asyncio
import sys
sys.path.append('multi-agent-researcher/src')

from researcher.agents.openai_lead import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext


async def test_fixed_react():
    """Testar sistema ReAct com correções Pydantic."""
    
    print("🔧 TESTE DO SISTEMA ReAct CORRIGIDO")
    print("=" * 50)
    print("Testando correção do erro Pydantic no QueryDecomposition")
    print()
    
    # Configuração
    config = OpenAILeadConfig.from_env()
    print(f"📋 Usando modelo: {config.model}")
    print(f"🔑 API Key presente: {'✅' if config.api_key else '❌'}")
    print()
    
    # Criar agente
    agent = OpenAILeadResearcher(
        agent_id="fixed-react-test",
        name="Fixed ReAct Test Agent",
        config=config
    )
    
    # Teste com query simples sobre Zep
    context = AgentContext(
        query="What is Zep memory architecture?",
        objective="Understand Zep's core memory architecture and components",
        constraints=["Focus on technical details", "Include practical examples"]
    )
    
    print("🧠 Testando query: 'What is Zep memory architecture?'")
    print("─" * 60)
    
    try:
        # Executar com sistema corrigido
        result = await agent.run(context)
        
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print()
        
        # Verificar se LLM decomposition funcionou
        reasoning_summary = agent.get_reasoning_summary()
        
        print("📊 RESULTADOS DO TESTE:")
        print(f"• Status: {result.status.name}")
        print(f"• Total de passos: {reasoning_summary['total_steps']}")
        print(f"• Tipos de passos: {set(reasoning_summary['step_types'])}")
        print(f"• Confiança: {reasoning_summary['confidence']:.2f}")
        print()
        
        # Verificar se houve fallback para heurística
        trace = agent.get_reasoning_trace()
        if "LLM decomposition failed" in trace:
            print("⚠️ LLM decomposition ainda falhando - usando fallback heurístico")
        else:
            print("✅ LLM decomposition funcionando corretamente!")
        
        # Mostrar preview do resultado
        if result.output:
            preview = result.output[:500] + "..." if len(result.output) > 500 else result.output
            print("\n📝 PREVIEW DO RESULTADO:")
            print("─" * 30)
            print(preview)
        
        print("\n🔍 TRACE RESUMIDO (últimos passos):")
        print("─" * 40)
        trace_lines = trace.split('\n')
        for line in trace_lines[-10:]:  # Últimas 10 linhas
            if line.strip():
                print(line)
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        
        # Tentar obter trace mesmo com erro
        try:
            trace = agent.get_reasoning_trace()
            print("\n🔍 Trace até o erro:")
            print(trace[-500:])  # Últimos 500 caracteres
        except:
            print("Não foi possível obter trace")


if __name__ == "__main__":
    print("🚀 INICIANDO TESTE DO SISTEMA CORRIGIDO")
    asyncio.run(test_fixed_react())
    print("\n🏁 TESTE FINALIZADO")
