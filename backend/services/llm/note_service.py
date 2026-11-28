from google import genai
from services.embedding_service import EmbeddingService
from services.llm.prompt_service import get_prompt_service
from services.llm.utils import repair_note_markdown
from db.session import SessionLocal
from sqlalchemy import text
from typing import List
import logging
import time
from collections import defaultdict
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

RAG_CHUNKS_PER_NOTE = 5
NO_CONTEXT = "no specific course context found."

# top chunks for every query vector in one round trip rather than one round trip per note
_BATCH_CHUNK_SEARCH = text("""
    select q.ord, c.content
    from unnest(cast(:ords as int[]), cast(:vectors as vector[])) as q(ord, vec)
    cross join lateral (
        select ch.content, ch.embedding <=> q.vec as distance
        from chunks ch
        join files f on ch.file_id = f.id
        where f.project_id = cast(:project_id as uuid)
        order by ch.embedding <=> q.vec
        limit :per_note
    ) c
    order by q.ord, c.distance
""")


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

    def prepare_contexts(self, project_id: str, concept_ids: List[str]) -> List[str]:
        """rag context for each concept: one batched embedding call, then one batched vector search"""
        if not concept_ids:
            return []
        embed_start = time.perf_counter()
        try:
            vectors = self.embedder.get_embeddings(concept_ids)
        finally:
            self.timings["rag_embedding"] += time.perf_counter() - embed_start

        search_start = time.perf_counter()
        # called from a worker thread, and sessions can't be shared across threads
        db = SessionLocal()
        try:
            rows = db.execute(_BATCH_CHUNK_SEARCH, {
                "ords": list(range(len(vectors))),
                "vectors": ["[" + ",".join(map(str, v)) + "]" for v in vectors],
                "project_id": str(project_id),
                "per_note": RAG_CHUNKS_PER_NOTE,
            }).all()
        finally:
            db.close()
            self.timings["rag_search"] += time.perf_counter() - search_start

        chunks_by_concept: List[List[str]] = [[] for _ in concept_ids]
        for ord_, content in rows:
            chunks_by_concept[ord_].append(content)
        return ["\n\n".join(chunks) if chunks else NO_CONTEXT for chunks in chunks_by_concept]

    async def generate_note(
        self,
        concept_id: str,
        context_chunks: str,
        valid_concept_ids: set[str],
        outbound_links: List[str] | None = None,
    ) -> str:
        """
        Generates a short, study-focused note for a concept.
        Targeted synthesis from the chunks prepare_contexts retrieved, no context cache.
        """
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
