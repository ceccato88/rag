#!/usr/bin/env python3
"""
Sistema de Decomposição RAG Enhanced
Baseado no sistema original mas adaptado para busca vetorial + reranking
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from .enhanced_models import (
    QueryComplexity, RAGSearchStrategy, SpecialistType,
    RAGSubagentTaskSpec, RAGApproach, RAGDecomposition,
    SynthesisInstructions, RAGTaskFactory
)

# Import config do sistema principal
try:
    from src.core.config import SystemConfig
except ImportError:
    import sys
    from pathlib import Path
    # Adicionar caminho relativo apenas se necessário
    sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
    from src.core.config import SystemConfig

# Import configurações enhanced unificadas
from .enhanced_unified_config import get_config_for_task, unified_config
from .enhanced_config import SPECIALIST_OPTIMIZATIONS  # Manter para seções preferidas

# Configuração
config = SystemConfig()
logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analisa queries para determinar complexidade e abordagem (adaptado do sistema original)"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        
        # Padrões para classificação rápida (sem LLM)
        self.complexity_patterns = {
            QueryComplexity.SIMPLE: [
                "what is", "define", "meaning of", "explain",
                "o que é", "definição de", "significado"
            ],
            QueryComplexity.MODERATE: [
                "how does", "why", "advantages", "disadvantages",
                "como funciona", "por que", "vantagens", "desvantagens"
            ],
            QueryComplexity.COMPLEX: [
                "compare", "analyze", "evaluate", "assess",
                "comparar", "analisar", "avaliar", "assessment"
            ],
            QueryComplexity.VERY_COMPLEX: [
                "comprehensive analysis", "detailed comparison", "in-depth study",
                "análise abrangente", "comparação detalhada", "estudo aprofundado"
            ]
        }
        
        self.specialist_patterns = {
            SpecialistType.CONCEPTUAL: [
                "what is", "define", "concept", "theory", "principle",
                "o que é", "definir", "conceito", "teoria", "princípio"
            ],
            SpecialistType.COMPARATIVE: [
                "compare", "versus", "vs", "difference", "alternative",
                "comparar", "diferença", "alternativa"
            ],
            SpecialistType.TECHNICAL: [
                "how to", "implement", "architecture", "algorithm", "technical",
                "como implementar", "arquitetura", "algoritmo", "técnico"
            ],
            SpecialistType.EXAMPLES: [
                "example", "case study", "use case", "application",
                "exemplo", "caso de uso", "aplicação"
            ]
        }
    
    def analyze_complexity(self, query: str) -> QueryComplexity:
        """Determina complexidade da query"""
        query_lower = query.lower()
        
        # Classificação determinística primeiro (mais rápida)
        for complexity, patterns in self.complexity_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                logger.debug(f"Complexidade determinística: {complexity} para '{query[:50]}...'")
                return complexity
        
        # Análise com LLM para casos ambíguos
        return self._analyze_complexity_with_llm(query)
    
    def _analyze_complexity_with_llm(self, query: str) -> QueryComplexity:
        """Analisa complexidade usando LLM"""
        try:
            prompt = f"""
Analise a complexidade desta query para pesquisa em documentos:

QUERY: "{query}"

Classifique como:
- SIMPLE: Pergunta direta sobre definição/conceito
- MODERATE: Pergunta sobre funcionamento/processo  
- COMPLEX: Comparação/análise de múltiplos aspectos
- VERY_COMPLEX: Análise abrangente/múltiplas perspectivas

Responda apenas com: SIMPLE, MODERATE, COMPLEX ou VERY_COMPLEX
"""
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0
            )
            
            result = response.choices[0].message.content.strip().upper()
            return QueryComplexity(result.lower())
            
        except Exception as e:
            logger.warning(f"Erro na análise LLM de complexidade: {e}")
            return QueryComplexity.MODERATE  # Fallback seguro
    
    def determine_specialists(self, query: str, complexity: QueryComplexity) -> List[SpecialistType]:
        """Determina especialistas necessários baseado na query"""
        query_lower = query.lower()
        specialists = []
        
        # Determinação baseada em padrões
        for specialist, patterns in self.specialist_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                specialists.append(specialist)
        
        # Se nenhum padrão específico, usar GENERAL
        if not specialists:
            specialists.append(SpecialistType.GENERAL)
        
        # Ajustar baseado na complexidade
        if complexity == QueryComplexity.SIMPLE and len(specialists) > 1:
            # Para queries simples, usar apenas o primeiro especialista
            specialists = specialists[:1]
        elif complexity == QueryComplexity.VERY_COMPLEX and len(specialists) == 1:
            # Para queries muito complexas, adicionar especialista complementar
            if specialists[0] != SpecialistType.GENERAL:
                specialists.append(SpecialistType.GENERAL)
        
        return specialists[:3]  # Máximo 3 especialistas
    
    def extract_key_aspects(self, query: str) -> List[str]:
        """Extrai aspectos-chave da query usando LLM"""
        try:
            prompt = f"""
Extraia os aspectos-chave desta query de pesquisa em documentos:

QUERY: "{query}"

Liste os 3-5 aspectos mais importantes que devem ser investigados.
Cada aspecto deve ser específico e focado em informações que podem ser encontradas em documentos.

Formato: lista simples, um aspecto por linha.
"""
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            aspects_text = response.choices[0].message.content.strip()
            aspects = [aspect.strip("- •") for aspect in aspects_text.split('\n') if aspect.strip()]
            
            return aspects[:5]  # Máximo 5 aspectos
            
        except Exception as e:
            logger.warning(f"Erro na extração de aspectos: {e}")
            return [query]  # Fallback: usar a própria query


class RAGDecomposer:
    """Decomposição estruturada para pesquisa RAG (baseado no sistema original)"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.analyzer = QueryAnalyzer(openai_client)
        
        # Estratégias baseadas na complexidade
        self.strategy_mapping = {
            QueryComplexity.SIMPLE: RAGSearchStrategy.DIRECT_SEARCH,
            QueryComplexity.MODERATE: RAGSearchStrategy.SEMANTIC_EXPANSION,
            QueryComplexity.COMPLEX: RAGSearchStrategy.MULTI_PERSPECTIVE,
            QueryComplexity.VERY_COMPLEX: RAGSearchStrategy.COMPREHENSIVE_COVERAGE
        }
    
    def decompose(self, query: str) -> RAGDecomposition:
        """Decomposição principal da query"""
        logger.info(f"Iniciando decomposição RAG para: '{query[:50]}...'")
        
        # 1. Análise da complexidade
        complexity = self.analyzer.analyze_complexity(query)
        logger.debug(f"Complexidade determinada: {complexity}")
        
        # 2. Refinamento da query
        refined_query = self._refine_query(query)
        logger.debug(f"Query refinada: '{refined_query}'")
        
        # 3. Determinação da abordagem
        approach = self._determine_approach(query, refined_query, complexity)
        
        # 4. Criação das tarefas dos subagentes
        subagent_tasks = self._create_subagent_tasks(query, refined_query, approach)
        
        # 5. Geração de instruções de síntese
        synthesis_instructions = self._generate_synthesis_instructions(query, approach, subagent_tasks)
        
        # 6. Definição de critérios de qualidade
        quality_criteria = self._define_quality_criteria(complexity)
        
        decomposition = RAGDecomposition(
            original_query=query,
            refined_query=refined_query,
            approach=approach,
            subagent_tasks=subagent_tasks,
            global_context=f"Comprehensive research about: {query}",
            synthesis_instructions=synthesis_instructions,
            quality_criteria=quality_criteria,
            fallback_strategy=self._define_fallback_strategy(complexity)
        )
        
        logger.info(f"Decomposição completa: {len(subagent_tasks)} tarefas, estratégia {approach.strategy}")
        return decomposition
    
    def _refine_query(self, query: str) -> str:
        """Refina a query para melhor busca vetorial"""
        try:
            prompt = f"""
Refine esta query para otimizar a busca vetorial em documentos:

QUERY ORIGINAL: "{query}"

Objetivos do refinamento:
1. Adicionar contexto semântico útil
2. Incluir sinônimos e termos relacionados
3. Manter o foco principal da pergunta
4. Otimizar para similarity search

Retorne apenas a query refinada, sem explicações.
"""
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            refined = response.choices[0].message.content.strip()
            return refined if refined else query
            
        except Exception as e:
            logger.warning(f"Erro no refinamento da query: {e}")
            return query
    
    def _determine_approach(self, original_query: str, refined_query: str, complexity: QueryComplexity) -> RAGApproach:
        """Determina abordagem completa da pesquisa"""
        
        # Estratégia baseada na complexidade
        strategy = self.strategy_mapping[complexity]
        
        # Número de subagentes baseado na complexidade
        subagent_counts = {
            QueryComplexity.SIMPLE: 1,
            QueryComplexity.MODERATE: 1,
            QueryComplexity.COMPLEX: 2,
            QueryComplexity.VERY_COMPLEX: 3
        }
        estimated_subagents = subagent_counts[complexity]
        
        # Especialistas necessários
        specialists = self.analyzer.determine_specialists(original_query, complexity)
        
        # Aspectos-chave
        key_aspects = self.analyzer.extract_key_aspects(original_query)
        
        # Passos da abordagem
        approach_steps = self._generate_approach_steps(strategy, specialists)
        
        # Tipos de documentos necessários
        document_types = self._determine_document_types(original_query, specialists)
        
        return RAGApproach(
            complexity=complexity,
            strategy=strategy,
            estimated_subagents=estimated_subagents,
            approach_steps=approach_steps,
            key_aspects=key_aspects,
            document_types_needed=document_types,
            reranking_strategy=self._determine_reranking_strategy(strategy),
            synthesis_approach=self._determine_synthesis_approach(complexity, specialists)
        )
    
    def _create_subagent_tasks(self, original_query: str, refined_query: str, approach: RAGApproach) -> List[RAGSubagentTaskSpec]:
        """Cria tarefas específicas para cada subagente"""
        specialists = self.analyzer.determine_specialists(original_query, approach.complexity)
        tasks = []
        
        for i, specialist in enumerate(specialists):
            # Obter configuração unificada para este especialista e complexidade
            optimized_config = get_config_for_task(
                complexity=approach.complexity.value,
                specialist_type=specialist.value
            )
            
            if approach.complexity == QueryComplexity.SIMPLE:
                task = RAGTaskFactory.create_simple_task(refined_query, specialist)
                # Aplicar configurações unificadas
                task.similarity_threshold = optimized_config['similarity_threshold']
                task.max_candidates = optimized_config['max_candidates']
            else:
                # Para queries complexas, criar tarefa específica
                focus_areas = self._determine_focus_areas(specialist, approach.key_aspects)
                keywords = self._generate_keywords(original_query, specialist, focus_areas)
                task = RAGTaskFactory.create_complex_task(
                    refined_query, specialist, focus_areas, keywords
                )
                # Aplicar configurações unificadas
                task.similarity_threshold = optimized_config['similarity_threshold']
                task.max_candidates = optimized_config['max_candidates']
            
            # Ajustar prioridade
            task.priority = "high" if i == 0 else "medium"
            
            tasks.append(task)
        
        return tasks
    
    def _determine_focus_areas(self, specialist: SpecialistType, key_aspects: List[str]) -> List[str]:
        """Determina áreas de foco específicas para cada especialista (baseado no sistema original)"""
        
        # Mapeamento 1:1: Especialista → Focus Area principal (mesmo nome)
        specialist_focus_mapping = {
            SpecialistType.CONCEPTUAL: [
                "conceptual",                   # Focus area principal (mesmo nome)
                "definitions", 
                "theoretical_background"
            ],
            SpecialistType.COMPARATIVE: [
                "comparative",                  # Focus area principal (mesmo nome)
                "alternatives", 
                "differences"
            ],
            SpecialistType.TECHNICAL: [
                "technical",                    # Focus area principal (mesmo nome)
                "architecture",
                "implementation"
            ],
            SpecialistType.EXAMPLES: [
                "examples",                     # Focus area principal (mesmo nome)
                "case_studies",
                "applications"
            ],
            SpecialistType.GENERAL: [
                "general",                      # Focus area principal (mesmo nome)
                "overview", 
                "broad_context"
            ]
        }
        
        base_focus = specialist_focus_mapping.get(specialist, ["general"])
        
        # Adicionar aspectos-chave relevantes
        relevant_aspects = []
        for aspect in key_aspects:
            aspect_lower = aspect.lower()
            if specialist == SpecialistType.TECHNICAL and any(term in aspect_lower for term in ["how", "implement", "technical", "methodology"]):
                relevant_aspects.append(aspect)
            elif specialist == SpecialistType.COMPARATIVE and any(term in aspect_lower for term in ["compare", "versus", "difference", "analysis"]):
                relevant_aspects.append(aspect)
            elif specialist == SpecialistType.EXAMPLES and any(term in aspect_lower for term in ["example", "case", "application", "use case"]):
                relevant_aspects.append(aspect)
            elif specialist == SpecialistType.CONCEPTUAL and any(term in aspect_lower for term in ["concept", "definition", "understanding"]):
                relevant_aspects.append(aspect)
        
        return base_focus + relevant_aspects[:2]  # Foco principal + aspectos relevantes
    
    def _generate_keywords(self, query: str, specialist: SpecialistType, focus_areas: List[str]) -> List[str]:
        """Gera palavras-chave específicas para busca vetorial"""
        
        # Keywords base da query
        base_keywords = [query]
        
        # Keywords específicas do especialista
        specialist_keywords = {
            SpecialistType.CONCEPTUAL: ["definition", "concept", "theory", "meaning"],
            SpecialistType.COMPARATIVE: ["comparison", "versus", "alternative", "difference"],
            SpecialistType.TECHNICAL: ["implementation", "technical", "architecture", "method"],
            SpecialistType.EXAMPLES: ["example", "case study", "application", "use case"],
            SpecialistType.GENERAL: ["overview", "introduction", "general"]
        }
        
        keywords = base_keywords + specialist_keywords.get(specialist, [])
        
        # Adicionar variações das focus areas
        for focus in focus_areas:
            if "_" in focus:
                keywords.append(focus.replace("_", " "))
            keywords.append(focus)
        
        return list(set(keywords))[:10]  # Máximo 10 keywords únicas
    
    def _generate_approach_steps(self, strategy: RAGSearchStrategy, specialists: List[SpecialistType]) -> List[str]:
        """Gera passos específicos da abordagem"""
        
        base_steps = [
            "1. Análise inicial da query e refinamento semântico",
            "2. Busca vetorial inicial com embeddings otimizados",
            "3. Reranking dos candidatos mais relevantes"
        ]
        
        if strategy == RAGSearchStrategy.ITERATIVE_REFINEMENT:
            base_steps.extend([
                "4. Avaliação inicial dos resultados",
                "5. Refinamento iterativo das keywords",
                "6. Nova busca com parâmetros ajustados"
            ])
        elif strategy == RAGSearchStrategy.MULTI_PERSPECTIVE:
            base_steps.extend([
                f"4. Execução paralela com especialistas: {', '.join([s.value for s in specialists])}",
                "5. Consolidação de perspectivas múltiplas"
            ])
        elif strategy == RAGSearchStrategy.COMPREHENSIVE_COVERAGE:
            base_steps.extend([
                "4. Busca exaustiva em múltiplas dimensões semânticas",
                "5. Análise de cobertura e identificação de gaps",
                "6. Busca complementar para preencher lacunas"
            ])
        
        base_steps.append(f"{len(base_steps) + 1}. Síntese coordenada dos resultados")
        
        return base_steps
    
    def _determine_document_types(self, query: str, specialists: List[SpecialistType]) -> List[str]:
        """Determina tipos de documentos/seções mais relevantes"""
        
        # Mapeamento básico por especialista
        type_mapping = {
            SpecialistType.CONCEPTUAL: ["definitions", "introductions", "theoretical sections"],
            SpecialistType.COMPARATIVE: ["comparison tables", "analysis sections", "review papers"],
            SpecialistType.TECHNICAL: ["methodology sections", "implementation details", "technical specifications"],
            SpecialistType.EXAMPLES: ["case studies", "examples", "applications", "use cases"],
            SpecialistType.GENERAL: ["abstracts", "summaries", "overview sections"]
        }
        
        document_types = []
        for specialist in specialists:
            document_types.extend(type_mapping.get(specialist, []))
        
        return list(set(document_types))
    
    def _determine_reranking_strategy(self, strategy: RAGSearchStrategy) -> str:
        """Determina estratégia específica de reranking"""
        
        reranking_strategies = {
            RAGSearchStrategy.DIRECT_SEARCH: "Simple similarity-based reranking",
            RAGSearchStrategy.SEMANTIC_EXPANSION: "Semantic relevance + keyword matching",
            RAGSearchStrategy.ITERATIVE_REFINEMENT: "Progressive relevance refinement",
            RAGSearchStrategy.MULTI_PERSPECTIVE: "Multi-perspective relevance scoring",
            RAGSearchStrategy.COMPREHENSIVE_COVERAGE: "Coverage-optimized reranking",
            RAGSearchStrategy.FOCUSED_DEEP_DIVE: "Deep relevance analysis"
        }
        
        return reranking_strategies.get(strategy, "Standard reranking")
    
    def _determine_synthesis_approach(self, complexity: QueryComplexity, specialists: List[SpecialistType]) -> str:
        """Determina abordagem de síntese baseada na complexidade"""
        
        if complexity == QueryComplexity.SIMPLE:
            return "Direct answer synthesis from primary specialist"
        elif complexity == QueryComplexity.MODERATE:
            return "Enhanced answer with supporting details"
        elif complexity == QueryComplexity.COMPLEX:
            return f"Multi-perspective synthesis from {len(specialists)} specialists"
        else:  # VERY_COMPLEX
            return "Comprehensive analysis with structured integration of all perspectives"
    
    def _generate_synthesis_instructions(self, query: str, approach: RAGApproach, tasks: List[RAGSubagentTaskSpec]) -> str:
        """Gera instruções específicas para síntese"""
        
        specialist_types = [task.specialist_type.value for task in tasks]
        
        instructions = f"""
INSTRUÇÕES DE SÍNTESE PARA: "{query}"

ABORDAGEM: {approach.synthesis_approach}
ESPECIALISTAS: {', '.join(specialist_types)}
COMPLEXIDADE: {approach.complexity.value}

DIRETRIZES:
1. Integrar informações de todos os especialistas de forma coerente
2. Manter foco na pergunta original do usuário
3. Destacar informações mais relevantes e confiáveis
4. Resolver conflitos priorizando fontes com maior score de similaridade
5. Incluir citações específicas dos documentos utilizados
6. Manter tom informativo e preciso

ESTRUTURA DA RESPOSTA:
- Resposta direta à pergunta principal
- Detalhes de apoio organizados por relevância
- Fontes citadas com páginas específicas
"""
        
        return instructions
    
    def _define_quality_criteria(self, complexity: QueryComplexity) -> List[str]:
        """Define critérios de qualidade baseados na complexidade"""
        
        base_criteria = [
            "Relevância direta à pergunta original",
            "Qualidade e confiabilidade das fontes",
            "Coerência na integração das informações"
        ]
        
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            base_criteria.extend([
                "Completude da cobertura dos aspectos-chave",
                "Equilíbrio entre diferentes perspectivas",
                "Identificação e resolução de conflitos"
            ])
        
        if complexity == QueryComplexity.VERY_COMPLEX:
            base_criteria.extend([
                "Análise crítica das limitações",
                "Contextualização histórica ou metodológica"
            ])
        
        return base_criteria
    
    def _define_fallback_strategy(self, complexity: QueryComplexity) -> str:
        """Define estratégia de fallback baseada na complexidade"""
        
        fallback_strategies = {
            QueryComplexity.SIMPLE: "Busca com threshold reduzido + resposta genérica",
            QueryComplexity.MODERATE: "Simplificação para busca direta + síntese básica",
            QueryComplexity.COMPLEX: "Redução para 1 especialista + foco no aspecto principal",
            QueryComplexity.VERY_COMPLEX: "Decomposição em sub-queries simples + integração sequencial"
        }
        
        return fallback_strategies.get(complexity, "Busca simplificada")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['QueryAnalyzer', 'RAGDecomposer']