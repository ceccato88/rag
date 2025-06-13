# buscador_otimizado.py

import os
import re
import base64
import logging
from typing import List, Tuple, Optional
from dotenv import load_dotenv

import voyageai
from openai import OpenAI
from PIL import Image
from astrapy import DataAPIClient

# ───────────────────────── Configurações Otimizadas ──────────────────────────
LLM_MODEL = "gpt-4.1"              # GPT-4.1 (mais inteligente)
MAX_INITIAL_FETCH = 8               # Fase 1: Busca ampla (era 5)
MAX_FINAL_SELECTION = 2             # Fase 2: Seleção final
MAX_TOKENS_RERANK = 512            
MAX_TOKENS_ANSWER = 2048           
COLLECTION_NAME = "pdf_documents"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ───────────────────────── Classe Otimizada ──────────────────────────
class OptimizedMultimodalRagSearcher:
    def __init__(self) -> None:
        """Inicializa com GPT-4.1 e lógica de duas fases."""
        load_dotenv()

        required = [
            "VOYAGE_API_KEY", "OPENAI_API_KEY",
            "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN"
        ]
        for k in required:
            if not os.getenv(k):
                raise ValueError(f"Chave {k} não encontrada em .env")

        voyageai.api_key = os.environ["VOYAGE_API_KEY"]
        self.voyage_client = voyageai.Client()
        self.openai_client = OpenAI()

        try:
            logger.info("Conectando ao Astra DB…")
            client = DataAPIClient()
            database = client.get_database(
                os.environ["ASTRA_DB_API_ENDPOINT"], 
                token=os.environ["ASTRA_DB_APPLICATION_TOKEN"]
            )
            self.collection = database.get_collection(COLLECTION_NAME)
            
            try:
                list(self.collection.find({}, limit=1))
                logger.info("✅ Conectado ao Astra DB - Collection '%s' acessível", COLLECTION_NAME)
            except Exception:
                logger.error("❌ Collection '%s' não encontrada ou inacessível", COLLECTION_NAME)
                raise
                
        except Exception as e:
            logger.error("Falha ao conectar Astra DB: %s", e)
            raise

        logger.info("🚀 Sistema RAG Otimizado pronto com GPT-4.1!")

    # ───────── Embedding da consulta ─────────
    def get_query_embedding(self, query: str) -> List[float]:
        """Gera embedding de texto para a consulta."""
        try:
            res = self.voyage_client.multimodal_embed(
                inputs=[[query]],
                model="voyage-multimodal-3",
                input_type="query"
            )
            return res.embeddings[0]
        except Exception as e:
            logger.error("Erro embedding consulta: %s", e)
            raise

    # ───────── Utilidades de imagem ─────────
    @staticmethod
    def encode_image_to_base64(image_path: str) -> Optional[str]:
        """Converte imagem local em base64."""
        try:
            if not image_path or not os.path.exists(image_path):
                logger.warning("Imagem não encontrada: %s", image_path)
                return None
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error("Erro codificando %s: %s", image_path, e)
            return None

    # ───────── FASE 1: Busca Ampla ─────────
    def phase1_broad_search(self, query_embedding: List[float]) -> List[dict]:
        """
        FASE 1: Busca ampla - "Cast a Wide Net"
        Busca mais candidatos para não perder documentos relevantes.
        """
        try:
            logger.info("🌐 FASE 1: Busca ampla (top-%d candidatos)...", MAX_INITIAL_FETCH)
            
            cursor = self.collection.find(
                {},
                sort={"$vector": query_embedding},
                limit=MAX_INITIAL_FETCH,  # Busca mais candidatos
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
            
            logger.info("📊 Fase 1 retornou %d candidatos", len(candidates))
            
            # Log dos scores para análise
            for i, c in enumerate(candidates):
                logger.info("   Candidato %d: Página %d, Score=%.4f", 
                           i+1, c['page_num'], c['similarity_score'])
            
            return candidates
        except Exception as e:
            logger.error("Erro na Fase 1: %s", e)
            return []

    # ───────── FASE 2: Seleção Precisa com GPT-4.1 ─────────
    def phase2_precise_reranking(self, query: str, candidates: List[dict]) -> Tuple[List[dict], str]:
        """
        FASE 2: Seleção precisa - "Be Selective"
        Usa GPT-4.1 para escolher os melhores candidatos da Fase 1.
        """
        if not candidates:
            return [], "Nenhum candidato da Fase 1."

        if len(candidates) == 1:
            c = candidates[0]
            doc_name = os.path.basename(c["file_path"]).replace(".png", "")
            return [c], f"Único candidato {doc_name}, p.{c['page_num']}."

        try:
            logger.info("🎯 FASE 2: Seleção precisa com GPT-4.1 (%d → %d)...", 
                       len(candidates), MAX_FINAL_SELECTION)
            
            pages_info = ", ".join(
                f"{os.path.basename(c['file_path']).replace('.png','')} (p.{c['page_num']}, score={c['similarity_score']:.3f})"
                for c in candidates
            )
            
            # Prompt otimizado para GPT-4.1
            prompt_head = (
                f"Você é um assistente especialista usando GPT-4.1 para seleção precisa de documentos.\n\n"
                f"PERGUNTA: '{query}'\n\n"
                f"CANDIDATOS da Fase 1 ({len(candidates)} páginas): {pages_info}\n\n"
                f"TAREFA:\n"
                f"Analise cada página e selecione APENAS as mais relevantes que contenham informação específica para responder à pergunta.\n"
                f"- Priorize páginas com informação direta e factual\n"
                f"- Máximo {MAX_FINAL_SELECTION} páginas\n"
                f"- Se uma página já responde completamente, não selecione outras\n\n"
                f"FORMATO DE RESPOSTA:\n"
                f"Páginas_Selecionadas: [nº] ou [nº1, nº2]\n"
                f"Justificativa: Explique brevemente por que essas páginas são as melhores\n"
                f"Confidence: Alta/Média/Baixa"
            )
            
            content = [{"type": "text", "text": prompt_head}]

            # Adicionar contexto visual de cada candidato
            for cand in candidates:
                b64 = self.encode_image_to_base64(cand["file_path"])
                if not b64:
                    continue
                    
                preview = cand["markdown_text"][:400]  # Mais contexto
                text_block = (
                    f"\n=== PÁGINA {cand['page_num']} ===\n"
                    f"Documento: {os.path.basename(cand['file_path']).replace('.png','').upper()}\n"
                    f"Similarity Score: {cand['similarity_score']:.4f}\n"
                    f"Conteúdo: {preview}{'…' if len(cand['markdown_text'])>400 else ''}\n"
                )
                content.append({"type": "text", "text": text_block})
                content.append({"type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}"}})

            # Usar GPT-4.1 para seleção precisa
            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,  # GPT-4.1
                messages=[{"role": "user", "content": content}],
                max_tokens=MAX_TOKENS_RERANK,
                temperature=0.0  # Determinístico para consistência
            )
            
            result = response.choices[0].message.content or ""
            logger.info("📝 Resposta GPT-4.1 Fase 2: %s", result)

            # Parser da resposta
            selected_nums: List[int] = []
            justification = "Justificativa ausente."
            confidence = "Média"
            
            for line in result.splitlines():
                line = line.strip()
                if line.lower().startswith("páginas_selecionadas"):
                    selected_nums = [int(n) for n in re.findall(r"\d+", line)]
                elif line.startswith("Justificativa:"):
                    justification = line.replace("Justificativa:", "").strip()
                elif line.startswith("Confidence:"):
                    confidence = line.replace("Confidence:", "").strip()

            # Mapear números selecionados para candidatos
            chosen = [c for c in candidates if c["page_num"] in selected_nums]
            
            if chosen:
                logger.info("✅ Fase 2 selecionou %d páginas: %s (Confidence: %s)", 
                           len(chosen), [c['page_num'] for c in chosen], confidence)
                return chosen, f"{justification} (Confidence: {confidence})"
            else:
                logger.warning("⚠️ GPT-4.1 não selecionou páginas válidas; usando a mais similar.")
                return [candidates[0]], "Fallback: usando candidato com maior similarity."

        except Exception as e:
            logger.error("Erro na Fase 2: %s", e)
            return [candidates[0]], "Fallback: erro na seleção com GPT-4.1."

    # ───────── Verificação de Relevância ─────────
    def verify_relevance(self, query: str, selected: List[dict]) -> bool:
        """Verifica se a resposta está de fato no contexto selecionado."""
        if not selected:
            return False

        try:
            logger.info("🔍 Verificação de relevância...")
            context_text = "\n\n".join(
                f"=== PÁGINA {c['page_num']} ===\n{c['markdown_text']}"
                for c in selected
            )

            prompt = (
                f"Analise o conteúdo para responder: \"{query}\"\n\n"
                f"Conteúdo selecionado:\n---\n{context_text}\n---\n\n"
                f"O conteúdo contém informação factual e específica para responder à pergunta? "
                f"Considere apenas respostas diretas e explícitas.\n"
                f"Responda apenas: 'Sim' ou 'Não'"
            )

            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,  # GPT-4.1 para verificação também
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0
            )
            
            verification_result = response.choices[0].message.content or ""
            logger.info("📋 Verificação de relevância: '%s'", verification_result)
            
            return "sim" in verification_result.lower()

        except Exception as e:
            logger.error("Erro na verificação de relevância: %s", e)
            return True  # Fallback conservador

    # ───────── Geração da resposta final com GPT-4.1 ─────────
    def generate_final_answer(self, query: str, selected: List[dict]) -> str:
        """Constrói resposta final usando GPT-4.1."""
        try:
            logger.info("📝 Gerando resposta final com GPT-4.1...")
            
            no_md = "- NÃO use formatação Markdown como **, _, #. Escreva texto corrido."
            
            if len(selected) == 1:
                c = selected[0]
                doc = os.path.basename(c["file_path"]).split("_page_")[0]
                prompt = (
                    f"Você é um assistente especializado usando GPT-4.1 para análise de documentos acadêmicos.\n\n"
                    f"PERGUNTA: {query}\n\n"
                    f"DOCUMENTO: Use APENAS a página {c['page_num']} do documento '{doc}' abaixo.\n\n"
                    f"CONTEÚDO DA PÁGINA:\n{c['markdown_text']}\n\n"
                    f"INSTRUÇÕES:\n"
                    f"- Responda com base exclusivamente no conteúdo fornecido\n"
                    f"- Se a resposta estiver presente, explique de forma clara e completa\n"
                    f"- Se não estiver, informe que a informação específica não está disponível\n"
                    f"- Mencione que a resposta vem do documento '{doc}', página {c['page_num']}\n"
                    f"- Use linguagem clara e precisa\n"
                    f"{no_md}"
                )
                content = [{"type": "text", "text": prompt}]
                
                b64 = self.encode_image_to_base64(c["file_path"])
                if b64:
                    content.append({"type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}})

            else:
                # Múltiplas páginas
                pages_str = " e ".join(
                    f"{os.path.basename(c['file_path']).split('_page_')[0]} p.{c['page_num']}"
                    for c in selected
                )
                combined_text = "\n\n".join(
                    f"=== PÁGINA {c['page_num']} ===\n{c['markdown_text']}"
                    for c in selected
                )
                prompt = (
                    f"Você é um assistente especializado usando GPT-4.1.\n\n"
                    f"PERGUNTA: {query}\n\n"
                    f"DOCUMENTOS: Use APENAS as páginas {pages_str} abaixo.\n\n"
                    f"CONTEÚDO COMBINADO:\n{combined_text}\n\n"
                    f"INSTRUÇÕES:\n"
                    f"- Integre informações de todas as páginas relevantes\n"
                    f"- Seja claro sobre qual página contém cada informação\n"
                    f"- Se alguma informação estiver ausente, mencione explicitamente\n"
                    f"- Cite as páginas utilizadas na resposta\n"
                    f"{no_md}"
                )
                content = [{"type": "text", "text": prompt}]
                
                for c in selected:
                    b64 = self.encode_image_to_base64(c["file_path"])
                    if b64:
                        content.append({"type": "text", "text": f"\n--- IMAGEM PÁGINA {c['page_num']} ---"})
                        content.append({"type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}})

            # GPT-4.1 para resposta final
            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=MAX_TOKENS_ANSWER,
                temperature=0.1
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Erro gerando resposta final: %s", e, exc_info=True)
            return f"Erro ao gerar resposta com GPT-4.1: {e}"

    # ───────── Pipeline Completo de Duas Fases ─────────
    def search_and_answer(self, query: str) -> dict:
        """Pipeline otimizado com duas fases: Busca Ampla → Seleção Precisa."""
        logger.info("🚀 Iniciando pipeline otimizado de duas fases...")
        logger.info("📝 Consulta: '%s'", query)
        
        try:
            embedding = self.get_query_embedding(query)
        except Exception as e:
            return {"error": f"Embedding falhou: {e}"}

        # FASE 1: Busca ampla
        candidates = self.phase1_broad_search(embedding)
        if not candidates:
            return {"error": "Fase 1: Nenhuma página relevante encontrada."}

        # FASE 2: Seleção precisa com GPT-4.1
        selected, justification = self.phase2_precise_reranking(query, candidates)
        if not selected:
            return {"error": "Fase 2: Falha na seleção precisa."}

        # Verificação de relevância
        if not self.verify_relevance(query, selected):
            logger.warning(
                "❌ Verificação de relevância indicou que a resposta não está no contexto selecionado. "
                "Interrompendo para evitar resposta incorreta."
            )
            return {
                "error": "A informação solicitada não foi encontrada de forma explícita no documento."
            }

        # Geração da resposta final
        logger.info("📝 Gerando resposta final...")
        answer = self.generate_final_answer(query, selected)

        # Preparar detalhes da resposta
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
            "pipeline_info": {
                "phase1_candidates": len(candidates),
                "phase2_selected": len(selected),
                "model_used": LLM_MODEL,
                "optimization": "Two-Phase Retrieval"
            }
        }

# ───────────────────────── Interface CLI ──────────────────────────
def main() -> None:
    try:
        searcher = OptimizedMultimodalRagSearcher()
        print("🚀 RAG OTIMIZADO - Two-Phase Retrieval com GPT-4.1 🚀")
        print("=" * 70)
        print("📊 Configuração: Fase 1 (top-8) → Fase 2 (top-2) → GPT-4.1")
        print("=" * 70)

        while True:
            user_q = input("💬 Sua pergunta: ").strip()
            if user_q.lower() in {"sair", "exit", "quit"}:
                print("👋 Até logo!")
                break
            if not user_q:
                continue

            print("\n" + "─" * 70 + "\n🔍 Processando com pipeline de duas fases...")
            result = searcher.search_and_answer(user_q)

            if "error" in result:
                print("❌", result["error"])
                continue

            print(f"\n📄 Páginas selecionadas: {result['selected_pages']}")
            print(f"🤖 Justificativa: {result['justification']}")
            
            pipeline_info = result.get('pipeline_info', {})
            print(f"⚙️ Pipeline: {pipeline_info.get('phase1_candidates', 0)} → {pipeline_info.get('phase2_selected', 0)} páginas")
            
            print("\n📝 RESPOSTA:\n" + "═" * 70)
            print(result["answer"])
            print("═" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n👋 Até logo!")
    except Exception as e:
        logger.critical("Erro fatal: %s", e, exc_info=True)
        print("❌ Erro fatal:", e)

__all__ = ['OptimizedMultimodalRagSearcher']

if __name__ == "__main__":
    main()