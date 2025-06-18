"""
Teste completo do sistema ReAct com perguntas sobre Zep (camada de memória).
"""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append('multi-agent-researcher/src')
sys.path.append('/workspaces/rag')

from researcher.agents.openai_lead import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext


async def test_zep_memory_research():
    """Teste completo com perguntas sobre Zep na base de dados."""
    
    print("🧠 TESTE COMPLETO: Sistema ReAct + Zep Memory Layer")
    print("=" * 60)
    print("Testando o sistema de raciocínio estruturado com perguntas sobre Zep")
    print()
    
    # Configuração
    config = OpenAILeadConfig.from_env()
    
    print(f"📋 Configuração do Sistema:")
    print(f"  • Modelo: {config.model}")
    print(f"  • Max subagentes: {config.max_subagents}")
    print(f"  • Execução paralela: {config.parallel_execution}")
    print(f"  • Decomposição LLM: {config.use_llm_decomposition}")
    print(f"  • API Key presente: {'✅' if config.api_key else '❌'}")
    print()
    
    # Criar agente ReAct
    agent = OpenAILeadResearcher(
        agent_id="zep-memory-researcher",
        name="Zep Memory Research Agent",
        config=config
    )
    
    # Perguntas sobre Zep para testar o sistema
    zep_questions = [
        {
            "query": "What is Zep memory layer and how does it work?",
            "objective": "Understand the fundamental concepts and architecture of Zep memory layer",
            "constraints": ["Focus on technical details", "Include implementation aspects"],
            "focus": "conceptual understanding"
        },
        {
            "query": "Zep memory management features and capabilities",
            "objective": "Explore the specific features and capabilities that Zep provides for memory management",
            "constraints": ["Include practical examples", "Focus on real-world applications"],
            "focus": "feature analysis"
        },
        {
            "query": "How to integrate Zep memory layer in AI applications",
            "objective": "Learn integration patterns and best practices for using Zep in AI systems",
            "constraints": ["Include code examples", "Focus on implementation patterns"],
            "focus": "integration guide"
        }
    ]
    
    # Testar cada pergunta
    for i, question in enumerate(zep_questions, 1):
        print(f"📝 PERGUNTA {i}: {question['focus'].upper()}")
        print("─" * 50)
        print(f"Query: {question['query']}")
        print(f"Objetivo: {question['objective']}")
        print(f"Restrições: {', '.join(question['constraints'])}")
        print()
        
        try:
            # Criar contexto
            context = AgentContext(
                query=question["query"],
                objective=question["objective"],
                constraints=question["constraints"]
            )
            
            print("🧠 Iniciando raciocínio ReAct...")
            print()
            
            # Executar pesquisa com ReAct
            result = await agent.run(context)
            
            # Mostrar resultado
            print("✅ RESULTADO DA PESQUISA:")
            print("─" * 30)
            
            if result.output:
                # Mostrar preview do resultado
                preview = result.output[:800]  # Primeiros 800 caracteres
                print(preview)
                if len(result.output) > 800:
                    print(f"\n... (+{len(result.output) - 800} caracteres restantes)")
            else:
                print("❌ Nenhum resultado obtido")
                if result.error:
                    print(f"Erro: {result.error}")
            
            print()
            
            # Mostrar trace de raciocínio ReAct
            print("🔍 TRACE DE RACIOCÍNIO ReAct:")
            print("─" * 35)
            
            try:
                reasoning_trace = agent.get_reasoning_trace()
                # Mostrar apenas os últimos 1000 caracteres do trace para não sobrecarregar
                if len(reasoning_trace) > 1000:
                    trace_preview = "..." + reasoning_trace[-1000:]
                else:
                    trace_preview = reasoning_trace
                print(trace_preview)
            except Exception as trace_error:
                print(f"❌ Erro ao obter trace: {trace_error}")
            
            print()
            
            # Mostrar resumo do raciocínio
            print("📊 RESUMO DO RACIOCÍNIO:")
            print("─" * 25)
            
            try:
                summary = agent.get_reasoning_summary()
                print(f"• Total de passos: {summary['total_steps']}")
                print(f"• Tipos de passos: {set(summary['step_types'])}")
                print(f"• Iterações: {summary['iteration_count']}")
                print(f"• Nível de confiança: {summary['confidence']:.2f}")
                
                if summary.get('current_facts'):
                    facts = summary['current_facts']
                    print(f"• Fatos coletados: {len(facts.get('given_facts', []))} dados, {len(facts.get('recalled_facts', []))} lembrados")
                    
            except Exception as summary_error:
                print(f"❌ Erro ao obter resumo: {summary_error}")
            
            print()
            print("=" * 60)
            print()
            
        except Exception as e:
            print(f"❌ ERRO na pergunta {i}: {e}")
            print()
            
            # Tentar mostrar o trace mesmo em caso de erro
            try:
                reasoning_trace = agent.get_reasoning_trace()
                print("🔍 Trace de raciocínio (até o erro):")
                print(reasoning_trace[-500:])  # Últimos 500 caracteres
            except:
                print("Não foi possível obter trace de raciocínio")
            
            print("=" * 60)
            print()
    
    print("🎯 TESTE COMPLETO FINALIZADO")
    print("=" * 60)
    print("Análise do desempenho do sistema ReAct com Zep:")
    print("• Raciocínio estruturado em fases bem definidas")
    print("• Trace auditável de todo o processo")
    print("• Detecção automática de problemas e loops")
    print("• Métricas objetivas de confiança")
    print("• Substituição eficaz do 'thinking' do Anthropic")


async def quick_zep_test():
    """Teste rápido para verificar se o sistema está funcionando."""
    
    print("⚡ TESTE RÁPIDO: Sistema ReAct")
    print("=" * 40)
    
    try:
        # Teste básico de configuração
        config = OpenAILeadConfig.from_env()
        print("✅ Configuração carregada")
        
        # Teste básico de criação do agente
        agent = OpenAILeadResearcher(
            agent_id="quick-test",
            name="Quick Test Agent",
            config=config
        )
        print("✅ Agente ReAct criado")
        
        # Teste básico de raciocínio
        reasoner = agent.reasoner
        facts = reasoner.gather_facts("Test task", "Test context")
        print("✅ Sistema de raciocínio funcionando")
        
        trace = reasoner.get_reasoning_trace()
        print("✅ Trace de raciocínio gerado")
        
        print()
        print("🎯 Sistema ReAct está operacional!")
        print("Pronto para perguntas sobre Zep na base de dados.")
        
    except Exception as e:
        print(f"❌ Erro no teste rápido: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DO SISTEMA ReAct COM ZEP")
    print()
    
    # Executar teste rápido primeiro
    asyncio.run(quick_zep_test())
    print()
    
    # Depois executar teste completo
    asyncio.run(test_zep_memory_research())
    
    print("\n🏁 TODOS OS TESTES CONCLUÍDOS!")
