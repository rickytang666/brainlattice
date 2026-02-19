import google.generativeai as genai
from core.config import get_settings
from schemas.graph import GraphData
from typing import List
import json
import logging

settings = get_settings()

# config gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

class GraphExtractor:
    """
    extracts knowledge graph (nodes/links) from text using gemini 2.0 flash.
    stateful: takes existing concepts to encourage ID reuse.
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.logger = logging.getLogger(__name__)

    async def extract_from_window(self, text_window: str, existing_concepts: List[str] = None) -> GraphData:
        """
        extracts concepts and links from a text window.
        """
        existing_list_str = ""
        if existing_concepts:
            existing_list_str = f"Existing Concept IDs (REUSE THESE IF APPLICABLE): {', '.join(existing_concepts[:500])}"

        prompt = f"""
        Analyze the following text and identify key concepts (nodes) and their relationships (links).
        
        {existing_list_str}
        
        Strict Output Rules:
        1. Return ONLY a valid JSON object with key "nodes".
        2. Nodes format: 
           {{
             "id": "concept_name_lowercase", 
             "aliases": ["synonym1", "acronym"],
             "links": ["related_concept_id_1", "related_concept_id_2"]
           }}
        3. IDs must be lowercase, singular.
        4. Links: meaningful connections found IN THIS TEXT or to EXISTING CONCEPTS.
        5. VALIDATE: Ensure every ID in "links" is either in the current "nodes" list OR in the "Existing Concept IDs" list.
        6. REUSE IDs: If a concept in the text matches an ID in the "Existing Concept IDs" list (or is a synonym), use that existing ID.
        
        Text to Analyze:
        """
        
        try:
            response = self.model.generate_content(
                f"{prompt}\n\n{text_window}",
                generation_config={"response_mime_type": "application/json"}
            )
            
            raw_json = response.text
            data = json.loads(raw_json)
            
            return GraphData(**data)
            
        except Exception as e:
            self.logger.error(f"graph extraction failed: {e}")
            return GraphData()
