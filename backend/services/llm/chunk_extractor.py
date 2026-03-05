"""
ChunkExtractor: extract GraphData (nodes/edges) from a text chunk using OpenRouter.
Step 2 Map phase - per-chunk extraction with seed list for cross-chunk linking.
"""
import json
import logging
from typing import List, Optional

from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from pydantic import ValidationError
from schemas.graph import GraphData
from services.llm.prompt_service import get_prompt_service

logger = logging.getLogger(__name__)


class ChunkExtractor:
    """
    Extracts raw nodes/edges from a text chunk using OpenRouter (cheap model).
    Requires OpenRouter API key (BYOK). Uses seed list for cross-chunk link consistency.
    """

    OPENROUTER_MODEL = "google/gemma-3n-e4b-it"

    def __init__(self, openrouter_key: str):
        if not openrouter_key:
            raise ValueError(
                "OpenRouter API key is required for ChunkExtractor. "
                "Add it via config (web app or CLI)."
            )
        self._client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        self.prompts = get_prompt_service()

    async def extract_from_chunk(
        self,
        chunk_text: str,
        seed_list: Optional[List[str]] = None,
    ) -> GraphData:
        """
        Extract nodes from a single chunk. Returns GraphData.
        """
        if not chunk_text.strip():
            return GraphData(nodes=[])

        prompt = self.prompts.render(
            "chunk_extraction.jinja",
            chunk_text=chunk_text.strip(),
            seed_list=seed_list or [],
        )

        try:
            raw = await self._call_openrouter(prompt)
            return self._parse_graph_data(raw)
        except Exception as e:
            logger.error(f"chunk extraction failed: {e}")
            return GraphData(nodes=[])

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def _call_openrouter(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self.OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()

    def _parse_graph_data(self, raw: str) -> GraphData:
        """Parse JSON to GraphData, handling common wrapper patterns."""
        if raw.startswith("```json"):
            raw = raw[7:-3].strip()
        elif raw.startswith("```"):
            raw = raw[3:-3].strip()
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "nodes" in data:
                return GraphData(**data)
            if isinstance(data, list):
                return GraphData(nodes=data)
            return GraphData(nodes=[])
        except (json.JSONDecodeError, TypeError, ValidationError) as e:
            logger.warning(f"failed to parse chunk extraction response: {e}")
            return GraphData(nodes=[])
