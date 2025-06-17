"""Multimodal retriever agent using Voyage AI and Astra DB."""

import os
import base64
from typing import List, Optional, Dict, Any
import asyncio
import voyageai
from PIL import Image
from astrapy import DataAPIClient

from ..agents.base import Agent, AgentContext
from ..models.rag_models import (
    MultimodalSearchPlan, DocumentCandidate, SearchStrategy
)


class RetrieverConfig:
    """Configuration for multimodal retriever."""
    def __init__(
        self,
        voyage_api_key: Optional[str] = None,
        astra_endpoint: Optional[str] = None,
        astra_token: Optional[str] = None,
        collection_name: str = "pdf_documents",
        max_candidates: int = 20
    ):
        self.voyage_api_key = voyage_api_key or os.getenv("VOYAGE_API_KEY")
        self.astra_endpoint = astra_endpoint or os.getenv("ASTRA_DB_API_ENDPOINT")
        self.astra_token = astra_token or os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        self.collection_name = collection_name
        self.max_candidates = max_candidates


class MultimodalRetrieverAgent(Agent[List[DocumentCandidate]]):
    """Agent that retrieves documents using multimodal search with Voyage AI and Astra DB."""
    
    def __init__(self, config: Optional[RetrieverConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or RetrieverConfig()
        
        # Initialize Voyage AI client
        if self.config.voyage_api_key:
            voyageai.api_key = self.config.voyage_api_key
            self.voyage_client = voyageai.Client()
        else:
            raise ValueError("Voyage AI API key is required")
        
        # Initialize Astra DB connection
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize connection to Astra DB."""
        try:
            if not self.config.astra_endpoint or not self.config.astra_token:
                raise ValueError("Astra DB endpoint and token are required")
                
            client = DataAPIClient()
            database = client.get_database(
                self.config.astra_endpoint, 
                token=self.config.astra_token
            )
            self.collection = database.get_collection(self.config.collection_name)
            
            # Test connectivity
            list(self.collection.find({}, limit=1))
            self.add_thinking(f"Connected to Astra DB collection '{self.config.collection_name}'")
            
        except Exception as e:
            self.add_thinking(f"Failed to connect to Astra DB: {e}")
            raise
    
    async def plan(self, context: AgentContext) -> MultimodalSearchPlan:
        """Create multimodal search plan based on context."""
        self.add_thinking(f"Planning multimodal search for: {context.query}")
        
        # Extract search strategies from metadata
        search_strategies = context.metadata.get("search_strategies", [])
        
        if not search_strategies:
            # Create default strategy
            search_strategies = [SearchStrategy(
                primary_queries=[context.query],
                fallback_queries=[f"information about {context.query}"],
                content_filters=[],
                max_candidates=self.config.max_candidates
            )]
        
        # Generate text queries from strategies
        text_queries = []
        visual_concepts = []
        
        for strategy in search_strategies:
            text_queries.extend(strategy.primary_queries)
            
            # Extract visual concepts from content filters
            visual_filters = [f for f in strategy.content_filters 
                            if f in ['diagrams', 'tables', 'charts', 'graphs', 'figures']]
            visual_concepts.extend(visual_filters)
        
        plan = MultimodalSearchPlan(
            text_queries=text_queries,
            visual_concepts=visual_concepts or ["diagrams", "tables", "figures"],
            embedding_strategy="multimodal_combined",
            retrieval_params={
                "max_candidates": max(s.max_candidates for s in search_strategies),
                "include_similarity": True
            }
        )
        
        self.add_thinking(f"Search plan created with {len(plan.text_queries)} queries")
        return plan
    
    async def execute(self, plan: MultimodalSearchPlan) -> List[DocumentCandidate]:
        """Execute multimodal search using the plan."""
        self.add_thinking("Executing multimodal document retrieval")
        
        all_candidates = []
        
        # Execute searches for each text query
        for query in plan.text_queries:
            try:
                candidates = await self._search_with_query(query, plan)
                all_candidates.extend(candidates)
                self.add_thinking(f"Retrieved {len(candidates)} candidates for query: {query[:50]}...")
            except Exception as e:
                self.add_thinking(f"Search failed for query '{query}': {e}")
                continue
        
        # Remove duplicates and sort by similarity
        unique_candidates = self._deduplicate_candidates(all_candidates)
        unique_candidates.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit to max candidates
        max_candidates = plan.retrieval_params.get("max_candidates", self.config.max_candidates)
        final_candidates = unique_candidates[:max_candidates]
        
        self.add_thinking(f"Final retrieval: {len(final_candidates)} unique candidates")
        return final_candidates
    
    async def _search_with_query(
        self, 
        query: str, 
        plan: MultimodalSearchPlan
    ) -> List[DocumentCandidate]:
        """Search documents with a single query using multimodal embeddings."""
        
        # Generate multimodal embedding
        embedding = await self._get_multimodal_embedding(query)
        
        # Search in Astra DB
        try:
            cursor = self.collection.find(
                {},
                sort={"$vector": embedding},
                limit=plan.retrieval_params.get("max_candidates", 20),
                include_similarity=True,
                projection={
                    "file_path": True,
                    "page_num": True,
                    "doc_source": True,
                    "markdown_text": True,
                    "_id": True
                }
            )
            
            candidates = []
            for doc in cursor:
                candidate = DocumentCandidate(
                    doc_id=doc.get("_id", ""),
                    file_path=doc.get("file_path", ""),
                    page_num=doc.get("page_num", 0),
                    doc_source=doc.get("doc_source", ""),
                    markdown_text=doc.get("markdown_text", ""),
                    similarity_score=doc.get("$similarity", 0.0),
                    visual_content_type=self._detect_visual_content_type(doc.get("file_path", ""))
                )
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            self.add_thinking(f"Astra DB search failed: {e}")
            return []
    
    async def _get_multimodal_embedding(self, query: str) -> List[float]:
        """Generate multimodal embedding for the query using Voyage AI."""
        try:
            # For now, use text-only embedding
            # In future, could include reference images or visual context
            res = self.voyage_client.multimodal_embed(
                inputs=[[query]],
                model="voyage-multimodal-3",
                input_type="query"
            )
            return res.embeddings[0]
            
        except Exception as e:
            self.add_thinking(f"Failed to generate embedding: {e}")
            raise
    
    def _detect_visual_content_type(self, file_path: str) -> Optional[str]:
        """Detect type of visual content from file path."""
        if not file_path:
            return None
            
        # Simple heuristic based on filename patterns
        filename = os.path.basename(file_path).lower()
        
        if any(term in filename for term in ['table', 'tab']):
            return "table"
        elif any(term in filename for term in ['figure', 'fig', 'diagram']):
            return "diagram"
        elif any(term in filename for term in ['chart', 'graph']):
            return "chart"
        elif filename.endswith(('.png', '.jpg', '.jpeg')):
            return "image"
        else:
            return "mixed"
    
    def _deduplicate_candidates(self, candidates: List[DocumentCandidate]) -> List[DocumentCandidate]:
        """Remove duplicate candidates based on doc_id."""
        seen_ids = set()
        unique_candidates = []
        
        for candidate in candidates:
            if candidate.doc_id not in seen_ids:
                seen_ids.add(candidate.doc_id)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    @staticmethod
    def encode_image_to_base64(image_path: str) -> Optional[str]:
        """Encode image to base64 for multimodal processing."""
        try:
            if not image_path or not os.path.exists(image_path):
                return None
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None