from google import genai
from schemas.graph import GraphData
from services.llm.prompt_service import get_prompt_service
from typing import List
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt


class GraphExtractor:
    """
    extracts knowledge graph (nodes/links) from text using google-genai
    stateful: takes existing concepts to encourage id reuse
    """
    
    def __init__(self, gemini_key: str):
        if not gemini_key:
            raise ValueError("gemini_key is required for GraphExtractor. Strict BYOK is enabled.")
        self.client = genai.Client(api_key=gemini_key)
        self.model_id = 'gemini-2.0-flash'
        self.logger = logging.getLogger(__name__)
        self.prompts = get_prompt_service()

    async def extract_from_skeleton(self, skeleton_text: str) -> GraphData:
        """
        extracts high-level root concepts from a document skeleton string
        """
        prompt = self.prompts.render(
            "skeleton_extraction.jinja",
            skeleton_text=skeleton_text
        )
        return await self._call_llm(prompt)

    async def extract_from_window(self, text_window: str, existing_concepts: List[str] = None) -> GraphData:
        """
        extracts concepts and directed outbound links from a text window
        """
        prompt = self.prompts.render(
            "graph_extraction.jinja",
            existing_concepts=existing_concepts[:500] if existing_concepts else None,
            text_window=text_window
        )
        return await self._call_llm(prompt)

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def _generate_content_with_retry(self, prompt: str, config: dict):
        return await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=config
        )

    async def _call_llm(self, prompt: str) -> GraphData:
        """
        Internal method to call the LLM and parse the response.
        """
        try:
            config = {
                "response_mime_type": "application/json",
                "response_schema": GraphData,
                "temperature": 0.0
            }
            response = await self._generate_content_with_retry(prompt, config)
            
            raw_json = response.text.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3].strip()
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3].strip()
                
            data = json.loads(raw_json)
            
            return GraphData(**data)
            
        except Exception as e:
            self.logger.error(f"graph extraction failed: {e}")
            self.logger.error(f"raw response was: {response.text if 'response' in locals() else 'None'}")
            return GraphData()
