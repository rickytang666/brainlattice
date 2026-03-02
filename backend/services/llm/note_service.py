from google import genai
from core.config import get_settings
from services.embedding_service import EmbeddingService
from services.llm.prompt_service import get_prompt_service
from services.llm.utils import repair_note_markdown
from sqlalchemy.orm import Session
from db import models
from typing import List, Optional
import logging

settings = get_settings()
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
        self.model_id = 'gemini-2.0-flash'
        self.embedder = EmbeddingService(gemini_key=gemini_key, openai_key=openai_key)
        self.prompts = get_prompt_service()

    async def generate_note(self, db: Session, project_id: str, concept_id: str, outbound_links: List[str] = None, cache_name: Optional[str] = None) -> str:
        """
        generates a short, study-focused note for a concept.
        uses gemini context caching when available, otherwise falls back to rag chunks.
        """
        if cache_name:
            context_chunks = "document context is cached natively in the model."
            logger.info(f"attempting to use context cache {cache_name} for {concept_id}")
        else:
            context_chunks = self._get_context(db, project_id, concept_id)
            logger.info(f"no cache provided, retrieved {len(context_chunks.split(chr(10)*2)) if context_chunks else 0} fallback chunks for {concept_id}")
            
        links_str = ", ".join([f"[[{link}]]" for link in (outbound_links or [])])
        
        prompt = self.prompts.render(
            "node_note.jinja",
            concept_id=concept_id,
            links_str=links_str,
            context_chunks=context_chunks
        )

        try:
            config = {"temperature": 0.0}
            if cache_name:
                config["cached_content"] = cache_name

            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=config
                )
            except Exception as cache_err:
                if cache_name:
                    logger.warning(f"cache {cache_name} failed or expired for {concept_id}, falling back to RAG: {cache_err}")
                    # dynamically switch to RAG fallback
                    context_chunks = self._get_context(db, project_id, concept_id)
                    logger.info(f"retrieved {len(context_chunks.split(chr(10)*2)) if context_chunks else 0} fallback chunks for {concept_id}")
                    
                    # re-render prompt with text chunks instead of cache stub
                    prompt = self.prompts.render(
                        "node_note.jinja",
                        concept_id=concept_id,
                        links_str=links_str,
                        context_chunks=context_chunks
                    )
                    
                    # retry without cached_content
                    del config["cached_content"]
                    response = await self.client.aio.models.generate_content(
                        model=self.model_id,
                        contents=prompt,
                        config=config
                    )
                else:
                    raise cache_err
            
            note_content = response.text.strip().lower()
            valid_ids = {n.concept_id for n in db.query(models.GraphNode).filter(
                models.GraphNode.project_id == project_id
            ).all()}
            note_content = repair_note_markdown(note_content, valid_concept_ids=valid_ids)

            # unify related links logic: append missing links to content
            if outbound_links:
                lower_content = note_content.toLowerCase() if hasattr(note_content, 'toLowerCase') else note_content.lower()
                missing_links = [link for link in outbound_links if f"[[{link.lower()}]]" not in lower_content]
                
                if missing_links:
                    note_content += "\n\n## related\n\n" + "\n".join([f"- [[{link}]]" for link in missing_links])

            logger.info(f"successfully generated {len(note_content)} chars for {concept_id} (included {len(outbound_links) if outbound_links else 0} links)")
            return note_content
            
        except Exception as e:
            logger.error(f"failed to generate note for {concept_id}: {e}")
            return f"failed to generate note for {concept_id}."

    def _get_context(self, db: Session, project_id: str, concept_id: str) -> str:
        """performs vector search to find relevant context for the concept"""
        try:
            # 1. get query embedding
            query_vector = self.embedder.get_embedding(concept_id)
            
            # 2. find top relevant chunks across all files in the project
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
