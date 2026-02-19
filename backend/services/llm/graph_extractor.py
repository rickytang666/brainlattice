from google import genai
from core.config import get_settings
from schemas.graph import GraphData
from typing import List
import json
import logging

settings = get_settings()

class GraphExtractor:
    """
    extracts knowledge graph (nodes/links) from text using google-genai
    stateful: takes existing concepts to encourage ID reuse.
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = 'gemini-2.0-flash'
        self.logger = logging.getLogger(__name__)

    async def extract_from_window(self, text_window: str, existing_concepts: List[str] = None) -> GraphData:
        """
        extracts concepts and directed outbound links from a text window.
        """
        existing_list_str = ""
        if existing_concepts:
            existing_list_str = f"Existing Concept IDs (REUSE THESE IF APPLICABLE): {', '.join(existing_concepts[:500])}"

        prompt = f"""
        Analyze the following text and identify key concepts (nodes) and their directed relationships (outbound links).
        
        {existing_list_str}
        
        Strict Output Rules:
        1. Return ONLY a valid JSON object with key "nodes".
        2. Nodes format: 
           {{
             "id": "concept name lowercase", 
             "aliases": ["synonym1", "acronym"],
             "outbound_links": ["target concept id 1", "target concept id 2"]
           }}
        3. IDs: MUST be lowercase, singular, and use SPACES instead of underscores (e.g. "deep learning", not "deep_learning").
        4. outbound_links: concepts that this node POINTS TO or RELIES ON based on the text.
        5. VALIDATE: Ensure every ID in "outbound_links" is either in the current "nodes" list OR in the "Existing Concept IDs" list.
        6. REUSE IDs: If a concept in the text matches an ID in the "Existing Concept IDs" list (or is a synonym), use that existing ID.
        
        Text to Analyze:
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"{prompt}\n\n{text_window}",
                config={
                    "response_mime_type": "application/json"
                }
            )
            
            raw_json = response.text
            data = json.loads(raw_json)
            
            return GraphData(**data)
            
        except Exception as e:
            self.logger.error(f"graph extraction failed: {e}")
            return GraphData()
