from google import genai
from core.config import get_settings
from schemas.graph import GraphData
from services.llm.prompt_service import get_prompt_service
from typing import List
import json
import logging

settings = get_settings()

class GraphExtractor:
    """
    extracts knowledge graph (nodes/links) from text using google-genai
    stateful: takes existing concepts to encourage id reuse
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = 'gemini-2.0-flash'
        self.logger = logging.getLogger(__name__)
        self.prompts = get_prompt_service()

    async def extract_from_window(self, text_window: str, existing_concepts: List[str] = None) -> GraphData:
        """
        extracts concepts and directed outbound links from a text window
        """
        prompt = self.prompts.render(
            "graph_extraction.jinja",
            existing_concepts=existing_concepts[:500] if existing_concepts else None,
            text_window=text_window
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
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
