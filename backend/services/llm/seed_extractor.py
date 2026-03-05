"""
SeedExtractor: extract canonical concept IDs from document headers.
Uses OpenRouter (cheap model) when available, falls back to Gemini.
"""
import json
import logging
from typing import List, Optional

from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from core.config import get_settings
from services.llm.prompt_service import get_prompt_service

settings = get_settings()
logger = logging.getLogger(__name__)


class SeedExtractor:
    """
    Extracts a canonical concept ID list from document headers (H1/H2/H3).
    Uses OpenRouter for cost efficiency when available.
    """

    OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct"

    def __init__(self, openrouter_key: Optional[str] = None, gemini_key: Optional[str] = None):
        self.openrouter_key = openrouter_key or settings.OPENROUTER_API_KEY
        self.gemini_key = gemini_key
        self.prompts = get_prompt_service()

        if self.openrouter_key:
            self._client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_key,
            )
            self._provider = "openrouter"
        elif self.gemini_key:
            from google import genai
            self._client = genai.Client(api_key=self.gemini_key)
            self._provider = "gemini"
        else:
            raise ValueError(
                "SeedExtractor requires OPENROUTER_API_KEY or gemini_key. "
                "Set OPENROUTER_API_KEY for cheapest extraction."
            )

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
            if self._provider == "openrouter":
                return await self._call_openrouter(prompt)
            else:
                return await self._call_gemini(prompt)
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

    async def _call_gemini(self, prompt: str) -> List[str]:
        response = await self._client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        )
        raw = response.text.strip()
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
