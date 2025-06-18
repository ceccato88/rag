"""
Ferramenta de busca RAG otimizada para o sistema multi-agente.
Separa a busca+reranking da geração de resposta, permitindo maior flexibilidade.
"""

import sys
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

# Load environment variables from project root
from dotenv import load_dotenv, find_dotenv

# Find and load .env file from any parent directory
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)

# Add the parent RAG system to path
sys.path.insert(0, str(Path(__file__).parents[4]))

from researcher.tools.base import Tool, ToolDescription, ToolStatus, ToolResult


class OptimizedRAGSearchTool(Tool):
    """
    Ferramenta de busca RAG otimizada que retorna apenas os documentos relevantes
    sem gerar a resposta final. Isso permite que o subagente processe os documentos
    de acordo com sua especialização.
    """
    
    def __init__(self, collection_name: str = "pdf_documents", top_k: int = 5):
        super().__init__(
            name="optimized_rag_search", 
            description="Search and rerank documents without final answer generation"
        )
        self.collection_name = collection_name
        self.top_k = top_k
        self.rag_system = None
        
    def _initialize_rag(self):
        """Lazy initialization of RAG search system."""
        if self.rag_system is None:
            try:
                from search import ProductionConversationalRAG
                self.rag_system = ProductionConversationalRAG()
            except ImportError:
                # Fallback para modo demo se não conseguir importar
                self.rag_system = None
        
    def get_description(self) -> ToolDescription:
        return ToolDescription(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for internal documents"
                    },
                    "top_k": {
                        "type": "integer", 
                        "description": "Number of relevant documents to return",
                        "default": self.top_k,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "Area of focus for document selection",
                        "enum": ["conceptual", "technical", "comparative", "examples", "general"],
                        "default": "general"
                    }
                },
                "required": ["query"]
            },
            examples=[
                {"query": "temporal knowledge graphs", "top_k": 3, "focus_area": "technical"},
                {"query": "Zep vs MemGPT comparison", "top_k": 5, "focus_area": "comparative"}
            ],
            cost_per_call=0.001,
            timeout=30.0
        )
    
    async def _execute(
        self,
        query: str,
        top_k: Optional[int] = None,
        focus_area: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa busca RAG otimizada retornando documentos estruturados.
        
        Returns:
            Dict com documentos encontrados, metadados e informações de busca
        """
        
        start_time = time.time()
        search_top_k = top_k if top_k is not None else self.top_k
        
        # Validar input
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
            
        # Inicializar RAG se necessário
        self._initialize_rag()
        
        try:
            if self.rag_system is None:
                # Mock results para demo/testing
                return await self._generate_mock_results(query, search_top_k, focus_area)
            
            # Executar busca RAG otimizada
            search_results = await self._perform_optimized_search(query, search_top_k, focus_area)
            
            execution_time = time.time() - start_time
            
            return {
                "query": query,
                "documents": search_results["documents"],
                "search_metadata": {
                    "total_candidates": search_results.get("total_candidates", 0),
                    "documents_selected": len(search_results["documents"]),
                    "reranking_justification": search_results.get("justification", ""),
                    "execution_time": execution_time,
                    "focus_area": focus_area,
                    "search_method": "rag_pipeline"
                },
                "success": True
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "query": query,
                "documents": [],
                "search_metadata": {
                    "execution_time": execution_time,
                    "error": str(e)
                },
                "success": False,
                "error": f"Optimized RAG search failed: {str(e)}"
            }
    
    async def _perform_optimized_search(self, query: str, top_k: int, focus_area: str) -> Dict[str, Any]:
        """
        Executa busca otimizada usando o sistema RAG de produção.
        Modifica a query baseada no focus_area para melhor direcionamento.
        """
        
        # Ajustar query baseada no foco
        focused_query = self._adjust_query_for_focus(query, focus_area)
        
        # Executar busca até o ponto de reranking (sem geração final)
        rag_result = await self._execute_rag_pipeline_partial(focused_query, top_k)
        
        if "error" in rag_result:
            raise Exception(rag_result["error"])
        
        # Extrair documentos estruturados
        documents = []
        if "selected_pages_details" in rag_result:
            for i, page_detail in enumerate(rag_result["selected_pages_details"]):
                document = {
                    "document_id": f"doc_{page_detail.get('page_number', i)}",
                    "page_number": page_detail.get('page_number'),
                    "content": page_detail.get('content', ''),
                    "relevance_rank": i + 1,
                    "source": page_detail.get('source', 'unknown'),
                    "metadata": {
                        "doc_source": page_detail.get('doc_source'),
                        "page_type": "document_page",
                        "focus_area": focus_area
                    }
                }
                documents.append(document)
        
        return {
            "documents": documents,
            "total_candidates": rag_result.get("total_candidates", 0),
            "justification": rag_result.get("reranking_justification", ""),
            "pipeline_method": "production_rag"
        }
    
    def _adjust_query_for_focus(self, query: str, focus_area: str) -> str:
        """
        Ajusta a query baseada na área de foco para melhor direcionamento dos resultados.
        """
        focus_adjustments = {
            "conceptual": f"definition concepts fundamentals {query}",
            "technical": f"technical implementation architecture {query}",
            "comparative": f"comparison analysis differences {query}",
            "examples": f"examples use cases applications {query}",
            "general": query  # Sem modificação
        }
        
        return focus_adjustments.get(focus_area, query)
    
    async def _execute_rag_pipeline_partial(self, query: str, top_k: int) -> Dict[str, Any]:
        """
        Executa pipeline RAG até o ponto de reranking, sem gerar resposta final.
        Isso permite que o subagente processe os documentos com sua especialização.
        """
        
        try:
            # Usar o sistema RAG interno para busca e reranking
            # Mas interceptar antes da geração final
            
            # HACK: Interceptar o pipeline do sistema RAG
            # Em produção, isso seria uma refatoração do search.py
            
            # Por enquanto, usar o resultado completo e extrair as partes relevantes
            full_result = self.rag_system.search_and_answer(query)
            
            if "error" in full_result:
                return full_result
            
            # Extrair apenas as informações de busca e reranking
            partial_result = {
                "selected_pages_details": full_result.get("selected_pages_details", []),
                "total_candidates": full_result.get("total_candidates", 0),
                "reranking_justification": full_result.get("reranking_justification", ""),
                "search_successful": True
            }
            
            return partial_result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _generate_mock_results(self, query: str, top_k: int, focus_area: str) -> Dict[str, Any]:
        """Gera resultados mock para demo/testing."""
        
        mock_documents = []
        for i in range(min(top_k, 3)):  # Máximo 3 documentos mock
            document = {
                "document_id": f"mock_doc_{i+1}",
                "page_number": i + 1,
                "content": f"Mock content about {query} from {focus_area} perspective. " * 20,
                "relevance_rank": i + 1,
                "source": "mock_system",
                "metadata": {
                    "doc_source": f"mock_document_{i+1}.pdf",
                    "page_type": "mock_page",
                    "focus_area": focus_area,
                    "mock": True
                }
            }
            mock_documents.append(document)
        
        return {
            "query": query,
            "documents": mock_documents,
            "search_metadata": {
                "total_candidates": 5,
                "documents_selected": len(mock_documents),
                "reranking_justification": f"Mock reranking for {focus_area} focus",
                "execution_time": 0.1,
                "focus_area": focus_area,
                "search_method": "mock_system"
            },
            "success": True
        }


class DocumentProcessor:
    """
    Processador de documentos que permite aos subagentes especializados 
    processarem os resultados da busca de acordo com sua área de foco.
    """
    
    @staticmethod
    def extract_concepts(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai conceitos e definições dos documentos."""
        concepts = []
        definitions = []
        
        for doc in documents:
            content = doc.get("content", "")
            
            # Buscar padrões de definição
            if any(pattern in content.lower() for pattern in ["is defined as", "refers to", "means"]):
                definitions.append({
                    "source": doc.get("document_id"),
                    "content": content[:200] + "..." if len(content) > 200 else content
                })
            
            # Extrair termos técnicos (simulado)
            technical_terms = [word for word in content.split() if len(word) > 8 and word.isupper()]
            concepts.extend(technical_terms[:3])  # Máximo 3 por documento
        
        return {
            "concepts": list(set(concepts)),
            "definitions": definitions,
            "document_count": len(documents)
        }
    
    @staticmethod
    def extract_technical_details(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai detalhes técnicos dos documentos."""
        technical_info = []
        architectures = []
        
        for doc in documents:
            content = doc.get("content", "")
            
            # Buscar padrões técnicos
            if any(pattern in content.lower() for pattern in ["algorithm", "implementation", "architecture"]):
                technical_info.append({
                    "source": doc.get("document_id"),
                    "type": "technical_detail",
                    "content": content[:300] + "..." if len(content) > 300 else content
                })
            
            # Buscar menções de arquitetura
            if "architecture" in content.lower():
                architectures.append({
                    "source": doc.get("document_id"),
                    "architecture_mention": content[:150] + "..."
                })
        
        return {
            "technical_details": technical_info,
            "architectures": architectures,
            "document_count": len(documents)
        }
    
    @staticmethod
    def extract_comparisons(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai informações comparativas dos documentos."""
        comparisons = []
        advantages = []
        disadvantages = []
        
        for doc in documents:
            content = doc.get("content", "")
            
            # Buscar padrões comparativos
            comparison_patterns = ["compared to", "versus", "vs", "better than", "worse than"]
            if any(pattern in content.lower() for pattern in comparison_patterns):
                comparisons.append({
                    "source": doc.get("document_id"),
                    "comparison_text": content[:250] + "..." if len(content) > 250 else content
                })
            
            # Buscar vantagens/desvantagens
            if any(pattern in content.lower() for pattern in ["advantage", "benefit", "pro"]):
                advantages.append(content[:100] + "...")
            
            if any(pattern in content.lower() for pattern in ["disadvantage", "limitation", "con"]):
                disadvantages.append(content[:100] + "...")
        
        return {
            "comparisons": comparisons,
            "advantages": advantages[:3],  # Máximo 3
            "disadvantages": disadvantages[:3],  # Máximo 3
            "document_count": len(documents)
        }
    
    @staticmethod
    def extract_examples(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai exemplos e casos de uso dos documentos."""
        examples = []
        use_cases = []
        
        for doc in documents:
            content = doc.get("content", "")
            
            # Buscar padrões de exemplo
            example_patterns = ["example", "for instance", "such as", "case study"]
            if any(pattern in content.lower() for pattern in example_patterns):
                examples.append({
                    "source": doc.get("document_id"),
                    "example_text": content[:200] + "..." if len(content) > 200 else content
                })
            
            # Buscar casos de uso
            if any(pattern in content.lower() for pattern in ["use case", "application", "scenario"]):
                use_cases.append({
                    "source": doc.get("document_id"),
                    "use_case": content[:150] + "..." if len(content) > 150 else content
                })
        
        return {
            "examples": examples,
            "use_cases": use_cases,
            "document_count": len(documents)
        }