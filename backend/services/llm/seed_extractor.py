"""
SeedExtractor: extract canonical concept IDs from document headers.
Uses OpenRouter (cheap model). OpenRouter key is REQUIRED (no fallback).
"""
import json
import logging
from typing import List

from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from services.llm.prompt_service import get_prompt_service

logger = logging.getLogger(__name__)


class SeedExtractor:
    """
    Extracts a canonical concept ID list from document headers (H1/H2/H3).
    Requires OpenRouter API key (BYOK). No fallback.
    """

    OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct"

    def __init__(self, openrouter_key: str):
        if not openrouter_key:
            raise ValueError(
                "OpenRouter API key is required for SeedExtractor. "
                "There is no fallback. Add it via config (web app or CLI)."
            )
        self._client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        self.prompts = get_prompt_service()

    async def extract_seed_from_headers(self, header_text: str) -> List[str]:
        """
        Convert document headers into canonical concept IDs.
        Returns a list of strings (e.g. ["calculus", "limit", "derivative"]).
        """
        if not header_text.strip():
            logger.warning("empty header text, returning empty seed")
            return []

        prompt = self.prompts.render(
            "global_seed_header.jinja",
            header_text=header_text.strip(),
        )

        try:
            return await self._call_openrouter(prompt)
        except Exception as e:
            logger.error(f"seed extraction failed: {e}")
            return []

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def _call_openrouter(self, prompt: str) -> List[str]:
        response = await self._client.chat.completions.create(
            model=self.OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        return self._parse_json_array(raw)

    def _parse_json_array(self, raw: str) -> List[str]:
        """Parse JSON array from string, handling common wrapper patterns."""
        if raw.startswith("```json"):
            raw = raw[7:-3].strip()
        elif raw.startswith("```"):
            raw = raw[3:-3].strip()
        arr = json.loads(raw)
        if not isinstance(arr, list):
            return []
        return [str(x).strip() for x in arr if x]
