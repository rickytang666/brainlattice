from google import genai
from services.embedding_service import EmbeddingService
from services.llm.prompt_service import get_prompt_service
from services.llm.utils import repair_note_markdown
from db.session import SessionLocal
from db import models
from typing import List
import asyncio
import logging
import time
from collections import defaultdict
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

class NodeNoteService:
    """
    generates concise, obsidian-style study notes for graph nodes using rag.
    student-focused: essential content, formulas from chunks when possible.
    """

    def __init__(self, gemini_key: str, openai_key: str = None):
        if not gemini_key:
            raise ValueError("gemini_key is required for NodeNoteService. Strict BYOK is enabled.")
        self.client = genai.Client(api_key=gemini_key)
        self.model_id = 'gemini-2.5-flash-lite'
        self.embedder = EmbeddingService(gemini_key=gemini_key, openai_key=openai_key)
        self.prompts = get_prompt_service()
        # seconds summed across notes; concurrent notes overlap, so these can exceed wall-clock
        self.timings: dict[str, float] = defaultdict(float)

    def embed_concepts(self, concept_ids: List[str]) -> List[List[float]]:
        """rag query vectors for many concepts in one batched call"""
        start = time.perf_counter()
        try:
            return self.embedder.get_embeddings(concept_ids)
        finally:
            self.timings["rag_embedding"] += time.perf_counter() - start

    async def generate_note(
        self,
        project_id: str,
        concept_id: str,
        query_vector: List[float],
        valid_concept_ids: set[str],
        outbound_links: List[str] | None = None,
    ) -> str:
        """
        Generates a short, study-focused note for a concept.
        Targeted synthesis - always uses RAG (top 3-5 chunks), no context cache.
        """
        # the search is blocking db io; on the event loop it would stall every other note's request
        context_chunks = await asyncio.to_thread(self._get_context, project_id, concept_id, query_vector)
        chunk_count = len(context_chunks.split("\n\n")) if context_chunks else 0
        logger.info(f"retrieved {chunk_count} RAG chunks for {concept_id}")

        links_str = ", ".join([f"[[{link}]]" for link in (outbound_links or [])])

        prompt = self.prompts.render(
            "node_note.jinja",
            concept_id=concept_id,
            links_str=links_str,
            context_chunks=context_chunks,
        )

        # failures propagate: a placeholder note would be saved and shipped as if it were real
        config = {"temperature": 0.0}
        llm_start = time.perf_counter()
        try:
            response = await self._generate_content_with_retry(prompt, config)
        finally:
            self.timings["llm"] += time.perf_counter() - llm_start

        note_content = (response.text or "").strip().lower()
        if not note_content:
            raise ValueError(f"model returned an empty note for {concept_id}")
        note_content = repair_note_markdown(note_content, valid_concept_ids=valid_concept_ids)

        # append missing links to content
        if outbound_links:
            lower_content = note_content.lower()
            missing_links = [link for link in outbound_links if f"[[{link.lower()}]]" not in lower_content]

            if missing_links:
                note_content += "\n\n## related\n\n" + "\n".join([f"- [[{link}]]" for link in missing_links])

        logger.info(f"successfully generated {len(note_content)} chars for {concept_id} (included {len(outbound_links) if outbound_links else 0} links)")
        return note_content

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def _generate_content_with_retry(self, prompt: str, config: dict):
        return await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=config
        )

    def _get_context(self, project_id: str, concept_id: str, query_vector: List[float]) -> str:
        """rag: vector search for top 5 chunks relevant to concept_id."""
        start = time.perf_counter()
        # runs in a worker thread, and sessions can't be shared across threads
        db = SessionLocal()
        try:
            # find top relevant chunks across all files in the project
            chunks = db.query(models.Chunk).join(models.File).filter(
                models.File.project_id == project_id
            ).order_by(
                models.Chunk.embedding.cosine_distance(query_vector)
            ).limit(5).all()

            if not chunks:
                return "no specific course context found."

            return "\n\n".join([c.content for c in chunks])

        except Exception as e:
            logger.error(f"failed to retrieve context for {concept_id}: {e}")
            return ""
        finally:
            db.close()
            self.timings["rag_search"] += time.perf_counter() - start
