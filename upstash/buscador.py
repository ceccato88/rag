# buscador.py

import os
import re
import base64
import logging
from typing import List, Tuple, Optional
from dotenv import load_dotenv

import voyageai
from openai import OpenAI
from PIL import Image
from upstash_vector import Index          # Upstash Vector SDK

# ───────────────────────── Configurações ──────────────────────────
LLM_MODEL = "gpt-4.1" 
MAX_CANDIDATES = 5            # top-k da busca vetorial antes do re-rank
MAX_TOKENS_RERANK = 512       # margem para justificativa
MAX_TOKENS_ANSWER = 2048      # resposta final mais longa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ───────────────────────── Classe principal ──────────────────────────
class MultimodalRagSearcher:
    def __init__(self) -> None:
        """Inicializa clientes Voyage, OpenAI e Upstash."""
        load_dotenv()

        required = [
            "VOYAGE_API_KEY", "OPENAI_API_KEY",
            "UPSTASH_VECTOR_REST_URL", "UPSTASH_VECTOR_REST_TOKEN"
        ]
        for k in required:
            if not os.getenv(k):
                raise ValueError(f"Chave {k} não encontrada em .env")

        voyageai.api_key = os.environ["VOYAGE_API_KEY"]
        self.voyage_client = voyageai.Client()
        self.openai_client = OpenAI()

        try:
            logger.info("Conectando ao Upstash Vector…")
            self.upstash_client = Index.from_env()
            info = self.upstash_client.info()
            logger.info("Conectado. Vetores no índice: %d", info.vector_count)
        except Exception as e:
            logger.error("Falha ao conectar Upstash: %s", e)
            raise

        logger.info("Sistema RAG pronto!")

    # ───────── Embedding da consulta ─────────
    def get_query_embedding(self, query: str) -> List[float]:
        """Gera embedding SOMENTE de texto para a consulta."""
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
        """Converte imagem local em base64, retorna None se não existir."""
        try:
            if not image_path or not os.path.exists(image_path):
                logger.warning("Imagem não encontrada: %s", image_path)
                return None
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error("Erro codificando %s: %s", image_path, e)
            return None

    # ───────── Busca vetorial ─────────
    def search_candidates(
        self, query_embedding: List[float], limit: int = MAX_CANDIDATES
    ) -> List[dict]:
        """Retorna lista de páginas candidatas com metadados."""
        try:
            logger.info("Buscando similaridade no Upstash…")
            hits = self.upstash_client.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
                include_vectors=False
            )
            candidates = []
            for hit in hits or []:
                md = hit.metadata or {}
                candidates.append({
                    "file_path": md.get("file_path"),
                    "page_num": md.get("page_num"),
                    "doc_source": md.get("doc_source"),
                    "markdown_text": md.get("markdown_text", ""),
                    "similarity_score": hit.score,
                })
            logger.info("Busca retornou %d candidatos", len(candidates))
            return candidates
        except Exception as e:
            logger.error("Erro busca Upstash: %s", e)
            return []
    
    # ───────── Verificação de Relevância ─────────
    def verify_relevance(self, query: str, selected: List[dict]) -> bool:
        """Verifica se a resposta está de fato no contexto selecionado."""
        if not selected:
            return False

        try:
            logger.info("Verificando a relevância do contexto selecionado...")
            context_text = "\n\n".join(
                f"=== PÁGINA {c['page_num']} ===\n{c['markdown_text']}"
                for c in selected
            )

            # --- TRECHO ALTERADO: Prompt de verificação mais explícito ---
            prompt = (
                f"Analise o Conteúdo da Página para responder à Pergunta do Usuário: \"{query}\"\n\n"
                f"Conteúdo da(s) página(s) selecionada(s):\n---\n{context_text}\n---\n\n"
                "A página contém a resposta factual e explícita para a pergunta? "
                "Não considere apenas a relevância do tópico. Responda apenas com 'Sim' ou 'Não'."
            )

            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0
            )
            verification_result = response.choices[0].message.content or ""
            logger.info("Resultado da verificação de relevância: '%s'", verification_result)
            
            return "sim" in verification_result.lower()

        except Exception as e:
            logger.error("Erro na verificação de relevância: %s", e)
            return True

    # ───────── Re-ranking com GPT ─────────
    def rerank_with_gpt(
        self, query: str, candidates: List[dict]
    ) -> Tuple[List[dict], str]:
        """Escolhe 1–2 páginas mais relevantes via GPT-4."""
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
                f"Você é um assistente especialista. Pergunta: '{query}'.\n"
                f"Abaixo estão {len(candidates)} páginas: {pages_info}.\n"
                "Analise e selecione apenas a página mais relevante que contenha a resposta completa. Somente selecione uma segunda página se for absolutamente impossível responder com apenas uma.\n"
                "Nunca selecione mais de 2 páginas.\n\n"
                "Formato exato:\n"
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
                    f"Trecho: {preview}{'…' if len(cand['markdown_text'])>300 else ''}\n"
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
            logger.info("Resposta re-ranker: %s", result)

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
            logger.warning("Re-ranker não selecionou páginas válidas; usando a mais similar.")
            return [candidates[0]], "Fallback: re-ranker não selecionou páginas."

        except Exception as e:
            logger.error("Erro re-ranking: %s", e)
            return [candidates[0]], "Fallback: erro no re-ranker."

    # ───────── Geração da resposta final ─────────
    def generate_final_answer(
        self, query: str, selected: List[dict]
    ) -> str:
        """Constrói prompt multimodal para resposta definitiva."""
        try:
            no_md = "- NÃO use formatação Markdown como **, _, #. Escreva texto corrido."
            if len(selected) == 1:
                c = selected[0]
                doc = os.path.basename(c["file_path"]).split("_page_")[0]
                prompt = (
                    f"Você é um assistente especializado em documentos acadêmicos.\n"
                    f"Pergunta: {query}\n\n"
                    f"Use APENAS a página {c['page_num']} do documento '{doc}' abaixo.\n"
                    f"Texto da página:\n{c['markdown_text']}\n\n"
                    f"Instruções: se a resposta estiver presente, explique; caso contrário, diga que falta informação.\n"
                    f"Mencione que a resposta vem do documento '{doc}', página {c['page_num']}.\n"
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
                    f"Use APENAS as páginas {pages_str} abaixo.\n"
                    f"{combined_text}\n\n"
                    f"Integre informações das duas páginas.\n"
                    f"{no_md}"
                )
                content = [{"type": "text", "text": prompt}]
                for c in selected:
                    b64 = self.encode_image_to_base64(c["file_path"])
                    if b64:
                        content.append({"type": "text",
                                        "text": f"\n--- IMAGEM PÁG {c['page_num']} ---"})
                        content.append({"type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{b64}"}})

            response = self.openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=MAX_TOKENS_ANSWER,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Erro gerando resposta final: %s", e, exc_info=True)
            return f"Ocorreu um erro ao gerar a resposta: {e}"

    # ───────── Pipeline completo ─────────
    def search_and_answer(self, query: str) -> dict:
        logger.info("Consulta: '%s'", query)
        try:
            embedding = self.get_query_embedding(query)
        except Exception as e:
            return {"error": f"Embedding falhou: {e}"}

        candidates = self.search_candidates(embedding)
        if not candidates:
            return {"error": "Nenhuma página relevante encontrada."}

        logger.info("Re-rankeando…")
        selected, justification = self.rerank_with_gpt(query, candidates)
        if not selected:
            return {"error": "Re-ranking falhou em selecionar uma página."}

        if not self.verify_relevance(query, selected):
            logger.warning(
                "Verificação de relevância indicou que a resposta não está no contexto. "
                "Interrompendo para evitar resposta incorreta."
            )
            return {
                "error": "A informação solicitada não foi encontrada de forma explícita no documento."
            }

        logger.info("Gerando resposta final…")
        answer = self.generate_final_answer(query, selected)

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

# ───────────────────────── Interface CLI ──────────────────────────
def main() -> None:
    try:
        searcher = MultimodalRagSearcher()
        print("🚀 BUSCADOR RAG MULTIMODAL (Upstash Vector) 🚀")
        print("=" * 60)

        while True:
            user_q = input("💬 Sua pergunta: ").strip()
            if user_q.lower() in {"sair", "exit", "quit"}:
                print("👋 Até logo!")
                break
            if not user_q:
                continue

            print("\n" + "─" * 60 + "\n🔍 Processando…")
            result = searcher.search_and_answer(user_q)

            if "error" in result:
                print("❌", result["error"])
                continue

            print("\n📄 Páginas selecionadas:", result["selected_pages"])
            print("🤖 Justificativa:", result["justification"])
            print("\n📝 RESPOSTA:\n" + "═" * 60)
            print(result["answer"])
            print("═" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n👋 Até logo!")
    except Exception as e:
        logger.critical("Erro fatal: %s", e, exc_info=True)
        print("❌ Erro fatal:", e)

__all__ = ['MultimodalRagSearcher']

if __name__ == "__main__":
    main()
