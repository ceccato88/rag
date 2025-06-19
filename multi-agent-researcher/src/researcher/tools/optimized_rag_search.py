"""
Ferramenta de busca RAG otimizada para o sistema multi-agente.
Separa a busca+reranking da geração de resposta, permitindo maior flexibilidade.
"""

import sys
import os
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
    
    def __init__(self, collection_name: str = "pdf_documents", top_k: int = None):
        super().__init__(
            name="optimized_rag_search", 
            description="Search and rerank documents without final answer generation"
        )
        self.collection_name = collection_name
        # Usar MAX_CANDIDATES do ambiente, com fallback para 5
        self.top_k = top_k if top_k is not None else int(os.getenv('MAX_CANDIDATES', 5))
        self.rag_system = None
        
    def _initialize_rag(self):
        """Lazy initialization of RAG search system."""
        print(f"🔧 [DEBUG] Initializing RAG. Current rag_system: {type(self.rag_system).__name__ if self.rag_system else 'None'}")
        
        if self.rag_system is None:
            try:
                # Se um sistema RAG foi injetado, usar ele
                if hasattr(self, 'injected_rag_system') and self.injected_rag_system:
                    print(f"🔧 [DEBUG] Using injected RAG system: {type(self.injected_rag_system).__name__}")
                    self.rag_system = self.injected_rag_system
                    return
                
                # Tentar importar sistema padrão
                print("🔧 [DEBUG] No injected RAG found, trying to import ProductionConversationalRAG")
                from src.core.search import ProductionConversationalRAG
                self.rag_system = ProductionConversationalRAG()
                print("🔧 [DEBUG] ProductionConversationalRAG imported successfully")
            except ImportError as e:
                # Fallback para modo demo se não conseguir importar
                print(f"🔧 [DEBUG] ImportError: {e}. Falling back to None")
                self.rag_system = None
        else:
            print(f"🔧 [DEBUG] RAG system already initialized: {type(self.rag_system).__name__}")
        
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
                        "enum": ["conceptual", "technical", "comparative", "examples", "overview", "applications", "general"],
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
        
        # Extrair documentos multimodais completos
        documents = []
        if "selected_pages_details" in rag_result:
            for i, page_detail in enumerate(rag_result["selected_pages_details"]):
                document = {
                    "document_id": f"doc_{page_detail.get('page_number', i)}",
                    "page_number": page_detail.get('page_number'),
                    "content": page_detail.get('content', ''),  # Markdown completo
                    "image_base64": page_detail.get('image_base64'),  # Imagem para visão
                    "file_path": page_detail.get('file_path'),
                    "similarity_score": page_detail.get('similarity_score', 0.0),
                    "relevance_rank": i + 1,
                    "source": page_detail.get('source', 'unknown'),
                    "is_multimodal": page_detail.get('is_multimodal', False),
                    "metadata": {
                        "doc_source": page_detail.get('doc_source'),
                        "page_type": "document_page",
                        "focus_area": focus_area,
                        "has_image": bool(page_detail.get('image_base64')),
                        "similarity_score": page_detail.get('similarity_score', 0.0)
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
            "overview": f"overview general introduction {query}",
            "applications": f"practical applications real-world usage {query}",
            "general": query  # Sem modificação
        }
        
        return focus_adjustments.get(focus_area, query)
    
    async def _execute_rag_pipeline_partial(self, query: str, top_k: int) -> Dict[str, Any]:
        """
        Executa pipeline RAG até o ponto de reranking, retornando dados multimodais completos.
        Os subagentes recebem o conteúdo original do banco vetorial: markdown + imagem base64.
        """
        
        try:
            # Usar ProductionConversationalRAG para acessar dados brutos do banco
            if hasattr(self.rag_system, 'search_candidates'):
                print(f"🔧 [DEBUG] Usando search_candidates para dados multimodais completos")
                
                # 1. Gerar embedding da query
                query_embedding = self.rag_system.get_query_embedding(query)
                print(f"🔧 [DEBUG] Embedding gerado: {len(query_embedding)} dimensões")
                
                # 2. Buscar candidatos brutos do Astra DB
                raw_candidates = self.rag_system.search_candidates(query_embedding, limit=top_k)
                print(f"🔧 [DEBUG] Candidatos brutos encontrados: {len(raw_candidates)}")
                
                if not raw_candidates:
                    return {
                        "selected_pages_details": [],
                        "total_candidates": 0,
                        "reranking_justification": "Nenhum candidato encontrado no banco vetorial",
                        "search_successful": False
                    }
                
                # 3. Re-ranking para selecionar os melhores
                selected_candidates, justification = self.rag_system.rerank_with_gpt(query, raw_candidates)
                print(f"🔧 [DEBUG] Re-ranking selecionou: {len(selected_candidates)} documentos")
                
                # 4. Preparar dados multimodais completos para subagentes
                multimodal_documents = []
                for candidate in selected_candidates:
                    # Carregar imagem em base64
                    image_base64 = None
                    if candidate.get("file_path"):
                        image_base64 = self.rag_system.encode_image_to_base64(candidate["file_path"])
                    
                    multimodal_doc = {
                        "page_number": candidate.get("page_num"),
                        "content": candidate.get("markdown_text", ""),  # Texto markdown completo
                        "doc_source": candidate.get("doc_source"),
                        "file_path": candidate.get("file_path"),
                        "similarity_score": candidate.get("similarity_score", 0.0),
                        "image_base64": image_base64,  # Imagem para visão
                        "source": "astra_db_multimodal",
                        "is_multimodal": True
                    }
                    multimodal_documents.append(multimodal_doc)
                    print(f"🔧 [DEBUG] Documento multimodal preparado: página {multimodal_doc['page_number']}, imagem: {'Sim' if image_base64 else 'Não'}")
                
                return {
                    "selected_pages_details": multimodal_documents,
                    "total_candidates": len(raw_candidates),
                    "reranking_justification": justification,
                    "search_successful": True
                }
            
            # Fallback para SimpleRAG (sem multimodal)
            elif hasattr(self.rag_system, 'search'):
                print(f"🔧 [DEBUG] Fallback: usando SimpleRAG (sem multimodal)")
                result_text = self.rag_system.search(query)
                
                if result_text and "No results" not in result_text:
                    documents = [{
                        "page_number": 1,
                        "content": result_text,  # Texto completo, não chunk
                        "doc_source": "simple_rag",
                        "source": "SimpleRAG",
                        "is_multimodal": False
                    }]
                    
                    return {
                        "selected_pages_details": documents,
                        "total_candidates": 1,
                        "reranking_justification": "SimpleRAG search result (sem multimodal)",
                        "search_successful": True
                    }
                else:
                    return {
                        "selected_pages_details": [],
                        "total_candidates": 0,
                        "reranking_justification": "Nenhum resultado encontrado",
                        "search_successful": False
                    }
            
            else:
                return {"error": "Sistema RAG não tem método compatível para dados multimodais"}
            
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
    
    def set_rag_system(self, rag_system):
        """Inject a RAG system into this tool."""
        print(f"🔧 [DEBUG] Injecting RAG system into tool: {type(rag_system).__name__}")
        self.rag_system = rag_system
        # Also set as injected system for reference
        self.injected_rag_system = rag_system
        print(f"🔧 [DEBUG] RAG system injection complete. Tool now has: {type(self.rag_system).__name__}")


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
        
        # Buscar comparações visuais
        visual_comparisons = []
        for doc in documents:
            if doc.get("is_multimodal") and doc.get("image_base64"):
                visual_comparisons.append({
                    "source": f"Page {doc.get('page_number', 'N/A')}",
                    "description": "Visual comparison/diagram",
                    "image_base64": doc.get("image_base64")
                })
        
        return {
            "comparisons": comparisons,
            "visual_comparisons": visual_comparisons,
            "advantages": advantages[:3],
            "disadvantages": disadvantages[:3],
            "document_count": len(documents),
            "multimodal_count": sum(1 for doc in documents if doc.get("is_multimodal"))
        }
    
    @staticmethod
    def extract_examples(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai exemplos e casos de uso dos documentos multimodais."""
        examples = []
        use_cases = []
        visual_examples = []
        
        for doc in documents:
            content = doc.get("content", "")
            page_num = doc.get("page_number", "N/A")
            has_image = doc.get("is_multimodal", False) and doc.get("image_base64")
            
            # Buscar padrões de exemplos no texto
            example_patterns = ["example", "for instance", "such as", "case study", "demonstration"]
            if any(pattern in content.lower() for pattern in example_patterns):
                examples.append({
                    "source": f"Page {page_num}",
                    "example_text": content,  # Texto completo do exemplo
                    "has_visual": has_image,
                    "similarity_score": doc.get("similarity_score", 0.0)
                })
            
            # Buscar casos de uso
            usecase_patterns = ["use case", "application", "scenario", "implementation"]
            if any(pattern in content.lower() for pattern in usecase_patterns):
                use_cases.append({
                    "source": f"Page {page_num}",
                    "use_case": content[:200] + "..." if len(content) > 200 else content,
                    "has_visual": has_image
                })
            
            # Identificar exemplos visuais (screenshots, diagramas de exemplo)
            if has_image and any(keyword in content.lower() for keyword in ["screenshot", "example", "demo"]):
                visual_examples.append({
                    "source": f"Page {page_num}",
                    "type": "visual_example",
                    "description": f"Visual example/demo on page {page_num}",
                    "image_base64": doc.get("image_base64")
                })
        
        return {
            "examples": examples,
            "use_cases": use_cases[:3],
            "visual_examples": visual_examples,
            "document_count": len(documents),
            "multimodal_count": sum(1 for doc in documents if doc.get("is_multimodal"))
        }