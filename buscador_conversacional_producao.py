# buscador_conversacional_producao.py

import os
import re
import base64
import json
import logging
from typing import List, Tuple, Optional, Dict, Any
from dotenv import load_dotenv

import voyageai
from openai import OpenAI
from PIL import Image
from astrapy import DataAPIClient

# Configurações para produção
LLM_MODEL = "gpt-4o" 
MAX_CANDIDATES = 5
MAX_TOKENS_RERANK = 512
MAX_TOKENS_ANSWER = 2048
MAX_TOKENS_QUERY_TRANSFORM = 150  # Reduzido para eficiência
COLLECTION_NAME = "pdf_documents"

# Logging estruturado para produção
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ProductionQueryTransformer:
    """
    Transformador de queries otimizado para produção
    - Menos chamadas LLM (economia de custos)
    - Lógica determinística quando possível
    - Fallbacks robustos
    - Logging estruturado
    """
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.transformation_cache = {}  # Cache para transformações comuns
        self._init_patterns()
    
    def _init_patterns(self):
        """Inicializa padrões para classificação determinística"""
        self.greeting_patterns = {
            'simple': ['oi', 'olá', 'hello', 'hi', 'hey'],
            'formal': ['bom dia', 'boa tarde', 'boa noite', 'good morning'],
            'casual': ['opa', 'salve', 'e aí']
        }
        
        self.thank_patterns = [
            'obrigado', 'obrigada', 'thanks', 'thank you', 'valeu', 
            'brigado', 'grato', 'grata'
        ]
        
        self.document_terms = [
            'zep', 'graphiti', 'rag', 'temporal', 'knowledge graph',
            'grafo', 'arquitetura', 'paper', 'documento', 'artigo',
            'tabela', 'table', 'figura', 'figure', 'performance', 
            'resultado', 'metodologia', 'algorithm', 'invalidação', 
            'memória', 'embedding', 'vector', 'similarity'
        ]
        
        self.inquiry_keywords = [
            'explique', 'explain', 'como', 'how', 'o que', 'what',
            'quais', 'which', 'where', 'onde', 'quando', 'when',
            'por que', 'why', 'porque', 'me fale', 'tell me',
            'descreva', 'describe', 'mostre', 'show', 'qual',
            'quero saber', 'want to know', 'preciso entender',
            'pode explicar', 'can you explain'
        ]
        
        self.contextual_pronouns = [
            'isso', 'isto', 'aquilo', 'ele', 'ela', 'eles', 'elas',
            'this', 'that', 'these', 'those', 'it', 'they'
        ]
    
    def transform_query(self, chat_history: List[Dict[str, str]]) -> str:
        """
        Transformação principal com múltiplas estratégias
        """
        try:
            if not chat_history:
                return "Not applicable"
            
            last_message = self._get_last_user_message(chat_history)
            if not last_message:
                return "Not applicable"
            
            # Cache para transformações já feitas
            cache_key = self._create_cache_key(last_message, chat_history)
            if cache_key in self.transformation_cache:
                logger.debug(f"Cache hit para: {last_message[:30]}...")
                return self.transformation_cache[cache_key]
            
            # 1. Verificações determinísticas (sem LLM)
            deterministic_result = self._deterministic_classification(last_message, chat_history)
            if deterministic_result != "NEEDS_LLM":
                self.transformation_cache[cache_key] = deterministic_result
                return deterministic_result
            
            # 2. Transformação com LLM (apenas quando necessário)
            llm_result = self._llm_transformation(last_message, chat_history)
            self.transformation_cache[cache_key] = llm_result
            
            return llm_result
            
        except Exception as e:
            logger.error(f"Erro na transformação de query: {e}")
            # Fallback seguro
            return self._safe_fallback(last_message)
    
    def _deterministic_classification(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Classificação determinística sem LLM (mais rápida e barata)
        """
        message_lower = message.lower().strip()
        
        # 1. Saudações simples
        if self._is_simple_greeting(message_lower):
            return "Not applicable"
        
        # 2. Agradecimentos simples
        if self._is_simple_thanks(message_lower):
            return "Not applicable"
        
        # 3. Menções diretas ao documento
        if self._mentions_document_directly(message_lower):
            return message  # Já está bem formada
        
        # 4. Perguntas gerais sobre o documento
        if self._is_general_document_inquiry(message_lower):
            return f"Sobre o documento Zep: {message}"
        
        # 5. Referências contextuais (pronomes)
        if self._has_contextual_references(message_lower) and self._has_document_context(chat_history):
            return f"Sobre o Zep: {message}"
        
        # 6. Perguntas com palavras-chave de consulta
        if self._has_inquiry_pattern(message_lower):
            return f"Sobre o documento Zep: {message}"
        
        # Se chegou aqui, precisa de LLM para contexto mais complexo
        return "NEEDS_LLM"
    
    def _is_simple_greeting(self, message: str) -> bool:
        """Detecta saudações simples"""
        words = message.split()
        
        # Saudações de 1-2 palavras
        if len(words) <= 2:
            for pattern_group in self.greeting_patterns.values():
                if all(word in pattern_group for word in words):
                    return True
        
        return False
    
    def _is_simple_thanks(self, message: str) -> bool:
        """Detecta agradecimentos simples"""
        return any(thank in message for thank in self.thank_patterns) and len(message.split()) <= 3
    
    def _mentions_document_directly(self, message: str) -> bool:
        """Verifica se menciona termos do documento diretamente"""
        return any(term in message for term in self.document_terms)
    
    def _is_general_document_inquiry(self, message: str) -> bool:
        """Detecta perguntas gerais que precisam de contexto do documento"""
        has_inquiry = any(keyword in message for keyword in self.inquiry_keywords)
        is_question = any(char in message for char in ['?', 'qual', 'como', 'o que'])
        
        return has_inquiry or is_question
    
    def _has_contextual_references(self, message: str) -> bool:
        """Detecta pronomes que referenciam contexto anterior"""
        return any(pronoun in message for pronoun in self.contextual_pronouns)
    
    def _has_document_context(self, chat_history: List[Dict[str, str]]) -> bool:
        """Verifica se há contexto do documento nas mensagens recentes"""
        recent_messages = chat_history[-6:]  # Últimas 6 mensagens
        
        for msg in recent_messages:
            if msg.get('role') == 'assistant':
                content = msg.get('content', '').lower()
                if any(term in content for term in ['zep', 'graphiti', 'documento', 'página']):
                    return True
        
        return False
    
    def _has_inquiry_pattern(self, message: str) -> bool:
        """Detecta padrões de consulta"""
        return any(keyword in message for keyword in self.inquiry_keywords)
    
    def _llm_transformation(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Transformação com LLM - usada apenas quando necessário
        """
        try:
            # Contexto reduzido para economizar tokens
            recent_context = self._build_minimal_context(chat_history[-4:])
            
            prompt = f"""Transforme a mensagem em uma pergunta específica sobre documentos acadêmicos.

REGRAS:
1. Se menciona "Zep", mantenha como está
2. Se é pergunta geral, adicione "Sobre o Zep:"
3. Se referencia conversa anterior, combine contextos
4. Seja conciso e direto

CONTEXTO RECENTE:
{recent_context}

MENSAGEM: {message}

RESPONDA APENAS COM A PERGUNTA TRANSFORMADA:"""

            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS_QUERY_TRANSFORM,
                temperature=0.0
            )
            
            transformed = response.choices[0].message.content.strip()
            
            # Limpeza pós-LLM
            transformed = self._clean_llm_output(transformed)
            
            logger.debug(f"LLM transform: '{message}' → '{transformed}'")
            return transformed
            
        except Exception as e:
            logger.error(f"Erro na transformação LLM: {e}")
            return self._safe_fallback(message)
    
    def _build_minimal_context(self, recent_messages: List[Dict[str, str]]) -> str:
        """Constrói contexto mínimo para economizar tokens"""
        context_parts = []
        
        for msg in recent_messages:
            role = msg.get('role', '')
            content = msg.get('content', '')[:100]  # Limita a 100 chars
            
            if role in ['user', 'assistant']:
                context_parts.append(f"{role.title()}: {content}")
        
        return "\n".join(context_parts)
    
    def _clean_llm_output(self, output: str) -> str:
        """Limpa saída do LLM"""
        # Remove prefixos comuns
        prefixes = ['rag query:', 'query:', 'pergunta:', 'question:']
        
        for prefix in prefixes:
            if output.lower().startswith(prefix):
                output = output[len(prefix):].strip()
        
        # Remove aspas extras
        output = output.strip('"\'')
        
        return output
    
    def _safe_fallback(self, message: str) -> str:
        """Fallback seguro quando tudo mais falha"""
        if 'zep' in message.lower():
            return message
        else:
            return f"Sobre o documento Zep: {message}"
    
    def _create_cache_key(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """Cria chave de cache baseada na mensagem e contexto"""
        # Contexto simplificado para cache
        recent_topics = []
        for msg in chat_history[-3:]:
            content = msg.get('content', '').lower()
            if 'zep' in content:
                recent_topics.append('zep')
            if 'graphiti' in content:
                recent_topics.append('graphiti')
        
        context_key = '+'.join(set(recent_topics))
        return f"{message.lower()[:50]}||{context_key}"
    
    def _get_last_user_message(self, chat_history: List[Dict[str, str]]) -> str:
        """Pega última mensagem do usuário"""
        for msg in reversed(chat_history):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""
    
    def needs_rag(self, transformed_query: str) -> bool:
        """Verifica se precisa fazer RAG"""
        return "not applicable" not in transformed_query.lower()
    
    def clean_query(self, transformed_query: str) -> str:
        """Limpa query final"""
        return transformed_query.strip()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Estatísticas do cache para monitoramento"""
        return {
            "cache_size": len(self.transformation_cache),
            "cache_hits": getattr(self, '_cache_hits', 0),
            "llm_calls": getattr(self, '_llm_calls', 0)
        }

class ProductionConversationalRAG:
    """
    Sistema RAG conversacional otimizado para produção
    """
    
    def __init__(self) -> None:
        """Inicializa com configurações de produção"""
        load_dotenv()

        # Validação de ambiente
        required_vars = [
            "VOYAGE_API_KEY", "OPENAI_API_KEY",
            "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente ausentes: {missing_vars}")

        # Inicialização dos clientes
        voyageai.api_key = os.environ["VOYAGE_API_KEY"]
        self.voyage_client = voyageai.Client()
        self.openai_client = OpenAI()
        
        # Transformador otimizado para produção
        self.query_transformer = ProductionQueryTransformer(self.openai_client)
        
        # Histórico da conversa
        self.chat_history: List[Dict[str, str]] = []

        # Conexão com Astra DB
        self._initialize_database()
        
        logger.info("Sistema RAG de produção inicializado com sucesso")

    def _initialize_database(self):
        """Inicializa conexão com base de dados"""
        try:
            logger.info("Conectando ao Astra DB...")
            client = DataAPIClient()
            database = client.get_database(
                os.environ["ASTRA_DB_API_ENDPOINT"], 
                token=os.environ["ASTRA_DB_APPLICATION_TOKEN"]
            )
            self.collection = database.get_collection(COLLECTION_NAME)
            
            # Teste de conectividade
            list(self.collection.find({}, limit=1))
            logger.info(f"Conectado ao Astra DB - Collection '{COLLECTION_NAME}' acessível")
                
        except Exception as e:
            logger.error(f"Falha ao conectar Astra DB: {e}")
            raise

    def ask(self, user_message: str) -> str:
        """Interface conversacional principal otimizada"""
        try:
            # Adiciona mensagem do usuário ao histórico
            self.chat_history.append({"role": "user", "content": user_message})
            
            # Transforma em query RAG
            transformed_query = self.query_transformer.transform_query(self.chat_history)
            
            # Verifica se precisa fazer RAG
            if not self.query_transformer.needs_rag(transformed_query):
                response = self._generate_non_rag_response(user_message)
            else:
                # Limpa a query e faz RAG
                clean_query = self.query_transformer.clean_query(transformed_query)
                logger.info(f"Fazendo RAG para: '{clean_query}'")
                
                rag_result = self.search_and_answer(clean_query)
                
                if "error" in rag_result:
                    response = f"Desculpe, não consegui encontrar informações sobre isso. {rag_result['error']}"
                else:
                    response = rag_result["answer"]
            
            # Adiciona resposta ao histórico
            self.chat_history.append({"role": "assistant", "content": response})
            
            # Limita histórico para controle de memória
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-16:]
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            return "Desculpe, ocorreu um erro interno. Tente novamente."

    def _generate_non_rag_response(self, user_message: str) -> str:
        """Gera resposta para mensagens que não precisam de RAG"""
        greetings = ["oi", "olá", "hello", "hi", "boa tarde", "bom dia", "boa noite"]
        
        if any(greeting in user_message.lower() for greeting in greetings):
            return "Olá! Sou seu assistente para consultas sobre documentos acadêmicos. Como posso ajudar você hoje?"
        
        thanks = ["obrigado", "obrigada", "thanks", "valeu"]
        if any(thank in user_message.lower() for thank in thanks):
            return "De nada! Fico feliz em ajudar. Há mais alguma coisa que gostaria de saber?"
        
        return "Como posso ajudar você com consultas sobre os documentos? Faça uma pergunta específica e eu buscarei as informações relevantes."

    # Métodos de RAG originais (mantidos para compatibilidade)
    def get_query_embedding(self, query: str) -> List[float]:
        """Gera embedding para a consulta"""
        try:
            res = self.voyage_client.multimodal_embed(
                inputs=[[query]],
                model="voyage-multimodal-3",
                input_type="query"
            )
            return res.embeddings[0]
        except Exception as e:
            logger.error(f"Erro embedding consulta: {e}")
            raise

    @staticmethod
    def encode_image_to_base64(image_path: str) -> Optional[str]:
        """Converte imagem local em base64"""
        try:
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Imagem não encontrada: {image_path}")
                return None
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Erro codificando {image_path}: {e}")
            return None

    def search_candidates(self, query_embedding: List[float], limit: int = MAX_CANDIDATES) -> List[dict]:
        """Busca candidatos no Astra DB"""
        try:
            logger.debug("Buscando similaridade no Astra DB...")
            
            cursor = self.collection.find(
                {},
                sort={"$vector": query_embedding},
                limit=limit,
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
                candidates.append({
                    "file_path": doc.get("file_path"),
                    "page_num": doc.get("page_num"),
                    "doc_source": doc.get("doc_source"),
                    "markdown_text": doc.get("markdown_text", ""),
                    "similarity_score": doc.get("$similarity", 0.0),
                })
            
            logger.info(f"Busca retornou {len(candidates)} candidatos")
            return candidates
        except Exception as e:
            logger.error(f"Erro busca Astra DB: {e}")
            return []

    def verify_relevance(self, query: str, selected: List[dict]) -> bool:
        """Verifica relevância do contexto selecionado"""
        if not selected:
            return False

        try:
            logger.debug("Verificando relevância do contexto...")
            context_text = "\n\n".join(
                f"=== PÁGINA {c['page_num']} ===\n{c['markdown_text']}"
                for c in selected
            )

            prompt = (
                f"Analise o conteúdo para responder: \"{query}\"\n\n"
                f"Conteúdo:\n---\n{context_text}\n---\n\n"
                "O conteúdo contém resposta factual para a pergunta? "
                "Responda apenas 'Sim' ou 'Não'."
            )

            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0
            )
            
            verification_result = response.choices[0].message.content or ""
            logger.debug(f"Verificação de relevância: '{verification_result}'")
            
            return "sim" in verification_result.lower()

        except Exception as e:
            logger.error(f"Erro na verificação de relevância: {e}")
            return True  # Fallback conservador

    def rerank_with_gpt(self, query: str, candidates: List[dict]) -> Tuple[List[dict], str]:
        """Re-ranking com GPT-4"""
        if not candidates:
            return [], "Nenhuma página disponível."

        if len(candidates) == 1:
            c = candidates[0]
            doc_name = os.path.basename(c["file_path"]).replace(".png", "")
            return [c], f"Única página {doc_name}, p.{c['page_num']}."

        try:
            pages_info = ", ".join(
                f"{os.path.basename(c['file_path']).replace('.png','')} (p.{c['page_num']})"
                for c in candidates
            )
            
            prompt_head = (
                f"Pergunta: '{query}'.\n"
                f"Páginas ({len(candidates)}): {pages_info}.\n"
                "Selecione apenas a página mais relevante. "
                "Máximo 2 páginas se absolutamente necessário.\n\n"
                "Formato:\n"
                "Páginas_Selecionadas: [nº] ou [nº1, nº2]\n"
                "Justificativa: …"
            )
            content = [{"type": "text", "text": prompt_head}]

            for cand in candidates:
                b64 = self.encode_image_to_base64(cand["file_path"])
                if not b64:
                    continue
                    
                preview = cand["markdown_text"][:300]
                text_block = (
                    f"\n=== {os.path.basename(cand['file_path']).replace('.png','').upper()} "
                    f"- PÁGINA {cand['page_num']} ===\n"
                    f"Score: {cand['similarity_score']:.4f}\n"
                    f"Texto: {preview}{'…' if len(cand['markdown_text'])>300 else ''}\n"
                )
                content.append({"type": "text", "text": text_block})
                content.append({"type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}"}})

            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=MAX_TOKENS_RERANK,
                temperature=0.0
            )
            
            result = response.choices[0].message.content or ""
            logger.debug(f"Re-ranker: {result}")

            # Parse da resposta
            selected_nums: List[int] = []
            justification = "Justificativa ausente."
            
            for line in result.splitlines():
                if line.lower().startswith("páginas_selecionadas"):
                    selected_nums = [int(n) for n in re.findall(r"\d+", line)]
                elif line.startswith("Justificativa:"):
                    justification = line.replace("Justificativa:", "").strip()

            chosen = [c for c in candidates if c["page_num"] in selected_nums]
            if chosen:
                return chosen, justification
                
            logger.warning("Re-ranker não selecionou páginas válidas")
            return [candidates[0]], "Fallback: usando candidato mais similar."

        except Exception as e:
            logger.error(f"Erro re-ranking: {e}")
            return [candidates[0]], "Fallback: erro no re-ranker."

    def generate_conversational_answer(self, query: str, selected: List[dict]) -> str:
        """Gera resposta conversacional otimizada"""
        try:
            no_md = "NÃO use formatação Markdown como **, _, #. Escreva texto corrido."
            
            if len(selected) == 1:
                c = selected[0]
                doc = os.path.basename(c["file_path"]).split("_page_")[0]
                
                prompt = (
                    f"Assistente especializado em documentos acadêmicos.\n"
                    f"Pergunta: {query}\n\n"
                    f"Use APENAS a página {c['page_num']} do documento '{doc}'.\n"
                    f"Texto da página:\n{c['markdown_text']}\n\n"
                    f"Instruções: resposta clara e direta. Cite: documento '{doc}', página {c['page_num']}.\n"
                    f"{no_md}"
                )
                content = [{"type": "text", "text": prompt}]
                
                b64 = self.encode_image_to_base64(c["file_path"])
                if b64:
                    content.append({"type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{b64}"}})

            else:
                pages_str = " e ".join(
                    f"{os.path.basename(c['file_path']).split('_page_')[0]} p.{c['page_num']}"
                    for c in selected
                )
                combined_text = "\n\n".join(
                    f"=== PÁGINA {c['page_num']} ===\n{c['markdown_text']}"
                    for c in selected
                )
                
                prompt = (
                    f"Pergunta: {query}\n\n"
                    f"Use páginas: {pages_str}\n"
                    f"{combined_text}\n\n"
                    f"Integre informações. Cite fontes. {no_md}"
                )
                content = [{"type": "text", "text": prompt}]
                
                for c in selected:
                    b64 = self.encode_image_to_base64(c["file_path"])
                    if b64:
                        content.append({"type": "text", "text": f"\n--- PÁGINA {c['page_num']} ---"})
                        content.append({"type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{b64}"}})

            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=MAX_TOKENS_ANSWER,
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro gerando resposta: {e}")
            return f"Erro ao processar resposta: {e}"

    def search_and_answer(self, query: str) -> dict:
        """Pipeline completo RAG"""
        logger.info(f"Consulta: '{query}'")
        
        try:
            embedding = self.get_query_embedding(query)
        except Exception as e:
            return {"error": f"Embedding falhou: {e}"}

        candidates = self.search_candidates(embedding)
        if not candidates:
            return {"error": "Nenhuma página relevante encontrada."}

        logger.debug("Re-rankeando candidatos...")
        selected, justification = self.rerank_with_gpt(query, candidates)
        if not selected:
            return {"error": "Re-ranking falhou."}

        if not self.verify_relevance(query, selected):
            logger.warning("Verificação de relevância indicou baixa relevância")
            return {
                "error": "A informação solicitada não foi encontrada de forma explícita no documento."
            }

        logger.debug("Gerando resposta final...")
        answer = self.generate_conversational_answer(query, selected)

        # Prepara detalhes da resposta
        sel_details = [
            {
                "document": os.path.basename(c["file_path"]).split("_page_")[0],
                "page_number": c["page_num"],
                "similarity_score": c["similarity_score"],
            }
            for c in selected
        ]
        
        all_details = [
            {
                "document": os.path.basename(c["file_path"]).split("_page_")[0],
                "page_number": c["page_num"],
                "similarity_score": c["similarity_score"],
            }
            for c in candidates
        ]
        
        sel_str = " + ".join(
            f"{p['document']} (p.{p['page_number']})" for p in sel_details
        )

        return {
            "query": query,
            "selected_pages": sel_str,
            "selected_pages_details": sel_details,
            "selected_pages_count": len(selected),
            "justification": justification,
            "answer": answer,
            "total_candidates": len(candidates),
            "all_candidates": all_details,
        }

    def extract_structured_data(self, template: dict, document_filter: Optional[str] = None) -> dict:
        """Extração de dados estruturados"""
        try:
            # Busca páginas relevantes
            if document_filter:
                pages_cursor = self.collection.find(
                    {"doc_source": document_filter},
                    limit=10,
                    projection={
                        "file_path": True,
                        "page_num": True,
                        "doc_source": True,
                        "markdown_text": True
                    }
                )
            else:
                pages_cursor = self.collection.find(
                    {},
                    limit=10,
                    projection={
                        "file_path": True,
                        "page_num": True,
                        "doc_source": True,
                        "markdown_text": True
                    }
                )
            
            pages = list(pages_cursor)
            if not pages:
                return {"error": "Nenhuma página encontrada"}
            
            # Prepara prompt de extração
            template_str = json.dumps(template, indent=2)
            
            content = [{
                "type": "text",
                "text": f"""
Extraia dados estruturados seguindo este template: {template_str}

Se informação não disponível, deixe em branco.
Responda APENAS com JSON válido.

DOCUMENTOS:"""
            }]
            
            # Adiciona páginas (limitado para não exceder tokens)
            for page in pages[:5]:
                doc_name = page.get("doc_source", "documento")
                page_num = page.get("page_num", 0)
                content_text = page.get("markdown_text", "")[:500]
                
                content.append({
                    "type": "text",
                    "text": f"\n=== {doc_name.upper()} - PÁGINA {page_num} ===\n{content_text}\n"
                })
                
                # Adiciona imagem se disponível
                img_b64 = self.encode_image_to_base64(page.get("file_path"))
                if img_b64:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                    })
            
            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": content}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            extracted_data = json.loads(response.choices[0].message.content)
            
            return {
                "status": "success",
                "data": extracted_data,
                "pages_analyzed": len(pages)
            }
            
        except Exception as e:
            logger.error(f"Erro na extração de dados: {e}")
            return {
                "status": "error",
                "message": f"Erro na extração: {e}"
            }

    def clear_history(self):
        """Limpa histórico da conversa"""
        self.chat_history = []
        logger.info("Histórico de conversa limpo")

    def get_chat_history(self) -> List[Dict[str, str]]:
        """Retorna histórico atual"""
        return self.chat_history.copy()

    def get_system_stats(self) -> Dict[str, Any]:
        """Estatísticas do sistema para monitoramento"""
        stats = {
            "chat_history_length": len(self.chat_history),
            "transformer_stats": self.query_transformer.get_cache_stats(),
            "system_health": "operational"
        }
        
        try:
            # Teste de conectividade
            list(self.collection.find({}, limit=1))
            stats["database_status"] = "connected"
        except:
            stats["database_status"] = "error"
            stats["system_health"] = "degraded"
        
        return stats

# Wrapper para compatibilidade com código existente
class ConversationalMultimodalRAG(ProductionConversationalRAG):
    """Alias para compatibilidade com código existente"""
    pass

# Classe simples para interface externa
class SimpleRAG:
    """Interface simplificada para uso externo"""
    
    def __init__(self):
        self.rag = ProductionConversationalRAG()
    
    def search(self, query: str) -> str:
        """Busca simples"""
        return self.rag.ask(query)
    
    def extract(self, template: dict, document: str = None) -> dict:
        """Extrai dados estruturados"""
        return self.rag.extract_structured_data(template, document)
    
    def clear_chat(self):
        """Limpa histórico"""
        self.rag.clear_history()

# Interface CLI otimizada para produção
def main() -> None:
    """Interface CLI com tratamento de erros robusto"""
    try:
        rag = ProductionConversationalRAG()
        
        print("🚀 SISTEMA RAG CONVERSACIONAL - PRODUÇÃO 🚀")
        print("=" * 70)
        print("✨ Otimizações de produção ativas:")
        print("  • Query transformer inteligente")
        print("  • Cache de transformações")
        print("  • Logging estruturado")
        print("  • Fallbacks robustos")
        print("=" * 70)

        print(rag.ask("Olá!"))
        print()

        while True:
            try:
                user_input = input("💬 Você: ").strip()
                
                if user_input.lower() in {"sair", "exit", "quit", "/quit"}:
                    print("👋 Até logo!")
                    break
                
                if not user_input:
                    continue
                
                # Comandos especiais
                if user_input.startswith("/"):
                    if user_input == "/help":
                        print_production_help()
                    elif user_input == "/clear":
                        rag.clear_history()
                        print("🧹 Histórico limpo!")
                    elif user_input == "/stats":
                        stats = rag.get_system_stats()
                        print("📊 Estatísticas do sistema:")
                        for key, value in stats.items():
                            print(f"  {key}: {value}")
                    elif user_input.startswith("/extract"):
                        handle_production_extract_command(rag, user_input)
                    else:
                        print("❓ Comando não reconhecido. Digite /help")
                    continue

                # Resposta normal
                print("\n🤖 Assistente: ", end="")
                try:
                    response = rag.ask(user_input)
                    print(response)
                except Exception as e:
                    logger.error(f"Erro no processamento: {e}")
                    print("❌ Erro temporário. Tente novamente.")
                print()

            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro na interface: {e}")
                print("❌ Erro na interface. Continuando...")

    except Exception as e:
        logger.critical(f"Erro fatal: {e}")
        print(f"❌ Erro fatal na inicialização: {e}")
        print("Verifique:")
        print("1. Arquivo .env com chaves corretas")
        print("2. Conexão com Astra DB")
        print("3. Documentos indexados")

def print_production_help():
    """Ajuda para versão de produção"""
    print("""
📚 COMANDOS DE PRODUÇÃO:
• /help     - Esta ajuda
• /clear    - Limpa histórico
• /stats    - Estatísticas do sistema
• /extract  - Extração de dados
  Exemplo: /extract {"title": "", "authors": []}

💡 RECURSOS DE PRODUÇÃO:
• Cache de transformações (economia de custos)
• Fallbacks automáticos (maior robustez)
• Logging estruturado (monitoramento)
• Validação de ambiente (segurança)

🔍 TIPOS DE CONSULTA OTIMIZADOS:
• Perguntas diretas sobre o Zep
• Referências contextuais ("como funciona isso?")
• Consultas técnicas específicas
• Seguimento de conversas anteriores
""")

def handle_production_extract_command(rag, command):
    """Manipula extração de dados na versão de produção"""
    try:
        if len(command.split(" ", 1)) < 2:
            print("💡 Uso: /extract {\"campo\": \"valor\"}")
            print("📝 Exemplo: /extract {\"title\": \"\", \"methodology\": \"\"}")
            return
        
        template_str = command.split(" ", 1)[1]
        template = json.loads(template_str)
        
        print("🔍 Extraindo dados (produção)...")
        result = rag.extract_structured_data(template)
        
        if result.get("status") == "success":
            print("✅ Extração bem-sucedida:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
            print(f"📊 Páginas analisadas: {result['pages_analyzed']}")
        else:
            print(f"❌ Erro: {result.get('message')}")
            
    except json.JSONDecodeError:
        print("❌ JSON inválido. Use aspas duplas!")
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
        print(f"❌ Erro: {e}")

# Para monitoramento em produção
def health_check() -> Dict[str, str]:
    """Health check para monitoramento"""
    try:
        rag = ProductionConversationalRAG()
        stats = rag.get_system_stats()
        
        return {
            "status": "healthy" if stats["system_health"] == "operational" else "degraded",
            "database": stats["database_status"],
            "cache_size": str(stats["transformer_stats"]["cache_size"]),
            "timestamp": str(datetime.now())
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": str(datetime.now())
        }

# Aliases para compatibilidade
MultimodalRagSearcher = ProductionConversationalRAG  # Para avaliador
EnhancedMultimodalRagSearcher = ProductionConversationalRAG  # Para sistemas melhorados

__all__ = [
    'ProductionConversationalRAG', 
    'ConversationalMultimodalRAG',
    'SimpleRAG', 
    'MultimodalRagSearcher',
    'health_check'
]

if __name__ == "__main__":
    main()