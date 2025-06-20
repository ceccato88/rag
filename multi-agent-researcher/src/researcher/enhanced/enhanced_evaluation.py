#!/usr/bin/env python3
"""
Sistema de Avaliação Iterativa RAG Enhanced
Baseado no sistema original mas adaptado para busca vetorial + reranking
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from .enhanced_models import (
    RAGSubagentTaskSpec, DocumentEvaluation, RAGSearchEvaluation,
    DocumentRelevance, SubagentResult, SpecialistType
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


class DocumentAnalyzer:
    """Analisa documentos individuais para relevância e qualidade"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
    
    def evaluate_document(
        self, 
        document_content: str, 
        document_id: str,
        page_number: int,
        similarity_score: float,
        query: str,
        focus_areas: List[str],
        image_base64: str = ""
    ) -> DocumentEvaluation:
        """Avalia um documento individual"""
        
        logger.debug(f"Avaliando documento {document_id} página {page_number}")
        
        # 1. Determinar nível de relevância
        relevance_level = self._assess_relevance(document_content, query, focus_areas, similarity_score)
        
        # 2. Extrair descobertas-chave (usando texto + visão se disponível)
        key_findings = self._extract_key_findings(document_content, query, focus_areas, image_base64)
        
        # 3. Identificar áreas de cobertura
        coverage_areas = self._identify_coverage_areas(document_content, focus_areas)
        
        # 4. Calcular score de qualidade
        quality_score = self._calculate_quality_score(
            document_content, similarity_score, relevance_level
        )
        
        # 5. Gerar resumo da extração
        extraction_summary = self._generate_extraction_summary(
            document_content, key_findings, coverage_areas
        )
        
        return DocumentEvaluation(
            document_id=document_id,
            page_number=page_number,
            similarity_score=similarity_score,
            relevance_level=relevance_level,
            key_findings=key_findings,
            coverage_areas=coverage_areas,
            quality_score=quality_score,
            extraction_summary=extraction_summary
        )
    
    def _assess_relevance(self, content: str, query: str, focus_areas: List[str], similarity_score: float = 0.0) -> DocumentRelevance:
        """Avalia relevância do documento usando LLM"""
        
        try:
            focus_context = ", ".join(focus_areas) if focus_areas else "general"
            
            prompt = f"""
Avalie a relevância deste documento para a query específica:

QUERY: "{query}"
ÁREAS DE FOCO: {focus_context}

CONTEÚDO DO DOCUMENTO:
{content[:2000]}...

Classifique a relevância como:
- HIGHLY_RELEVANT: Responde diretamente à query
- RELEVANT: Contém informações úteis relacionadas
- SOMEWHAT_RELEVANT: Menciona o tópico mas não é central
- NOT_RELEVANT: Não relacionado ou irrelevante

Responda apenas com: HIGHLY_RELEVANT, RELEVANT, SOMEWHAT_RELEVANT ou NOT_RELEVANT
"""
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.rag.max_tokens_evaluation,
                temperature=config.rag.temperature_precise
            )
            
            relevance_str = response.choices[0].message.content.strip().upper()
            return DocumentRelevance(relevance_str.lower())
            
        except Exception as e:
            logger.warning(f"Erro na avaliação de relevância: {e}")
            # Fallback baseado no similarity score
            # Usar similarity_score da função
            if similarity_score > 0.8:
                return DocumentRelevance.HIGHLY_RELEVANT
            elif similarity_score > 0.6:
                return DocumentRelevance.RELEVANT
            elif similarity_score > 0.4:
                return DocumentRelevance.SOMEWHAT_RELEVANT
            else:
                return DocumentRelevance.NOT_RELEVANT
    
    def _extract_key_findings(self, content: str, query: str, focus_areas: List[str], image_base64: str = "") -> List[str]:
        """Extrai descobertas-chave do documento"""
        
        try:
            focus_context = ", ".join(focus_areas) if focus_areas else "any relevant information"
            
            prompt = f"""
Extraia as descobertas-chave deste documento que respondem à query:

QUERY: "{query}"
FOCO EM: {focus_context}

DOCUMENTO:
{content[:1500]}...

Extraia 3-5 descobertas específicas e factuais.
Cada descoberta deve ser uma frase concisa e informativa.
Foque no que é mais relevante para a query.

Formato: lista simples, uma descoberta por linha.
"""
            
            # Preparar mensagens (texto + imagem se disponível)
            messages = []
            
            if image_base64:
                # Análise multimodal: texto + imagem
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                })
            else:
                # Análise apenas de texto
                messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=config.rag.llm_model,
                messages=messages,
                max_tokens=config.rag.max_tokens_rating,
                temperature=system_config.rag.temperature
            )
            
            findings_text = response.choices[0].message.content.strip()
            findings = [finding.strip("- •") for finding in findings_text.split('\n') if finding.strip()]
            
            return findings[:5]  # Máximo 5 descobertas
            
        except Exception as e:
            logger.warning(f"Erro na extração de descobertas: {e}")
            return [f"Documento contém informações sobre: {query}"]
    
    def _identify_coverage_areas(self, content: str, focus_areas: List[str]) -> List[str]:
        """Identifica quais áreas de foco são cobertas pelo documento"""
        
        content_lower = content.lower()
        covered_areas = []
        
        for focus_area in focus_areas:
            focus_keywords = focus_area.replace("_", " ").split()
            
            # Verifica se palavras-chave do foco aparecem no conteúdo
            matches = sum(1 for keyword in focus_keywords if keyword.lower() in content_lower)
            coverage_ratio = matches / len(focus_keywords) if focus_keywords else 0
            
            if coverage_ratio >= 0.5:  # Pelo menos 50% das palavras-chave
                covered_areas.append(focus_area)
        
        return covered_areas
    
    def _calculate_quality_score(
        self, 
        content: str, 
        similarity_score: float, 
        relevance_level: DocumentRelevance
    ) -> float:
        """Calcula score de qualidade do conteúdo"""
        
        # Base score a partir da similaridade
        base_score = similarity_score
        
        # Ajuste baseado na relevância
        relevance_multipliers = {
            DocumentRelevance.HIGHLY_RELEVANT: 1.0,
            DocumentRelevance.RELEVANT: 0.8,
            DocumentRelevance.SOMEWHAT_RELEVANT: 0.6,
            DocumentRelevance.NOT_RELEVANT: 0.3
        }
        
        relevance_multiplier = relevance_multipliers.get(relevance_level, 0.5)
        
        # Ajuste baseado no comprimento do conteúdo
        content_length = len(content.strip())
        length_bonus = min(0.1, content_length / 5000)  # Até +0.1 para conteúdo longo
        
        # Score final
        quality_score = (base_score * relevance_multiplier) + length_bonus
        
        return min(1.0, max(0.0, quality_score))  # Garantir range [0, 1]
    
    def _generate_extraction_summary(
        self, 
        content: str, 
        key_findings: List[str], 
        coverage_areas: List[str]
    ) -> str:
        """Gera resumo do que foi extraído do documento"""
        
        findings_summary = f"Encontradas {len(key_findings)} descobertas principais"
        coverage_summary = f"Cobre {len(coverage_areas)} áreas de foco" if coverage_areas else "Cobertura geral"
        content_summary = f"Documento com {len(content)} caracteres"
        
        return f"{findings_summary}. {coverage_summary}. {content_summary}."


class IterativeRAGEvaluator:
    """Sistema de avaliação iterativa para RAG (baseado no sistema original)"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.document_analyzer = DocumentAnalyzer(openai_client)
    
    def evaluate_search_results(
        self,
        task_spec: RAGSubagentTaskSpec,
        search_results: List[Dict[str, Any]],
        query: str
    ) -> RAGSearchEvaluation:
        """Avalia resultados de busca RAG e sugere refinamentos"""
        
        logger.info(f"Avaliando {len(search_results)} resultados para query: '{query[:50]}...'")
        
        start_time = time.time()
        
        # 1. Avaliar cada documento individualmente
        document_evaluations = []
        for result in search_results:
            doc_eval = self.document_analyzer.evaluate_document(
                document_content=result.get('content', ''),
                document_id=result.get('document_id', 'unknown'),
                page_number=result.get('page_number', 0),
                similarity_score=result.get('similarity_score', 0.0),
                query=query,
                focus_areas=task_spec.focus_areas,
                image_base64=result.get('image_base64', '')  # Passar imagem para análise multimodal
            )
            document_evaluations.append(doc_eval)
        
        # 2. Calcular score geral de relevância
        overall_relevance = self._calculate_overall_relevance(document_evaluations)
        
        # 3. Avaliar completude da cobertura
        coverage_completeness = self._assess_coverage_completeness(
            document_evaluations, task_spec.focus_areas
        )
        
        # 4. Identificar gaps
        gaps_identified = self._identify_gaps(
            document_evaluations, task_spec.focus_areas, query
        )
        
        # 5. Gerar sugestões de refinamento
        refinement_suggestions = self._generate_refinement_suggestions(
            document_evaluations, gaps_identified, task_spec
        )
        
        # 6. Determinar se informação é suficiente
        sufficient_information = self._is_information_sufficient(
            overall_relevance, coverage_completeness, gaps_identified
        )
        
        # 7. Gerar keywords para próxima iteração
        next_keywords = self._generate_next_keywords(
            gaps_identified, refinement_suggestions
        ) if not sufficient_information else []
        
        # 8. Criar orientação para síntese
        synthesis_guidance = self._create_synthesis_guidance(
            document_evaluations, overall_relevance, coverage_completeness
        )
        
        evaluation_time = time.time() - start_time
        logger.debug(f"Avaliação completa em {evaluation_time:.2f}s")
        
        return RAGSearchEvaluation(
            task_spec=task_spec,
            documents_evaluated=document_evaluations,
            overall_relevance_score=overall_relevance,
            coverage_completeness=coverage_completeness,
            gaps_identified=gaps_identified,
            refinement_suggestions=refinement_suggestions,
            sufficient_information=sufficient_information,
            next_search_keywords=next_keywords,
            synthesis_guidance=synthesis_guidance
        )
    
    def _calculate_overall_relevance(self, document_evaluations: List[DocumentEvaluation]) -> float:
        """Calcula score geral de relevância"""
        
        if not document_evaluations:
            return 0.0
        
        # Weighted average baseado na qualidade e relevância
        total_weight = 0.0
        weighted_sum = 0.0
        
        for doc_eval in document_evaluations:
            # Peso baseado na relevância
            relevance_weights = {
                DocumentRelevance.HIGHLY_RELEVANT: 1.0,
                DocumentRelevance.RELEVANT: 0.8,
                DocumentRelevance.SOMEWHAT_RELEVANT: 0.5,
                DocumentRelevance.NOT_RELEVANT: 0.1
            }
            
            weight = relevance_weights.get(doc_eval.relevance_level, 0.1)
            weighted_sum += doc_eval.quality_score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _assess_coverage_completeness(
        self, 
        document_evaluations: List[DocumentEvaluation], 
        focus_areas: List[str]
    ) -> float:
        """Avalia quão completa é a cobertura das áreas de foco"""
        
        if not focus_areas:
            return 1.0  # Se não há áreas específicas, considera completo
        
        covered_areas = set()
        for doc_eval in document_evaluations:
            covered_areas.update(doc_eval.coverage_areas)
        
        coverage_ratio = len(covered_areas) / len(focus_areas)
        return min(1.0, coverage_ratio)
    
    def _identify_gaps(
        self, 
        document_evaluations: List[DocumentEvaluation], 
        focus_areas: List[str],
        query: str
    ) -> List[str]:
        """Identifica gaps nos resultados da busca"""
        
        gaps = []
        
        # 1. Verificar áreas de foco não cobertas
        covered_areas = set()
        for doc_eval in document_evaluations:
            covered_areas.update(doc_eval.coverage_areas)
        
        uncovered_areas = set(focus_areas) - covered_areas
        for area in uncovered_areas:
            gaps.append(f"Área não coberta: {area}")
        
        # 2. Verificar qualidade geral baixa
        avg_quality = sum(doc.quality_score for doc in document_evaluations) / len(document_evaluations)
        if avg_quality < 0.5:
            gaps.append("Qualidade geral dos documentos baixa")
        
        # 3. Verificar se há documentos suficientes de alta relevância
        highly_relevant_count = sum(
            1 for doc in document_evaluations 
            if doc.relevance_level == DocumentRelevance.HIGHLY_RELEVANT
        )
        
        if highly_relevant_count == 0:
            gaps.append("Nenhum documento altamente relevante encontrado")
        elif highly_relevant_count == 1 and len(document_evaluations) > 3:
            gaps.append("Poucos documentos altamente relevantes")
        
        return gaps
    
    def _generate_refinement_suggestions(
        self, 
        document_evaluations: List[DocumentEvaluation],
        gaps_identified: List[str],
        task_spec: RAGSubagentTaskSpec
    ) -> List[str]:
        """Gera sugestões específicas para refinamento"""
        
        suggestions = []
        
        # 1. Sugestões baseadas nos gaps
        for gap in gaps_identified:
            if "Área não coberta" in gap:
                area = gap.split(": ")[1]
                suggestions.append(f"Adicionar keywords específicas para: {area}")
            elif "qualidade" in gap.lower():
                suggestions.append("Reduzir threshold de similaridade para capturar mais candidatos")
            elif "relevante" in gap.lower():
                suggestions.append("Refinar query para ser mais específica")
        
        # 2. Sugestões baseadas na distribuição de qualidade
        quality_scores = [doc.quality_score for doc in document_evaluations]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            max_quality = max(quality_scores)
            
            if max_quality - avg_quality > 0.3:
                suggestions.append("Focar em documentos similares aos de maior qualidade")
        
        # 3. Sugestões baseadas no threshold atual
        similarity_scores = [doc.similarity_score for doc in document_evaluations]
        if similarity_scores:
            min_similarity = min(similarity_scores)
            if min_similarity < task_spec.similarity_threshold - 0.1:
                suggestions.append("Aumentar threshold de similaridade para melhor qualidade")
        
        # 4. Sugestões baseadas no número de candidatos
        if len(document_evaluations) < 3:
            suggestions.append("Aumentar número máximo de candidatos")
        elif len(document_evaluations) > 8:
            suggestions.append("Reduzir número de candidatos e focar nos mais relevantes")
        
        return suggestions[:5]  # Máximo 5 sugestões
    
    def _is_information_sufficient(
        self, 
        overall_relevance: float, 
        coverage_completeness: float, 
        gaps_identified: List[str]
    ) -> bool:
        """Determina se a informação encontrada é suficiente"""
        
        # Critérios para suficiência (otimizados)
        relevance_threshold = 0.65  # Ligeiramente mais exigente
        coverage_threshold = 0.75   # Mais exigente para completude
        max_critical_gaps = 2       # Mais tolerante a gaps menores
        
        # Contar gaps críticos (não incluir sugestões de melhoria)
        critical_gaps = [gap for gap in gaps_identified if "não coberta" in gap or "relevante" in gap]
        
        is_sufficient = (
            overall_relevance >= relevance_threshold and
            coverage_completeness >= coverage_threshold and
            len(critical_gaps) <= max_critical_gaps
        )
        
        logger.debug(f"Suficiência: relevance={overall_relevance:.2f}, coverage={coverage_completeness:.2f}, gaps={len(critical_gaps)}")
        
        return is_sufficient
    
    def _generate_next_keywords(
        self, 
        gaps_identified: List[str], 
        refinement_suggestions: List[str]
    ) -> List[str]:
        """Gera keywords para próxima iteração baseado nos gaps"""
        
        next_keywords = []
        
        # Extrair áreas não cobertas para gerar keywords
        for gap in gaps_identified:
            if "Área não coberta" in gap:
                area = gap.split(": ")[1]
                # Converter área em keywords
                area_keywords = area.replace("_", " ").split()
                next_keywords.extend(area_keywords)
        
        # Adicionar variações baseadas nas sugestões
        for suggestion in refinement_suggestions:
            if "keywords específicas" in suggestion:
                # Extrair área da sugestão
                if ":" in suggestion:
                    area = suggestion.split(": ")[1]
                    next_keywords.extend(area.split())
        
        return list(set(next_keywords))[:10]  # Máximo 10 keywords únicas
    
    def _create_synthesis_guidance(
        self, 
        document_evaluations: List[DocumentEvaluation],
        overall_relevance: float,
        coverage_completeness: float
    ) -> str:
        """Cria orientação específica para síntese baseada na avaliação"""
        
        # Contar documentos por relevância
        relevance_counts = {}
        for doc in document_evaluations:
            relevance_counts[doc.relevance_level] = relevance_counts.get(doc.relevance_level, 0) + 1
        
        highly_relevant = relevance_counts.get(DocumentRelevance.HIGHLY_RELEVANT, 0)
        relevant = relevance_counts.get(DocumentRelevance.RELEVANT, 0)
        
        guidance = f"Síntese baseada em {len(document_evaluations)} documentos avaliados. "
        
        if highly_relevant > 0:
            guidance += f"Priorizar informações dos {highly_relevant} documentos altamente relevantes. "
        
        if relevant > 0:
            guidance += f"Complementar com informações dos {relevant} documentos relevantes. "
        
        if overall_relevance >= 0.8:
            guidance += "Alta confiança nos resultados - síntese direta. "
        elif overall_relevance >= 0.6:
            guidance += "Confiança moderada - verificar consistência entre fontes. "
        else:
            guidance += "Baixa confiança - mencionar limitações na resposta. "
        
        if coverage_completeness < 0.5:
            guidance += "Cobertura parcial - indicar aspectos não cobertos. "
        
        return guidance


class SubagentExecutor:
    """Executa tarefas de subagentes com avaliação iterativa"""
    
    def __init__(self, openai_client: OpenAI, rag_system):
        self.openai_client = openai_client
        self.rag_system = rag_system
        self.evaluator = IterativeRAGEvaluator(openai_client)
    
    def execute_task(
        self, 
        task_spec: RAGSubagentTaskSpec, 
        refined_query: str,
        max_iterations: int = 2  # Otimizado: 2 iterações são suficientes na maioria dos casos
    ) -> SubagentResult:
        """Executa tarefa com avaliação iterativa"""
        
        logger.info(f"Executando tarefa {task_spec.specialist_type} com {max_iterations} iterações máximas")
        
        start_time = time.time()
        iterations_performed = 0
        final_evaluation = None
        extracted_information = ""
        
        # Iterações de busca e refinamento
        for iteration in range(max_iterations):
            iterations_performed += 1
            logger.debug(f"Iteração {iteration + 1}/{max_iterations}")
            
            # 1. Executar busca RAG
            search_results = self._perform_rag_search(task_spec, refined_query)
            
            # 2. Avaliar resultados
            evaluation = self.evaluator.evaluate_search_results(
                task_spec, search_results, refined_query
            )
            
            # 3. Verificar se informação é suficiente
            if evaluation.sufficient_information or iteration == max_iterations - 1:
                final_evaluation = evaluation
                extracted_information = self._extract_final_information(evaluation)
                break
            
            # 4. Refinar para próxima iteração
            task_spec = self._refine_task_spec(task_spec, evaluation)
            logger.debug(f"Tarefa refinada para iteração {iteration + 2}")
        
        processing_time = time.time() - start_time
        
        # Calcular nível de confiança
        confidence_level = self._calculate_confidence_level(final_evaluation)
        
        # Preparar fontes utilizadas
        sources_used = self._prepare_sources(final_evaluation.documents_evaluated)
        
        return SubagentResult(
            specialist_type=task_spec.specialist_type,
            task_completed=task_spec,
            search_evaluation=final_evaluation,
            extracted_information=extracted_information,
            confidence_level=confidence_level,
            sources_used=sources_used,
            processing_time=processing_time,
            iterations_performed=iterations_performed
        )
    
    def _perform_rag_search(self, task_spec: RAGSubagentTaskSpec, query: str) -> List[Dict[str, Any]]:
        """Executa busca RAG usando configurações enhanced (SEM RERANKING)"""
        
        logger.debug(f"Buscando com {task_spec.max_candidates} candidatos diretos, threshold {task_spec.similarity_threshold}")
        
        try:
            # ETAPA 1: Gerar embedding da query
            embedding = self.rag_system.get_query_embedding(query)
            
            # ETAPA 2: Buscar candidatos com limite enhanced (DIRETO, SEM RERANKING)
            candidates = self.rag_system.search_candidates(
                embedding, 
                limit=task_spec.max_candidates  # ← Usar max_candidates do enhanced (2-5 páginas)
            )
            
            if not candidates:
                logger.warning(f"Nenhum candidato encontrado para: {query}")
                return []
            
            # ETAPA 3: Filtrar por similarity threshold enhanced
            filtered_candidates = []
            for candidate in candidates:
                similarity_score = candidate.get('similarity_score', 0.0)
                if similarity_score >= task_spec.similarity_threshold:  # ← Usar threshold enhanced
                    filtered_candidates.append(candidate)
            
            logger.debug(f"Candidatos filtrados: {len(filtered_candidates)}/{len(candidates)} (threshold: {task_spec.similarity_threshold})")
            
            # REMOVIDO: ETAPA 4 de reranking - usar diretamente os candidatos por similaridade
            enhanced_candidates = filtered_candidates[:task_spec.max_candidates]  # Garantir limite
            
            # ETAPA 4: Converter para formato de avaliação (COM MULTIMODAL: texto + imagem base64)
            search_results = []
            for i, candidate in enumerate(enhanced_candidates):
                search_results.append({
                    'document_id': candidate.get("doc_source", f"doc_{i}"),
                    'page_number': candidate.get("page_num", 0),
                    'similarity_score': candidate.get("similarity_score", 0.0),
                    'content': candidate.get("markdown_text", ""),  # Conteúdo completo para análise
                    'image_base64': candidate.get("image_base64", ""),  # Imagem para visão multimodal
                    'file_path': candidate.get("file_path", "")
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Erro na busca RAG enhanced: {e}")
            # Fallback para sistema atual
            rag_result = self.rag_system.search_and_answer(query)
            
            search_results = []
            if "selected_pages_details" in rag_result:
                for i, page_detail in enumerate(rag_result["selected_pages_details"]):
                    search_results.append({
                        'document_id': page_detail.get("document", f"doc_{i}"),
                        'page_number': page_detail.get("page_number", 0),
                        'similarity_score': page_detail.get("similarity_score", 0.0),
                        'content': rag_result.get("answer", ""),
                        'image_base64': page_detail.get("image_base64", "")  # Preservar imagem no fallback
                    })
            
            return search_results
    
    # REMOVIDO: Método _enhanced_reranking não é mais necessário
    # Sistema agora usa diretamente os candidatos por similaridade (2-5 páginas)
    
    def _extract_final_information(self, evaluation: RAGSearchEvaluation) -> str:
        """Extrai informação final baseada na avaliação"""
        
        # Coletar todas as descobertas dos documentos mais relevantes
        key_findings = []
        for doc_eval in evaluation.documents_evaluated:
            if doc_eval.relevance_level in [DocumentRelevance.HIGHLY_RELEVANT, DocumentRelevance.RELEVANT]:
                key_findings.extend(doc_eval.key_findings)
        
        # Limitar e organizar
        unique_findings = list(set(key_findings))[:10]
        
        if unique_findings:
            return ". ".join(unique_findings) + "."
        else:
            return "Informações limitadas encontradas nos documentos pesquisados."
    
    def _calculate_confidence_level(self, evaluation: RAGSearchEvaluation) -> float:
        """Calcula nível de confiança baseado na avaliação"""
        
        # Baseado em múltiplos fatores
        relevance_factor = evaluation.overall_relevance_score
        coverage_factor = evaluation.coverage_completeness
        sufficiency_factor = 1.0 if evaluation.sufficient_information else 0.5
        
        # Fator baseado na qualidade dos documentos
        quality_scores = [doc.quality_score for doc in evaluation.documents_evaluated]
        quality_factor = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Média ponderada
        confidence = (
            relevance_factor * 0.3 +
            coverage_factor * 0.2 +
            sufficiency_factor * 0.3 +
            quality_factor * 0.2
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _prepare_sources(self, document_evaluations: List[DocumentEvaluation]) -> List[Dict[str, Any]]:
        """Prepara lista de fontes utilizadas"""
        
        sources = []
        for doc_eval in document_evaluations:
            if doc_eval.relevance_level != DocumentRelevance.NOT_RELEVANT:
                sources.append({
                    "document_id": doc_eval.document_id,
                    "page_number": doc_eval.page_number,
                    "relevance_level": doc_eval.relevance_level.value,
                    "quality_score": doc_eval.quality_score,
                    "key_findings_count": len(doc_eval.key_findings)
                })
        
        return sources
    
    def _refine_task_spec(
        self, 
        task_spec: RAGSubagentTaskSpec, 
        evaluation: RAGSearchEvaluation
    ) -> RAGSubagentTaskSpec:
        """Refina especificação da tarefa baseado na avaliação"""
        
        # Criar nova task spec refinada
        refined_task = RAGSubagentTaskSpec(
            specialist_type=task_spec.specialist_type,
            focus_areas=task_spec.focus_areas.copy(),
            search_keywords=task_spec.search_keywords.copy(),
            semantic_context=task_spec.semantic_context,
            expected_findings=task_spec.expected_findings,
            similarity_threshold=task_spec.similarity_threshold,
            max_candidates=task_spec.max_candidates,
            priority=task_spec.priority,
            iterative_refinement=True  # Marcar como refinamento
        )
        
        # Aplicar refinamentos baseados nas sugestões
        for suggestion in evaluation.refinement_suggestions:
            if "threshold" in suggestion.lower() and "reduzir" in suggestion.lower():
                refined_task.similarity_threshold = max(0.3, refined_task.similarity_threshold - 0.1)
            elif "threshold" in suggestion.lower() and "aumentar" in suggestion.lower():
                refined_task.similarity_threshold = min(0.9, refined_task.similarity_threshold + 0.1)
            elif "candidatos" in suggestion.lower() and "aumentar" in suggestion.lower():
                refined_task.max_candidates = min(15, refined_task.max_candidates + 3)
            elif "candidatos" in suggestion.lower() and "reduzir" in suggestion.lower():
                refined_task.max_candidates = max(3, refined_task.max_candidates - 2)
        
        # Adicionar keywords para próxima iteração
        if evaluation.next_search_keywords:
            refined_task.search_keywords.extend(evaluation.next_search_keywords)
            refined_task.search_keywords = list(set(refined_task.search_keywords))[:15]
        
        return refined_task


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['DocumentAnalyzer', 'IterativeRAGEvaluator', 'SubagentExecutor']