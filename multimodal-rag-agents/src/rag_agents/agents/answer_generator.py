"""Multimodal answer generator agent using OpenAI for comprehensive response generation."""

import time
from typing import List, Optional, Dict, Any
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from ..agents.base import Agent, AgentContext
from ..models.rag_models import (
    RankedDocuments, ContextAnalysis, StructuredAnswer, 
    SourceCitation, DocumentCandidate
)


class MultimodalResponse(BaseModel):
    """Structured multimodal response using Instructor."""
    main_response: str
    evidence_strength: str
    key_sources: List[Dict[str, Any]]
    visual_elements_referenced: List[str]
    limitations: List[str]
    follow_up_suggestions: List[str]
    confidence_assessment: str


class AnswerGeneratorConfig(BaseModel):
    """Configuration for answer generator."""
    openai_api_key: Optional[str] = None
    model: str = "gpt-4o"
    max_tokens: int = 3000
    temperature: float = 0.2
    include_citations: bool = True
    format_markdown: bool = False


class MultimodalAnswerAgent(Agent[StructuredAnswer]):
    """Agent that generates comprehensive multimodal answers using OpenAI."""
    
    def __init__(self, config: Optional[AnswerGeneratorConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or AnswerGeneratorConfig()
        
        # Initialize OpenAI client with Instructor
        client = AsyncOpenAI(api_key=self.config.openai_api_key)
        self.client = instructor.from_openai(client)
    
    async def plan(self, context: AgentContext) -> Dict[str, Any]:
        """Plan answer generation strategy."""
        self.add_thinking("Planning multimodal answer generation")
        
        ranked_docs: RankedDocuments = context.metadata.get("ranked_documents")
        context_analysis: ContextAnalysis = context.metadata.get("context_analysis")
        response_format: str = context.metadata.get("response_format", "conversational")
        
        plan = {
            "ranked_documents": ranked_docs,
            "context_analysis": context_analysis,
            "response_format": response_format,
            "include_visual_analysis": True,
            "citation_style": "integrated",
            "partial_response": context.metadata.get("partial_response", False)
        }
        
        doc_count = len(ranked_docs.documents) if ranked_docs else 0
        self.add_thinking(f"Answer generation plan: {doc_count} documents, "
                         f"format: {response_format}")
        return plan
    
    async def execute(self, plan: Dict[str, Any]) -> StructuredAnswer:
        """Generate comprehensive multimodal answer."""
        ranked_docs: RankedDocuments = plan["ranked_documents"]
        context_analysis: ContextAnalysis = plan["context_analysis"]
        
        if not ranked_docs or not ranked_docs.documents:
            return self._create_no_context_answer()
        
        # Step 1: Generate multimodal response using OpenAI
        self.add_thinking("Generating multimodal response with OpenAI")
        response = await self._generate_multimodal_response(
            ranked_docs.documents, plan
        )
        
        # Step 2: Create source citations
        self.add_thinking("Creating source citations")
        citations = self._create_source_citations(ranked_docs.documents)
        
        # Step 3: Assess visual elements used
        visual_elements = self._identify_visual_elements(ranked_docs.documents)
        
        # Step 4: Calculate confidence scores
        multimodal_confidence = self._calculate_multimodal_confidence(
            context_analysis, ranked_docs
        )
        
        return StructuredAnswer(
            main_response=response.main_response,
            evidence_strength=response.evidence_strength,
            sources_used=citations,
            visual_elements_used=visual_elements,
            limitations=response.limitations,
            follow_up_suggestions=response.follow_up_suggestions,
            multimodal_confidence=multimodal_confidence,
            processing_metadata={
                "total_documents_used": len(ranked_docs.documents),
                "visual_analysis_included": plan["include_visual_analysis"],
                "response_format": plan["response_format"],
                "generation_model": self.config.model
            }
        )
    
    async def _generate_multimodal_response(
        self, 
        documents: List[DocumentCandidate],
        plan: Dict[str, Any]
    ) -> MultimodalResponse:
        """Generate response using OpenAI with multimodal content."""
        
        # Prepare multimodal content for OpenAI
        content = []
        
        # Add instruction text
        instruction = self._create_generation_instruction(plan)
        content.append({"type": "text", "text": instruction})
        
        # Add documents with text and images
        for i, doc in enumerate(documents, 1):
            # Add text content
            text_block = f"""
=== DOCUMENT {i} - {doc.doc_source.upper()} (PAGE {doc.page_num}) ===
Similarity Score: {doc.similarity_score:.3f}
Content: {doc.markdown_text}
"""
            content.append({"type": "text", "text": text_block})
            
            # Add image if available
            from .retriever import MultimodalRetrieverAgent
            image_b64 = MultimodalRetrieverAgent.encode_image_to_base64(doc.file_path)
            if image_b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                response_model=MultimodalResponse,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                max_retries=2
            )
            
            return response
            
        except Exception as e:
            self.add_thinking(f"Multimodal response generation failed: {e}")
            return self._create_fallback_response(documents)
    
    def _create_generation_instruction(self, plan: Dict[str, Any]) -> str:
        """Create instruction for response generation."""
        response_format = plan["response_format"]
        partial_response = plan.get("partial_response", False)
        
        base_instruction = """Generate a comprehensive answer using the provided documents and images.

IMPORTANT GUIDELINES:
1. Reference both textual and visual information
2. Be specific about which document/page information comes from
3. Integrate insights from images (diagrams, tables, charts) when relevant
4. Maintain accuracy - only state what's supported by the sources
5. Acknowledge any limitations in the available information"""
        
        if partial_response:
            base_instruction += "\n\nNOTE: This is a partial response due to incomplete context. Clearly indicate limitations."
        
        format_instructions = {
            "detailed": "Provide a thorough, well-structured response with detailed explanations.",
            "summary": "Provide a concise summary highlighting key points.",
            "structured": "Organize the response with clear sections and bullet points.",
            "conversational": "Write in a natural, conversational tone while being informative."
        }
        
        return f"{base_instruction}\n\n{format_instructions.get(response_format, format_instructions['conversational'])}"
    
    def _create_source_citations(self, documents: List[DocumentCandidate]) -> List[SourceCitation]:
        """Create source citations for used documents."""
        citations = []
        
        for doc in documents:
            citation = SourceCitation(
                document=doc.doc_source,
                page_number=doc.page_num,
                content_type=doc.visual_content_type or "text",
                excerpt=doc.markdown_text[:150] + "..." if len(doc.markdown_text) > 150 else doc.markdown_text
            )
            citations.append(citation)
        
        return citations
    
    def _identify_visual_elements(self, documents: List[DocumentCandidate]) -> List[str]:
        """Identify visual elements used in the response."""
        visual_elements = []
        
        for doc in documents:
            if doc.file_path:
                filename = doc.file_path.split('/')[-1]
                visual_elements.append(f"{doc.doc_source}_page_{doc.page_num}")
        
        return visual_elements
    
    def _calculate_multimodal_confidence(
        self,
        context_analysis: ContextAnalysis,
        ranked_docs: RankedDocuments
    ) -> float:
        """Calculate confidence score for multimodal aspects."""
        # Combine various factors
        factors = []
        
        # Context completeness
        factors.append(context_analysis.completeness_score)
        
        # Visual coverage
        factors.append(context_analysis.visual_coverage)
        
        # Document similarity scores
        if ranked_docs.documents:
            avg_similarity = sum(doc.similarity_score for doc in ranked_docs.documents) / len(ranked_docs.documents)
            factors.append(avg_similarity)
        
        # Diversity bonus (more sources = higher confidence)
        if ranked_docs.documents:
            unique_sources = len(set(doc.doc_source for doc in ranked_docs.documents))
            diversity_factor = min(unique_sources / 3, 1.0)  # Cap at 1.0
            factors.append(diversity_factor)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    def _create_no_context_answer(self) -> StructuredAnswer:
        """Create answer when no context is available."""
        return StructuredAnswer(
            main_response="I don't have sufficient information to answer your question. No relevant documents were found in the knowledge base.",
            evidence_strength="low",
            sources_used=[],
            visual_elements_used=[],
            limitations=["No relevant documents found", "Unable to access knowledge base"],
            follow_up_suggestions=[
                "Try rephrasing your question",
                "Check if the information exists in the documents",
                "Ask about a more specific topic"
            ],
            multimodal_confidence=0.0,
            processing_metadata={"reason": "no_context_available"}
        )
    
    def _create_fallback_response(self, documents: List[DocumentCandidate]) -> MultimodalResponse:
        """Create fallback response when structured generation fails."""
        # Simple text-based response as fallback
        doc_contents = []
        for doc in documents:
            doc_contents.append(f"From {doc.doc_source} page {doc.page_num}: {doc.markdown_text[:200]}...")
        
        combined_content = "\n\n".join(doc_contents)
        
        return MultimodalResponse(
            main_response=f"Based on the available documents:\n\n{combined_content}\n\nNote: This is a fallback response due to processing limitations.",
            evidence_strength="medium",
            key_sources=[{"source": doc.doc_source, "page": doc.page_num} for doc in documents],
            visual_elements_referenced=[],
            limitations=["Fallback response - limited processing capabilities"],
            follow_up_suggestions=["Try asking a more specific question"],
            confidence_assessment="medium"
        )