"""Simplified RAG-based research subagent."""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Load environment variables from project root
from dotenv import load_dotenv, find_dotenv

# Find and load .env file from any parent directory
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)

# Add the parent RAG directory to path
rag_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(rag_path))

from researcher.agents.base import Agent, AgentContext, AgentResult, AgentState
from researcher.tools.optimized_rag_search import OptimizedRAGSearchTool, DocumentProcessor
from pydantic import BaseModel


class RAGSubagentConfig(BaseModel):
    """Configuration for RAG-based subagent."""
    enable_thinking: bool = True
    top_k: int = int(os.getenv('MAX_CANDIDATES', 5))


class RAGResearchSubagent(Agent[str]):
    """
    Simplified RAG research subagent that searches internal documents.
    
    This subagent replaces web search with local document search using RAG.
    """
    
    def __init__(
        self,
        config: Optional[RAGSubagentConfig] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.config = config or RAGSubagentConfig()
        self.rag_tool = OptimizedRAGSearchTool(top_k=self.config.top_k)
        self.search_results: List[Dict[str, Any]] = []
        
    async def plan(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Create a simple research plan for RAG search."""
        self.add_thinking(f"Planning RAG research for: {context.objective}")
        
        # Simple plan: search with the main query
        return [{
            "action": "rag_search",
            "query": context.query,
            "objective": context.objective
        }]
    
    async def execute(self, plan: List[Dict[str, Any]]) -> str:
        """Execute optimized RAG search plan."""
        action_plan = plan[0]
        query = action_plan["query"]
        objective = action_plan["objective"]
        focus_area = action_plan.get("focus_area", "general")
        
        self.add_thinking(f"Executing optimized RAG search for: {query}")
        self.add_thinking(f"Focus area: {focus_area}")
        
        try:
            # Execute optimized RAG search (search + rerank only, no answer generation)
            search_result = await self.rag_tool._execute(
                query=query,
                top_k=self.config.top_k,
                focus_area=focus_area
            )
            
            if search_result.get("success", False):
                documents = search_result["documents"]
                metadata = search_result["search_metadata"]
                
                self.add_thinking(f"Found {len(documents)} relevant documents")
                self.add_thinking(f"Search completed in {metadata.get('execution_time', 0):.2f}s")
                
                # Process documents and generate specialized response
                specialized_response = self._generate_specialized_response(
                    documents, query, objective, focus_area, metadata
                )
                
                return specialized_response
                
            else:
                error_msg = f"Optimized RAG search failed: {search_result.get('error', 'Unknown error')}"
                self.add_thinking(error_msg)
                return f"Search failed: {search_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            error_msg = f"Error during optimized RAG search: {str(e)}"
            self.add_thinking(error_msg)
            return f"Error: {str(e)}"
    
    def _generate_specialized_response(self, documents: List[Dict[str, Any]], query: str, 
                                     objective: str, focus_area: str, metadata: Dict[str, Any]) -> str:
        """Generate specialized response based on focus area and document analysis."""
        
        if not documents:
            return f"No relevant documents found for query: {query}"
        
        # Use DocumentProcessor to extract relevant information based on focus area
        if focus_area == "conceptual":
            processed_info = DocumentProcessor.extract_concepts(documents)
            return self._format_conceptual_response(query, objective, documents, processed_info, metadata)
        elif focus_area == "technical":
            processed_info = DocumentProcessor.extract_technical_details(documents)
            return self._format_technical_response(query, objective, documents, processed_info, metadata)
        elif focus_area == "comparative":
            processed_info = DocumentProcessor.extract_comparisons(documents)
            return self._format_comparative_response(query, objective, documents, processed_info, metadata)
        elif focus_area == "examples":
            processed_info = DocumentProcessor.extract_examples(documents)
            return self._format_examples_response(query, objective, documents, processed_info, metadata)
        else:
            # General response
            return self._format_general_response(query, objective, documents, metadata)
    
    def _format_conceptual_response(self, query: str, objective: str, documents: List[Dict], 
                                  processed_info: Dict, metadata: Dict) -> str:
        """Format response focusing on concepts and definitions."""
        
        response_lines = [
            f"# 🎯 Conceptual Analysis: {query}",
            f"**Objective**: {objective}",
            f"**Documents Analyzed**: {processed_info['document_count']}",
            f"**Analysis Time**: {metadata.get('execution_time', 0):.2f}s",
            "",
            "## 📋 Key Concepts Identified",
        ]
        
        # Add concepts
        if processed_info['concepts']:
            for concept in processed_info['concepts'][:5]:
                response_lines.append(f"• {concept}")
        else:
            response_lines.append("• No specific technical concepts identified")
        
        response_lines.extend(["", "## 📖 Definitions Found"])
        
        # Add definitions
        if processed_info['definitions']:
            for i, definition in enumerate(processed_info['definitions'][:3], 1):
                response_lines.extend([
                    f"### Definition {i}",
                    f"**Source**: {definition['source']}",
                    definition['content'],
                    ""
                ])
        else:
            response_lines.append("No explicit definitions found in the documents.")
        
        # Add document summaries
        response_lines.extend(["", "## 📄 Document Summaries"])
        for i, doc in enumerate(documents[:3], 1):
            content_preview = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
            response_lines.extend([
                f"### Document {i} (Page {doc.get('page_number', 'N/A')})",
                content_preview,
                ""
            ])
        
        return "\n".join(response_lines)
    
    def _format_technical_response(self, query: str, objective: str, documents: List[Dict], 
                                 processed_info: Dict, metadata: Dict) -> str:
        """Format response focusing on technical details."""
        
        response_lines = [
            f"# 🔧 Technical Analysis: {query}",
            f"**Objective**: {objective}",
            f"**Documents Analyzed**: {processed_info['document_count']}",
            f"**Analysis Time**: {metadata.get('execution_time', 0):.2f}s",
            "",
            "## ⚙️ Technical Details"
        ]
        
        # Add technical information
        if processed_info['technical_details']:
            for i, detail in enumerate(processed_info['technical_details'][:3], 1):
                response_lines.extend([
                    f"### Technical Detail {i}",
                    f"**Type**: {detail['type']}",
                    f"**Source**: {detail['source']}",
                    detail['content'],
                    ""
                ])
        
        # Add visual technical content
        if processed_info.get('visual_technical'):
            response_lines.extend(["## 📊 Visual Technical Content"])
            for visual in processed_info['visual_technical']:
                response_lines.extend([
                    f"**{visual['source']}**: {visual['description']}",
                    ""
                ])
        
        # Add architecture information with visual indicators
        if processed_info['architectures']:
            response_lines.extend(["## 🏗️ Architecture Information"])
            for arch in processed_info['architectures'][:2]:
                visual_indicator = " 📷" if arch.get('has_visual') else ""
                response_lines.extend([
                    f"**Source**: {arch['source']}{visual_indicator}",
                    arch['architecture_mention'],
                    ""
                ])
        
        return "\n".join(response_lines)
    
    def _format_comparative_response(self, query: str, objective: str, documents: List[Dict], 
                                   processed_info: Dict, metadata: Dict) -> str:
        """Format response focusing on comparisons."""
        
        response_lines = [
            f"# ⚖️ Comparative Analysis: {query}",
            f"**Objective**: {objective}",
            f"**Documents Analyzed**: {processed_info['document_count']}",
            f"**Analysis Time**: {metadata.get('execution_time', 0):.2f}s",
            "",
            "## 🔄 Comparisons Found"
        ]
        
        # Add comparisons
        if processed_info['comparisons']:
            for i, comp in enumerate(processed_info['comparisons'][:3], 1):
                response_lines.extend([
                    f"### Comparison {i}",
                    f"**Source**: {comp['source']}",
                    comp['comparison_text'],
                    ""
                ])
        
        # Add advantages/disadvantages
        if processed_info['advantages'] or processed_info['disadvantages']:
            response_lines.extend(["## ✅ Advantages & ❌ Disadvantages"])
            
            if processed_info['advantages']:
                response_lines.append("### ✅ Advantages:")
                for adv in processed_info['advantages']:
                    response_lines.append(f"• {adv}")
                response_lines.append("")
            
            if processed_info['disadvantages']:
                response_lines.append("### ❌ Disadvantages:")
                for dis in processed_info['disadvantages']:
                    response_lines.append(f"• {dis}")
        
        return "\n".join(response_lines)
    
    def _format_examples_response(self, query: str, objective: str, documents: List[Dict], 
                                processed_info: Dict, metadata: Dict) -> str:
        """Format response focusing on examples and use cases."""
        
        response_lines = [
            f"# 📚 Examples & Use Cases: {query}",
            f"**Objective**: {objective}",
            f"**Documents Analyzed**: {processed_info['document_count']}",
            f"**Analysis Time**: {metadata.get('execution_time', 0):.2f}s",
            "",
            "## 💡 Examples Found"
        ]
        
        # Add examples
        if processed_info['examples']:
            for i, example in enumerate(processed_info['examples'][:3], 1):
                response_lines.extend([
                    f"### Example {i}",
                    f"**Source**: {example['source']}",
                    example['example_text'],
                    ""
                ])
        
        # Add use cases
        if processed_info['use_cases']:
            response_lines.extend(["## 🎯 Use Cases"])
            for i, use_case in enumerate(processed_info['use_cases'][:3], 1):
                response_lines.extend([
                    f"### Use Case {i}",
                    f"**Source**: {use_case['source']}",
                    use_case['use_case'],
                    ""
                ])
        
        return "\n".join(response_lines)
    
    def _format_general_response(self, query: str, objective: str, documents: List[Dict], 
                               metadata: Dict) -> str:
        """Format general response when no specific focus area is defined."""
        
        response_lines = [
            f"# 📋 Research Report: {query}",
            f"**Objective**: {objective}",
            f"**Documents Found**: {len(documents)}",
            f"**Search Time**: {metadata.get('execution_time', 0):.2f}s",
            f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📄 Document Findings"
        ]
        
        # Add findings from each document
        for i, doc in enumerate(documents[:5], 1):  # Limit to top 5
            doc_id = doc.get('document_id', f'Document {i}')
            content = doc.get('content', '')
            page_num = doc.get('page_number', 'N/A')
            
            # Truncate content for readability
            content_preview = content[:300] + "..." if len(content) > 300 else content
            
            response_lines.extend([
                f"### {i}. {doc_id} (Page {page_num})",
                f"**Content**: {content_preview}",
                ""
            ])
        
        # Add summary
        if len(documents) > 5:
            response_lines.extend([
                f"*({len(documents) - 5} additional documents found)*",
                ""
            ])
        
        return "\n".join(response_lines)
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the complete RAG research process."""
        self.state = AgentState.PLANNING
        start_time = datetime.utcnow()
        
        # Initialize result
        self._result = AgentResult(
            agent_id=self.agent_id,
            status=self.state,
            start_time=start_time
        )
        
        try:
            self.add_thinking(f"Starting RAG research for: '{context.query}'")
            
            # Planning
            plan = await self.plan(context)
            
            # Execution
            self.state = AgentState.EXECUTING
            self._result.status = self.state
            output = await self.execute(plan)
            
            # Success
            self.state = AgentState.COMPLETED
            self._result.status = AgentState.COMPLETED
            self._result.output = output
            self._result.end_time = datetime.utcnow()
            
            return self._result
            
        except Exception as e:
            self.state = AgentState.FAILED
            self._result.status = AgentState.FAILED
            self._result.error = str(e)
            self._result.end_time = datetime.utcnow()
            self.add_thinking(f"RAG research failed: {e}")
            
            return self._result
    
    def get_search_results(self) -> List[Dict[str, Any]]:
        """Get the raw search results."""
        return self.search_results.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the search results."""
        if not self.search_results:
            return {"status": "no_results", "count": 0}
        
        avg_similarity = sum(r.get('similarity_score', 0) for r in self.search_results) / len(self.search_results)
        
        return {
            "status": "success",
            "count": len(self.search_results),
            "average_similarity": avg_similarity
        }


# Alias for compatibility
DocumentResearchSubagent = RAGResearchSubagent
