#!/usr/bin/env python3
"""
Sistema de Síntese Coordenada RAG Enhanced
Baseado no sistema original mas adaptado para síntese de resultados RAG
"""

import time
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .enhanced_models import (
    RAGDecomposition, SubagentResult, SynthesisInstructions, 
    EnhancedRAGResult, QueryComplexity, SpecialistType
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

# Configuração
config = SystemConfig()
logger = logging.getLogger(__name__)


class ConflictResolver:
    """Resolve conflitos entre diferentes especialistas"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
    
    def identify_conflicts(self, subagent_results: List[SubagentResult]) -> List[Dict[str, Any]]:
        """Identifica conflitos entre resultados de especialistas"""
        
        conflicts = []
        
        # Comparar informações entre especialistas
        for i, result1 in enumerate(subagent_results):
            for j, result2 in enumerate(subagent_results[i+1:], i+1):
                conflict = self._check_conflict_between_results(result1, result2)
                if conflict:
                    conflicts.append({
                        'specialist1': result1.specialist_type,
                        'specialist2': result2.specialist_type,
                        'conflict_type': conflict['type'],
                        'details': conflict['details'],
                        'confidence1': result1.confidence_level,
                        'confidence2': result2.confidence_level
                    })
        
        return conflicts
    
    def _check_conflict_between_results(
        self, 
        result1: SubagentResult, 
        result2: SubagentResult
    ) -> Optional[Dict[str, str]]:
        """Verifica conflito entre dois resultados"""
        
        try:
            # Usar LLM para detectar conflitos semânticos
            prompt = f"""
Analise estes dois trechos de informação sobre o mesmo tópico e identifique conflitos:

ESPECIALISTA {result1.specialist_type.value.upper()}:
{result1.extracted_information[:800]}

ESPECIALISTA {result2.specialist_type.value.upper()}:
{result2.extracted_information[:800]}

Existe algum conflito factual ou contradição entre as informações?

Se SIM, responda no formato:
CONFLICT_TYPE: [factual/emphasis/perspective]
DETAILS: [descrição breve do conflito]

Se NÃO, responda apenas: NO_CONFLICT
"""
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.rag.max_tokens_query_transform,
                temperature=config.rag.temperature
            )
            
            result = response.choices[0].message.content.strip()
            
            if "NO_CONFLICT" in result:
                return None
            
            # Parsear resultado
            lines = result.split('\n')
            conflict_type = "unknown"
            details = "Conflito detectado"
            
            for line in lines:
                if line.startswith("CONFLICT_TYPE:"):
                    conflict_type = line.split(": ")[1].strip()
                elif line.startswith("DETAILS:"):
                    details = line.split(": ")[1].strip()
            
            return {
                'type': conflict_type,
                'details': details
            }
            
        except Exception as e:
            logger.warning(f"Erro na detecção de conflitos: {e}")
            return None
    
    def resolve_conflicts(
        self, 
        conflicts: List[Dict[str, Any]], 
        subagent_results: List[SubagentResult]
    ) -> Dict[str, str]:
        """Resolve conflitos identificados"""
        
        resolutions = {}
        
        for conflict in conflicts:
            resolution = self._resolve_single_conflict(conflict, subagent_results)
            conflict_key = f"{conflict['specialist1']}_{conflict['specialist2']}"
            resolutions[conflict_key] = resolution
        
        return resolutions
    
    def _resolve_single_conflict(
        self, 
        conflict: Dict[str, Any], 
        subagent_results: List[SubagentResult]
    ) -> str:
        """Resolve um conflito específico"""
        
        # Encontrar os resultados conflitantes
        result1 = next(r for r in subagent_results if r.specialist_type == conflict['specialist1'])
        result2 = next(r for r in subagent_results if r.specialist_type == conflict['specialist2'])
        
        # Estratégia de resolução baseada na confiança
        if abs(result1.confidence_level - result2.confidence_level) > 0.2:
            # Priorizar o de maior confiança
            if result1.confidence_level > result2.confidence_level:
                return f"Priorizado {result1.specialist_type} devido à maior confiança ({result1.confidence_level:.2f})"
            else:
                return f"Priorizado {result2.specialist_type} devido à maior confiança ({result2.confidence_level:.2f})"
        
        # Se confiança similar, resolver baseado no tipo de conflito
        if conflict['conflict_type'] == 'factual':
            return "Conflito factual - ambas perspectivas apresentadas com ressalvas"
        elif conflict['conflict_type'] == 'emphasis':
            return "Diferença de ênfase - informações complementares integradas"
        elif conflict['conflict_type'] == 'perspective':
            return "Perspectivas diferentes - apresentadas como visões alternativas"
        else:
            return "Conflito resolvido por integração balanceada"


class QualityAssessor:
    """Avalia qualidade da síntese final"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
    
    def assess_synthesis_quality(
        self, 
        original_query: str,
        final_answer: str,
        subagent_results: List[SubagentResult],
        decomposition: RAGDecomposition
    ) -> Dict[str, float]:
        """Avalia qualidade da síntese final"""
        
        metrics = {}
        
        # 1. Relevância à query original
        metrics['query_relevance'] = self._assess_query_relevance(original_query, final_answer)
        
        # 2. Completude da resposta
        metrics['completeness'] = self._assess_completeness(
            final_answer, decomposition.approach.key_aspects
        )
        
        # 3. Coerência interna
        metrics['coherence'] = self._assess_coherence(final_answer)
        
        # 4. Uso adequado das fontes
        metrics['source_utilization'] = self._assess_source_utilization(
            subagent_results, final_answer
        )
        
        # 5. Clareza e legibilidade
        metrics['clarity'] = self._assess_clarity(final_answer)
        
        # 6. Score geral
        metrics['overall_quality'] = sum(metrics.values()) / len(metrics)
        
        return metrics
    
    def _assess_query_relevance(self, query: str, answer: str) -> float:
        """Avalia relevância da resposta à query"""
        
        try:
            prompt = f"""
Avalie quão bem esta resposta atende à pergunta original:

PERGUNTA: "{query}"

RESPOSTA:
{answer[:1500]}...

Dê uma nota de 0.0 a 1.0 para relevância:
- 1.0: Responde completamente e diretamente
- 0.8: Responde bem com pequenos desvios
- 0.6: Responde parcialmente
- 0.4: Resposta tangencial
- 0.2: Pouco relevante
- 0.0: Irrelevante

Responda apenas com o número (ex: 0.8)
"""
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.rag.max_tokens_score,
                temperature=config.rag.temperature
            )
            
            score_text = response.choices[0].message.content.strip()
            return float(score_text)
            
        except Exception as e:
            logger.warning(f"Erro na avaliação de relevância: {e}")
            return 0.7  # Score neutro
    
    def _assess_completeness(self, answer: str, key_aspects: List[str]) -> float:
        """Avalia completude baseada nos aspectos-chave"""
        
        if not key_aspects:
            return 1.0
        
        covered_aspects = 0
        answer_lower = answer.lower()
        
        for aspect in key_aspects:
            aspect_keywords = aspect.lower().split()
            # Verifica se pelo menos 50% das palavras do aspecto aparecem na resposta
            matches = sum(1 for keyword in aspect_keywords if keyword in answer_lower)
            if matches >= len(aspect_keywords) * 0.5:
                covered_aspects += 1
        
        return covered_aspects / len(key_aspects)
    
    def _assess_coherence(self, answer: str) -> float:
        """Avalia coerência interna da resposta"""
        
        try:
            prompt = f"""
Avalie a coerência interna desta resposta:

{answer[:1200]}...

Considere:
- Fluxo lógico das ideias
- Consistência das informações
- Transições entre parágrafos
- Ausência de contradições

Nota de 0.0 a 1.0:
- 1.0: Perfeitamente coerente
- 0.8: Muito coerente
- 0.6: Moderadamente coerente
- 0.4: Algumas inconsistências
- 0.2: Pouco coerente
- 0.0: Incoerente

Responda apenas com o número.
"""
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.rag.max_tokens_score,
                temperature=config.rag.temperature
            )
            
            return float(response.choices[0].message.content.strip())
            
        except Exception as e:
            logger.warning(f"Erro na avaliação de coerência: {e}")
            return 0.7
    
    def _assess_source_utilization(
        self, 
        subagent_results: List[SubagentResult], 
        final_answer: str
    ) -> float:
        """Avalia se as fontes foram bem utilizadas"""
        
        total_sources = sum(len(result.sources_used) for result in subagent_results)
        if total_sources == 0:
            return 0.0
        
        # Verificar se informações dos especialistas aparecem na síntese
        utilized_specialists = 0
        answer_lower = final_answer.lower()
        
        for result in subagent_results:
            # Verificar se palavras-chave das descobertas aparecem na síntese
            info_keywords = result.extracted_information.lower().split()[:20]  # Primeiras 20 palavras
            matches = sum(1 for keyword in info_keywords if len(keyword) > 3 and keyword in answer_lower)
            
            if matches >= 3:  # Pelo menos 3 palavras-chave
                utilized_specialists += 1
        
        return utilized_specialists / len(subagent_results) if subagent_results else 0.0
    
    def _assess_clarity(self, answer: str) -> float:
        """Avalia clareza e legibilidade"""
        
        # Métricas objetivas de clareza
        sentences = answer.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Penalizar frases muito longas ou muito curtas
        if avg_sentence_length < 8:
            length_score = 0.6  # Muito curtas
        elif avg_sentence_length > 25:
            length_score = 0.7  # Muito longas
        else:
            length_score = 1.0  # Adequadas
        
        # Verificar estrutura (presença de conectivos, organização)
        connectives = ['therefore', 'however', 'moreover', 'furthermore', 'additionally', 
                      'portanto', 'entretanto', 'além disso', 'por outro lado']
        
        answer_lower = answer.lower()
        connective_count = sum(1 for conn in connectives if conn in answer_lower)
        structure_score = min(1.0, connective_count / max(1, len(sentences) // 3))
        
        return (length_score + structure_score) / 2


class EnhancedSynthesizer:
    """Sintetizador enhanced que integra resultados de especialistas"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.conflict_resolver = ConflictResolver(openai_client)
        self.quality_assessor = QualityAssessor(openai_client)
    
    def synthesize_results(
        self, 
        decomposition: RAGDecomposition,
        subagent_results: List[SubagentResult]
    ) -> EnhancedRAGResult:
        """Síntese principal dos resultados"""
        
        logger.info(f"Sintetizando resultados de {len(subagent_results)} especialistas")
        start_time = time.time()
        
        # 1. Identificar e resolver conflitos
        conflicts = self.conflict_resolver.identify_conflicts(subagent_results)
        conflict_resolutions = self.conflict_resolver.resolve_conflicts(conflicts, subagent_results)
        
        # 2. Gerar instruções específicas de síntese
        synthesis_instructions = self._generate_synthesis_instructions(
            decomposition, subagent_results, conflict_resolutions
        )
        
        # 3. Executar síntese coordenada
        final_answer = self._execute_coordinated_synthesis(
            decomposition.original_query,
            subagent_results,
            synthesis_instructions,
            conflict_resolutions
        )
        
        # 4. Calcular score de confiança
        confidence_score = self._calculate_overall_confidence(subagent_results)
        
        # 5. Preparar fontes citadas
        sources_cited = self._prepare_cited_sources(subagent_results)
        
        # 6. Gerar trace de raciocínio
        reasoning_trace = self._generate_reasoning_trace(
            decomposition, subagent_results, conflicts
        )
        
        # 7. Avaliar qualidade
        quality_metrics = self.quality_assessor.assess_synthesis_quality(
            decomposition.original_query, final_answer, subagent_results, decomposition
        )
        
        processing_time = time.time() - start_time
        
        return EnhancedRAGResult(
            original_query=decomposition.original_query,
            decomposition_used=decomposition,
            subagent_results=subagent_results,
            synthesis_instructions=synthesis_instructions,
            final_answer=final_answer,
            confidence_score=confidence_score,
            sources_cited=sources_cited,
            total_processing_time=processing_time,
            quality_metrics=quality_metrics,
            reasoning_trace=reasoning_trace
        )
    
    def _generate_synthesis_instructions(
        self,
        decomposition: RAGDecomposition,
        subagent_results: List[SubagentResult],
        conflict_resolutions: Dict[str, str]
    ) -> SynthesisInstructions:
        """Gera instruções específicas baseadas nos resultados"""
        
        # Determinar aspectos prioritários baseados na confiança
        specialist_confidences = {
            result.specialist_type: result.confidence_level 
            for result in subagent_results
        }
        
        priority_aspects = []
        for specialist, confidence in sorted(specialist_confidences.items(), key=lambda x: x[1], reverse=True):
            priority_aspects.append(f"{specialist.value} (confiança: {confidence:.2f})")
        
        # Estratégia de integração baseada na complexidade
        complexity = decomposition.approach.complexity
        if complexity == QueryComplexity.SIMPLE:
            integration_strategy = "Síntese direta do especialista principal"
        elif complexity == QueryComplexity.MODERATE:
            integration_strategy = "Integração sequencial com ênfase no especialista primário"
        elif complexity == QueryComplexity.COMPLEX:
            integration_strategy = "Integração balanceada de múltiplas perspectivas"
        else:  # VERY_COMPLEX
            integration_strategy = "Síntese estruturada com análise crítica e contextualização"
        
        # Resolução de conflitos
        conflict_resolution = "Integração harmoniosa - sem conflitos detectados"
        if conflict_resolutions:
            conflict_resolution = f"Resolução de {len(conflict_resolutions)} conflitos: " + \
                               "; ".join(conflict_resolutions.values())
        
        return SynthesisInstructions(
            synthesis_approach=decomposition.approach.synthesis_approach,
            priority_aspects=priority_aspects,
            integration_strategy=integration_strategy,
            conflict_resolution=conflict_resolution,
            output_format="Resposta estruturada com citações específicas",
            quality_checks=decomposition.quality_criteria,
            citation_requirements="Citar documentos e páginas específicas para informações factuais"
        )
    
    def _execute_coordinated_synthesis(
        self,
        original_query: str,
        subagent_results: List[SubagentResult],
        instructions: SynthesisInstructions,
        conflict_resolutions: Dict[str, str]
    ) -> str:
        """Executa síntese coordenada usando LLM"""
        
        # Preparar informações dos especialistas
        specialist_info = []
        for result in subagent_results:
            specialist_info.append(f"""
ESPECIALISTA {result.specialist_type.value.upper()}:
Confiança: {result.confidence_level:.2f}
Informações: {result.extracted_information}
Fontes: {len(result.sources_used)} documentos
""")
        
        # Preparar contexto de conflitos
        conflict_context = ""
        if conflict_resolutions:
            conflict_context = f"""
RESOLUÇÃO DE CONFLITOS:
{' | '.join(conflict_resolutions.values())}
"""
        
        prompt = f"""
Sintetize uma resposta abrangente para esta pergunta usando as informações dos especialistas:

PERGUNTA ORIGINAL: "{original_query}"

INSTRUÇÕES DE SÍNTESE:
- Abordagem: {instructions.synthesis_approach}
- Estratégia: {instructions.integration_strategy}
- Formato: {instructions.output_format}
- Citações: {instructions.citation_requirements}

INFORMAÇÕES DOS ESPECIALISTAS:
{''.join(specialist_info)}

{conflict_context}

DIRETRIZES:
1. Responda diretamente à pergunta original
2. Integre informações de todos os especialistas de forma coerente
3. Priorize informações de especialistas com maior confiança
4. Cite documentos específicos para informações factuais
5. Mantenha clareza e objetividade
6. Se houver limitações, mencione-as adequadamente

RESPOSTA SINTETIZADA:
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=config.multiagent.model,  # Usar modelo coordinator
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.rag.max_tokens_answer,
                temperature=config.rag.temperature_synthesis
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Erro na síntese coordenada: {e}")
            # Fallback: concatenar informações dos especialistas
            return self._fallback_synthesis(original_query, subagent_results)
    
    def _fallback_synthesis(
        self, 
        query: str, 
        subagent_results: List[SubagentResult]
    ) -> str:
        """Síntese de fallback em caso de erro"""
        
        answer_parts = [f"Em resposta à pergunta: {query}\n"]
        
        for result in subagent_results:
            specialist_name = result.specialist_type.value.replace('_', ' ').title()
            answer_parts.append(f"\n{specialist_name}:\n{result.extracted_information}")
        
        answer_parts.append(f"\nInformações baseadas em {sum(len(r.sources_used) for r in subagent_results)} fontes documentais.")
        
        return "".join(answer_parts)
    
    def _calculate_overall_confidence(self, subagent_results: List[SubagentResult]) -> float:
        """Calcula confiança geral baseada nos resultados"""
        
        if not subagent_results:
            return 0.0
        
        # Média ponderada baseada no número de fontes
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for result in subagent_results:
            weight = max(1, len(result.sources_used))  # Peso baseado no número de fontes
            total_weighted_confidence += result.confidence_level * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _prepare_cited_sources(self, subagent_results: List[SubagentResult]) -> List[Dict[str, Any]]:
        """Prepara lista consolidada de fontes citadas"""
        
        all_sources = []
        seen_sources = set()
        
        for result in subagent_results:
            for source in result.sources_used:
                source_key = f"{source.get('document_id', '')}_{source.get('page_number', 0)}"
                
                if source_key not in seen_sources:
                    all_sources.append({
                        'document_id': source.get('document_id', 'unknown'),
                        'page_number': source.get('page_number', 0),
                        'specialist_type': result.specialist_type.value,
                        'relevance_level': source.get('relevance_level', 'unknown'),
                        'quality_score': source.get('quality_score', 0.0)
                    })
                    seen_sources.add(source_key)
        
        # Ordenar por qualidade decrescente
        all_sources.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return all_sources
    
    def _generate_reasoning_trace(
        self,
        decomposition: RAGDecomposition,
        subagent_results: List[SubagentResult],
        conflicts: List[Dict[str, Any]]
    ) -> List[str]:
        """Gera trace do raciocínio aplicado"""
        
        trace = []
        
        # 1. Decomposição inicial
        trace.append(f"Decomposição: Query '{decomposition.original_query}' → Complexidade {decomposition.approach.complexity.value}")
        trace.append(f"Estratégia: {decomposition.approach.strategy.value} com {len(subagent_results)} especialistas")
        
        # 2. Execução dos especialistas
        for result in subagent_results:
            iterations_info = f" ({result.iterations_performed} iterações)" if result.iterations_performed > 1 else ""
            trace.append(f"Especialista {result.specialist_type.value}: {len(result.sources_used)} fontes, confiança {result.confidence_level:.2f}{iterations_info}")
        
        # 3. Resolução de conflitos
        if conflicts:
            trace.append(f"Conflitos identificados: {len(conflicts)} - todos resolvidos")
        else:
            trace.append("Nenhum conflito detectado entre especialistas")
        
        # 4. Síntese final
        total_sources = sum(len(result.sources_used) for result in subagent_results)
        trace.append(f"Síntese final: Integração de informações de {total_sources} fontes documentais")
        
        return trace


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['ConflictResolver', 'QualityAssessor', 'EnhancedSynthesizer']