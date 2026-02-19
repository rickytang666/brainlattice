from google import genai
from core.config import get_settings
from services.llm.providers import get_gemini_client
from services.embedding_service import EmbeddingService
from sqlalchemy.orm import Session
from db import models
from typing import List, Optional
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class NodeNoteService:
    """
    generates concise, obsidian-style research notes for graph nodes using rag.
    """
    
    def __init__(self):
        self.client = get_gemini_client()
        self.model_id = 'gemini-2.0-flash'
        self.embedder = EmbeddingService()

    async def generate_note(self, db: Session, project_id: str, concept_id: str, outbound_links: List[str] = None) -> str:
        """
        generates a short, lowercase research note for a concept using retrieved context chunks.
        """
        # 1. retrieve context via RAG
        context_chunks = self._get_context(db, project_id, concept_id)
        
        # 2. prepare prompt
        links_str = ", ".join([f"[[{link}]]" for link in (outbound_links or [])])
        
        prompt = f"""
summarize the concept '{concept_id}' based on the provided context chunks.
strict requirements:
1. use obsidian markdown syntax.
2. mention all related concepts using double brackets: {links_str}
3. use latex for any mathematical formulas or technical symbols (e.g. $e = mc^2$).
4. strictly lowercase output.
5. short and concise research notes. max 5 sentences.
6. if the context is insufficient, use your general knowledge to write a high-quality academic note.

context chunks:
{context_chunks}

note:
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    "temperature": 0.2
                }
            )
            
            note_content = response.text.strip().lower()
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
