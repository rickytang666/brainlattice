"""
chunkextractor: extract graphdata (nodes/edges) from a text chunk using openrouter.
per-chunk extraction with seed list for cross-chunk linking.
"""
import json
import logging
from typing import List, Optional

from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from pydantic import ValidationError
from schemas.graph import GraphData
from services.llm.prompt_service import get_prompt_service
from services.llm.utils import strip_code_fence

logger = logging.getLogger(__name__)


class ExtractionParseError(ValueError):
    """the model answered, but not with a graph we can read"""


class ChunkExtractor:
    """
    extracts raw nodes/edges from a text chunk using openrouter (cheap model).
    requires openrouter api key (byok). uses seed list for cross-chunk link consistency.
    """

    OPENROUTER_MODEL = "google/gemma-3-27b-it"

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
        extract nodes from a single chunk. returns graphdata.
        """
        if not chunk_text.strip():
            return GraphData(nodes=[])

        prompt = self.prompts.render(
            "chunk_extraction.jinja",
            chunk_text=chunk_text.strip(),
            seed_list=seed_list or [],
        )

        # failures propagate so the caller can count them instead of reading them as empty chunks
        raw = await self._call_openrouter(prompt)
        return self._parse_graph_data(raw)

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def _call_openrouter(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self.OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()

    def _parse_graph_data(self, raw: str) -> GraphData:
        """parse json to graphdata, handling common wrapper patterns."""
        raw = strip_code_fence(raw)
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "nodes" in data:
                return GraphData(**data)
            if isinstance(data, list):
                return GraphData(nodes=data)
        except (json.JSONDecodeError, TypeError, ValidationError) as e:
            raise ExtractionParseError(f"unparseable chunk extraction response: {e}") from e
        raise ExtractionParseError(f"unexpected chunk extraction shape: {type(data).__name__}")
