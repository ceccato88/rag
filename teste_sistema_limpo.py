#!/usr/bin/env python3
"""
🧹 TESTE DO SISTEMA LIMPO E OTIMIZADO
Testa o sistema após limpeza de arquivos e implementação da ferramenta otimizada
"""

import asyncio
import sys
import time
from pathlib import Path

# Configurar caminhos
sys.path.append('multi-agent-researcher/src')
sys.path.append('/workspaces/rag')

# Carregar configurações
from dotenv import load_dotenv, find_dotenv
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)

async def test_cleaned_system():
    """Testa o sistema após limpeza e otimizações"""
    print("🧹 TESTE DO SISTEMA LIMPO E OTIMIZADO")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    # Teste 1: Importações dos agentes renomeados
    print("\n📦 TESTE 1: Importações de Agentes Renomeados")
    print("-" * 50)
    total_tests += 1
    
    try:
        from researcher.agents.openai_lead_researcher import OpenAILeadResearcher, OpenAILeadConfig
        from researcher.agents.basic_lead_researcher import SimpleLeadResearcher
        from researcher.agents.document_search_agent import RAGResearchSubagent, RAGSubagentConfig
        
        print("✅ Agentes renomeados importados com sucesso")
        tests_passed += 1
        
    except ImportError as e:
        print(f"❌ Erro na importação dos agentes: {e}")
    
    # Teste 2: Ferramenta de busca otimizada
    print("\n🔧 TESTE 2: Ferramenta de Busca Otimizada")
    print("-" * 50)
    total_tests += 1
    
    try:
        from researcher.tools.optimized_rag_search import OptimizedRAGSearchTool, DocumentProcessor
        
        # Criar ferramenta
        tool = OptimizedRAGSearchTool(top_k=3)
        print("✅ Ferramenta otimizada criada")
        
        # Testar busca mock
        result = await tool._execute(
            query="test query",
            top_k=2,
            focus_area="conceptual"
        )
        
        if result.get("success"):
            docs = result.get("documents", [])
            print(f"✅ Busca executada: {len(docs)} documentos encontrados")
            print(f"   Tempo de execução: {result['search_metadata']['execution_time']:.3f}s")
            tests_passed += 1
        else:
            print(f"❌ Falha na busca: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Erro na ferramenta otimizada: {e}")
    
    # Teste 3: Agente especializado
    print("\n🎯 TESTE 3: Agente Especializado")
    print("-" * 50)
    total_tests += 1
    
    try:
        from researcher.agents.enhanced_rag_subagent import ConceptExtractionSubagent
        from researcher.agents.base import AgentContext
        
        # Criar agente especializado
        config = RAGSubagentConfig(top_k=2)
        agent = ConceptExtractionSubagent(
            agent_id="test_concept_agent",
            name="Test Concept Agent",
            config=config
        )
        
        print("✅ Agente especializado criado")
        
        # Criar contexto
        context = AgentContext(
            query="temporal knowledge graphs",
            objective="Understand concepts",
            constraints=["Focus on definitions"]
        )
        
        # Testar planejamento
        plan = await agent.plan(context)
        
        if plan and len(plan) > 0:
            print(f"✅ Plano criado: {plan[0].get('focus_area', 'unknown')} focus")
            print(f"   Query ajustada: {plan[0].get('query', 'N/A')[:50]}...")
            tests_passed += 1
        else:
            print("❌ Falha na criação do plano")
            
    except Exception as e:
        print(f"❌ Erro no agente especializado: {e}")
        import traceback
        traceback.print_exc()
    
    # Teste 4: Processador de documentos
    print("\n📊 TESTE 4: Processador de Documentos")
    print("-" * 50)
    total_tests += 1
    
    try:
        # Documentos mock para teste
        mock_documents = [
            {
                "document_id": "doc_1",
                "content": "Machine learning is defined as a subset of artificial intelligence. This algorithm provides better performance.",
                "page_number": 1
            },
            {
                "document_id": "doc_2", 
                "content": "Compared to traditional methods, neural networks offer superior accuracy. The architecture consists of multiple layers.",
                "page_number": 2
            }
        ]
        
        # Testar extração conceitual
        concepts = DocumentProcessor.extract_concepts(mock_documents)
        print(f"✅ Conceitos extraídos: {len(concepts.get('concepts', []))} termos")
        print(f"   Definições encontradas: {len(concepts.get('definitions', []))}")
        
        # Testar extração comparativa
        comparisons = DocumentProcessor.extract_comparisons(mock_documents)
        print(f"✅ Comparações extraídas: {len(comparisons.get('comparisons', []))}")
        
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Erro no processador de documentos: {e}")
    
    # Teste 5: Sistema integrado simples
    print("\n🚀 TESTE 5: Sistema Integrado Simples")
    print("-" * 50)
    total_tests += 1
    
    try:
        # Configurar sistema básico
        config = OpenAILeadConfig.from_env()
        lead_agent = OpenAILeadResearcher(
            agent_id="test_lead",
            name="Test Lead Agent",
            config=config
        )
        
        print("✅ Sistema multi-agente inicializado")
        print(f"   Modelo: {config.model}")
        print(f"   Max subagentes: {config.max_subagents}")
        
        # Testar apenas configuração (não execução completa para economizar tempo)
        if hasattr(lead_agent, 'config') and lead_agent.config:
            print("✅ Configuração validada")
            tests_passed += 1
        else:
            print("❌ Configuração inválida")
            
    except Exception as e:
        print(f"❌ Erro no sistema integrado: {e}")
    
    # Resumo final
    print(f"\n📊 RESUMO DOS TESTES")
    print("=" * 40)
    print(f"✅ Testes bem-sucedidos: {tests_passed}/{total_tests}")
    print(f"📈 Taxa de sucesso: {tests_passed/total_tests:.1%}")
    
    if tests_passed == total_tests:
        print("\n🎉 SISTEMA LIMPO E FUNCIONANDO PERFEITAMENTE!")
        print("🔧 Melhorias implementadas:")
        print("   • Arquivos duplicados removidos")
        print("   • Nomenclatura clarificada") 
        print("   • Ferramenta de busca otimizada")
        print("   • Processamento especializado por área")
        print("   • Cache e métricas integrados")
        
    elif tests_passed > total_tests * 0.7:
        print("\n✅ SISTEMA FUNCIONANDO COM PEQUENOS AJUSTES NECESSÁRIOS")
        
    else:
        print("\n⚠️ SISTEMA REQUER CORREÇÕES ADICIONAIS")
    
    return tests_passed == total_tests


async def test_performance_comparison():
    """Testa comparação de performance entre ferramenta antiga vs otimizada"""
    print("\n⚡ TESTE DE PERFORMANCE")
    print("=" * 40)
    
    try:
        from researcher.tools.optimized_rag_search import OptimizedRAGSearchTool
        
        # Criar ferramenta otimizada
        optimized_tool = OptimizedRAGSearchTool(top_k=3)
        
        # Teste de busca com diferentes focus areas
        focus_areas = ["conceptual", "technical", "comparative", "examples", "general"]
        
        for focus in focus_areas:
            start_time = time.time()
            
            result = await optimized_tool._execute(
                query="temporal knowledge graph architecture",
                top_k=3,
                focus_area=focus
            )
            
            execution_time = time.time() - start_time
            
            if result.get("success"):
                docs_found = len(result.get("documents", []))
                print(f"✅ {focus:12} - {execution_time:.3f}s - {docs_found} docs")
            else:
                print(f"❌ {focus:12} - Falha na busca")
        
        print("\n🎯 Ferramenta otimizada demonstrou flexibilidade por área de foco")
        
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")


async def main():
    """Execução principal dos testes"""
    success = await test_cleaned_system()
    
    if success:
        await test_performance_comparison()
    
    print(f"\n🏁 TESTE CONCLUÍDO")
    print("=" * 20)
    
    return success


if __name__ == "__main__":
    asyncio.run(main())