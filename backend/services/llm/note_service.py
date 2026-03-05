from google import genai
from services.embedding_service import EmbeddingService
from services.llm.prompt_service import get_prompt_service
from services.llm.utils import repair_note_markdown
from sqlalchemy.orm import Session
from db import models
from typing import List
import logging
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

    async def generate_note(
        self,
        db: Session,
        project_id: str,
        concept_id: str,
        outbound_links: List[str] | None = None,
    ) -> str:
        """
        Generates a short, study-focused note for a concept.
        Targeted synthesis - always uses RAG (top 3-5 chunks), no context cache.
        """
        context_chunks = self._get_context(db, project_id, concept_id)
        chunk_count = len(context_chunks.split("\n\n")) if context_chunks else 0
        logger.info(f"retrieved {chunk_count} RAG chunks for {concept_id}")

        links_str = ", ".join([f"[[{link}]]" for link in (outbound_links or [])])

        prompt = self.prompts.render(
            "node_note.jinja",
            concept_id=concept_id,
            links_str=links_str,
            context_chunks=context_chunks,
        )

        try:
            config = {"temperature": 0.0}
            response = await self._generate_content_with_retry(prompt, config)

            note_content = response.text.strip().lower()
            valid_ids = {n.concept_id for n in db.query(models.GraphNode).filter(
                models.GraphNode.project_id == project_id
            ).all()}
            note_content = repair_note_markdown(note_content, valid_concept_ids=valid_ids)

            # append missing links to content
            if outbound_links:
                lower_content = note_content.lower()
                missing_links = [link for link in outbound_links if f"[[{link.lower()}]]" not in lower_content]
                
                if missing_links:
                    note_content += "\n\n## related\n\n" + "\n".join([f"- [[{link}]]" for link in missing_links])

            logger.info(f"successfully generated {len(note_content)} chars for {concept_id} (included {len(outbound_links) if outbound_links else 0} links)")
            return note_content
            
        except Exception as e:
            logger.error(f"failed to generate note for {concept_id}: {e}")
            return f"failed to generate note for {concept_id}."

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def _generate_content_with_retry(self, prompt: str, config: dict):
        return await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=config
        )

    def _get_context(self, db: Session, project_id: str, concept_id: str) -> str:
        """RAG: vector search for top 5 chunks relevant to concept_id."""
        try:
            # get query embedding
            query_vector = self.embedder.get_embedding(concept_id)
            
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
