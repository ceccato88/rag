#!/usr/bin/env python3
"""
Script de Teste - Integração do Sistema Enhanced
Testa a integração dos componentes enhanced com o sistema atual
"""

import os
import sys
import time
import asyncio
import logging
from pathlib import Path

# Adicionar paths necessários
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "multi-agent-researcher" / "src"))

from researcher.enhanced.enhanced_integration import (
    EnhancedRAGSystem, 
    EnhancedLeadResearcher,
    create_enhanced_lead_researcher
)
from src.core.config import SystemConfig

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockRAGSystem:
    """Mock do sistema RAG para testes"""
    
    def search_and_answer(self, query: str):
        """Mock da busca RAG"""
        return {
            "answer": f"Esta é uma resposta mock para: {query}. Contém informações detalhadas sobre o tópico solicitado.",
            "selected_pages_details": [
                {
                    "document": "doc_test",
                    "page_number": 1,
                    "similarity_score": 0.85
                },
                {
                    "document": "doc_test",
                    "page_number": 2,
                    "similarity_score": 0.78
                }
            ]
        }


class MockAgentContext:
    """Mock do AgentContext para testes"""
    
    def __init__(self, query: str, objective: str = None):
        self.query = query
        self.objective = objective


async def test_enhanced_decomposition():
    """Testa decomposição enhanced"""
    logger.info("🧪 Testando Enhanced Decomposition...")
    
    try:
        from openai import OpenAI
        from researcher.enhanced.enhanced_decomposition import RAGDecomposer
        
        client = OpenAI()
        decomposer = RAGDecomposer(client)
        
        query = "Como funciona machine learning e quais são suas aplicações práticas?"
        
        decomposition = decomposer.decompose(query)
        
        logger.info(f"✅ Decomposição criada:")
        logger.info(f"   Query original: {decomposition.original_query}")
        logger.info(f"   Query refinada: {decomposition.refined_query}")
        logger.info(f"   Complexidade: {decomposition.approach.complexity}")
        logger.info(f"   Estratégia: {decomposition.approach.strategy}")
        logger.info(f"   Subagentes: {len(decomposition.subagent_tasks)}")
        
        for i, task in enumerate(decomposition.subagent_tasks):
            logger.info(f"   Subagente {i+1}: {task.specialist_type.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de decomposição: {e}")
        return False


async def test_enhanced_system():
    """Testa sistema enhanced completo"""
    logger.info("🧪 Testando Enhanced RAG System...")
    
    try:
        from openai import OpenAI
        
        # Criar mock RAG e enhanced system
        mock_rag = MockRAGSystem()
        client = OpenAI()
        enhanced_system = EnhancedRAGSystem(mock_rag, client)
        
        query = "O que é inteligência artificial?"
        
        # Executar busca enhanced
        start_time = time.time()
        result = await enhanced_system.enhanced_search(query)
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Sistema enhanced executado em {processing_time:.2f}s:")
        logger.info(f"   Query: {result.original_query}")
        logger.info(f"   Resposta: {result.final_answer[:100]}...")
        logger.info(f"   Confiança: {result.confidence_score:.2f}")
        logger.info(f"   Subagentes: {len(result.subagent_results)}")
        logger.info(f"   Fontes: {len(result.sources_cited)}")
        logger.info(f"   Qualidade geral: {result.quality_metrics.get('overall_quality', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste enhanced system: {e}")
        return False


async def test_enhanced_lead_researcher():
    """Testa Enhanced Lead Researcher"""
    logger.info("🧪 Testando Enhanced Lead Researcher...")
    
    try:
        # Criar enhanced lead researcher
        mock_rag = MockRAGSystem()
        enhanced_researcher = create_enhanced_lead_researcher(mock_rag)
        
        # Criar contexto mock
        context = MockAgentContext(
            query="Quais são os benefícios do deep learning?",
            objective="Entender aplicações práticas"
        )
        
        # Testar planning
        logger.info("🧠 Testando planning...")
        plan = await enhanced_researcher.plan(context)
        logger.info(f"   Plano criado com {len(plan)} etapas:")
        for i, step in enumerate(plan):
            logger.info(f"   {i+1}. {step}")
        
        # Testar execução completa
        logger.info("🚀 Testando execução completa...")
        result = await enhanced_researcher.run(context)
        
        logger.info(f"✅ Enhanced Lead Researcher executado:")
        logger.info(f"   Agent ID: {result.agent_id}")
        logger.info(f"   Status: {result.status}")
        logger.info(f"   Resposta: {result.output[:100] if result.output else 'N/A'}...")
        logger.info(f"   Erro: {result.error or 'Nenhum'}")
        logger.info(f"   Enhanced: {result.metadata.get('enhanced', False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste enhanced lead researcher: {e}")
        return False


async def test_api_compatibility():
    """Testa compatibilidade com API atual"""
    logger.info("🧪 Testando compatibilidade com API...")
    
    try:
        from researcher.enhanced.enhanced_integration import EnhancedAPIAdapter
        
        # Criar sistema e adapter
        mock_rag = MockRAGSystem()
        enhanced_system = EnhancedRAGSystem(mock_rag)
        api_adapter = EnhancedAPIAdapter(enhanced_system)
        
        query = "Como implementar um sistema RAG?"
        
        # Testar processamento de query para API
        result = await api_adapter.process_research_query(query, use_enhanced=True)
        
        logger.info(f"✅ API adapter funcionando:")
        logger.info(f"   Success: {result['success']}")
        logger.info(f"   Query: {result['query']}")
        logger.info(f"   Agent ID: {result['agent_id']}")
        logger.info(f"   Status: {result['status']}")
        logger.info(f"   Enhanced: {result.get('enhanced', False)}")
        logger.info(f"   Especialistas: {result.get('specialists_used', [])}")
        
        # Testar fallback
        logger.info("🔄 Testando fallback...")
        fallback_result = await api_adapter.process_research_query(query, use_enhanced=False)
        
        logger.info(f"   Fallback success: {fallback_result['success']}")
        logger.info(f"   Fallback enhanced: {fallback_result.get('enhanced', True)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de compatibilidade API: {e}")
        return False


def test_model_validation():
    """Testa validações dos modelos Pydantic"""
    logger.info("🧪 Testando validações dos modelos...")
    
    try:
        from researcher.enhanced.enhanced_models import (
            RAGSubagentTaskSpec, SpecialistType, QueryComplexity, 
            RAGApproach, RAGSearchStrategy
        )
        
        # Testar criação de task spec
        task_spec = RAGSubagentTaskSpec(
            specialist_type=SpecialistType.CONCEPTUAL,
            focus_areas=["definitions", "concepts"],
            search_keywords=["machine learning", "AI"],
            semantic_context="Understanding basic ML concepts",
            expected_findings="Clear definitions and explanations",
            similarity_threshold=0.7,
            max_candidates=5
        )
        
        logger.info(f"✅ TaskSpec criado: {task_spec.specialist_type.value}")
        
        # Testar approach
        approach = RAGApproach(
            complexity=QueryComplexity.MODERATE,
            strategy=RAGSearchStrategy.SEMANTIC_EXPANSION,
            estimated_subagents=2,
            approach_steps=["Step 1", "Step 2"],
            key_aspects=["concept", "application"],
            document_types_needed=["definitions"],
            reranking_strategy="semantic relevance",
            synthesis_approach="enhanced answer"
        )
        
        logger.info(f"✅ Approach criado: {approach.complexity.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de validação: {e}")
        return False


async def run_all_tests():
    """Executa todos os testes"""
    logger.info("🚀 Iniciando testes do sistema enhanced...")
    
    results = {}
    
    # Testes sequenciais
    tests = [
        ("Model Validation", test_model_validation),
        ("Enhanced Decomposition", test_enhanced_decomposition),
        ("Enhanced System", test_enhanced_system),
        ("Enhanced Lead Researcher", test_enhanced_lead_researcher),
        ("API Compatibility", test_api_compatibility)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Executando: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            results[test_name] = success
            
            if success:
                logger.info(f"✅ {test_name}: PASSOU")
            else:
                logger.error(f"❌ {test_name}: FALHOU")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERRO - {e}")
            results[test_name] = False
    
    # Resumo dos resultados
    logger.info(f"\n{'='*50}")
    logger.info("RESUMO DOS TESTES")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nResultado final: {passed}/{total} testes passaram")
    
    if passed == total:
        logger.info("🎉 Todos os testes passaram! Sistema enhanced pronto para integração.")
    else:
        logger.warning(f"⚠️ {total - passed} testes falharam. Revisar antes da integração.")
    
    return passed == total


if __name__ == "__main__":
    # Verificar variáveis de ambiente
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Executar testes
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Erro fatal nos testes: {e}")
        sys.exit(1)