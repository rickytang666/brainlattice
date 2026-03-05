"""
ConceptValidator: LLM pass to identify invalid concept IDs (metadata, dates, etc.).
C3 — single call per document to clean extraction noise.
"""
import json
import logging
from typing import List, Set

from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from services.llm.prompt_service import get_prompt_service

logger = logging.getLogger(__name__)


class ConceptValidator:
    """
    Identifies invalid concept IDs via LLM.
    Uses a capable model for reliable classification.
    """

    OPENROUTER_MODEL = "meta-llama/llama-4-scout"

    def __init__(self, openrouter_key: str):
        if not openrouter_key:
            raise ValueError("OpenRouter API key required for ConceptValidator.")
        self._client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        self.prompts = get_prompt_service()

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def get_invalid_concepts(self, concept_ids: List[str]) -> Set[str]:
        """
        Return set of concept IDs that are invalid (dates, metadata, etc.).
        """
        if not concept_ids:
            return set()

        concept_list = sorted(set(concept_ids))
        prompt = self.prompts.render(
            "concept_validation.jinja",
            concept_list=concept_list,
        )

        try:
            response = await self._client.chat.completions.create(
                model=self.OPENROUTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            raw = response.choices[0].message.content.strip()
            invalid = self._parse_json_array(raw)

            # only return IDs that were in the original list (case-insensitive)
            id_lower_to_orig = {c.lower(): c for c in concept_ids}
            result = set()
            for x in invalid:
                orig = id_lower_to_orig.get(str(x).strip().lower())
                if orig:
                    result.add(orig)

            if result:
                logger.info(f"validator flagged {len(result)} invalid concepts: {result}")
            return result

        except Exception as e:
            logger.warning(f"concept validation failed: {e}")
            return set()

    def _parse_json_array(self, raw: str) -> List[str]:
        if raw.startswith("```json"):
            raw = raw[7:].strip()
        if raw.startswith("```"):
            raw = raw[3:].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
        try:
            arr = json.loads(raw)
            if not isinstance(arr, list):
                return []
            return [str(x).strip() for x in arr if x]
        except json.JSONDecodeError:
            return []
