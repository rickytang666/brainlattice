"""
OrphanLinkService: fix degree-0 nodes by suggesting related concepts via cheap LLM.
"""
import json
import logging
from typing import Dict, List, Set

from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from schemas.graph import GraphData
from services.llm.prompt_service import get_prompt_service

logger = logging.getLogger(__name__)


class OrphanLinkService:
    """
    Suggests outbound + inbound links for degree-0 nodes using cheap OpenRouter model.
    Only runs for nodes with 0 outbound AND 0 inbound links.
    No RAG — uses canonical list only.
    """

    OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct"
    MAX_LINKS_PER_DIRECTION = 5

    def __init__(self, openrouter_key: str):
        if not openrouter_key:
            raise ValueError("OpenRouter API key required for OrphanLinkService.")
        self._client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        self.prompts = get_prompt_service()

    async def fix_degree_zero_nodes(self, graph_data: GraphData) -> GraphData:
        """
        For each degree-0 node, ask LLM which concepts relate (outbound + inbound).
        Adds valid links in-place. Returns the same graph_data (modified).
        """
        node_map = {n.id: n for n in graph_data.nodes}
        canonical_ids: Set[str] = set(node_map.keys())
        canonical_list = sorted(canonical_ids)

        orphans = [
            n for n in graph_data.nodes
            if not n.outbound_links and not n.inbound_links
        ]

        if not orphans:
            logger.info("no degree-0 nodes to fix.")
            return graph_data

        logger.info(f"fixing {len(orphans)} degree-0 nodes via orphan link completion...")

        id_lower_to_canonical = {c.lower(): c for c in canonical_ids}

        for node in orphans:
            try:
                result = await self._suggest_links(
                    concept_id=node.id,
                    canonical_list=canonical_list,
                )

                outbound_valid = self._filter_valid(
                    result.get("outbound", []),
                    id_lower_to_canonical,
                    node.id,
                )
                inbound_valid = self._filter_valid(
                    result.get("inbound", []),
                    id_lower_to_canonical,
                    node.id,
                )

                # add outbound: node -> target
                for target_id in outbound_valid[: self.MAX_LINKS_PER_DIRECTION]:
                    if target_id not in node.outbound_links:
                        node.outbound_links.append(target_id)
                    target_node = node_map.get(target_id)
                    if target_node and node.id not in target_node.inbound_links:
                        target_node.inbound_links.append(node.id)

                # add inbound: source -> node (so source gets node in outbound, node gets source in inbound)
                for source_id in inbound_valid[: self.MAX_LINKS_PER_DIRECTION]:
                    if source_id not in node.inbound_links:
                        node.inbound_links.append(source_id)
                    source_node = node_map.get(source_id)
                    if source_node and node.id not in source_node.outbound_links:
                        source_node.outbound_links.append(node.id)

                if outbound_valid or inbound_valid:
                    logger.info(
                        f"orphan '{node.id}' linked: outbound={outbound_valid}, inbound={inbound_valid}"
                    )

            except Exception as e:
                logger.warning(f"orphan link completion failed for {node.id}: {e}")
                continue

        return graph_data

    def _filter_valid(
        self,
        ids: List[str],
        id_lower_to_canonical: Dict[str, str],
        exclude_id: str,
    ) -> List[str]:
        """Filter to valid canonical IDs, exclude self, dedupe."""
        valid = []
        seen = set()
        for rid in ids:
            if not rid:
                continue
            canonical = id_lower_to_canonical.get(str(rid).strip().lower())
            if canonical and canonical != exclude_id and canonical not in seen:
                valid.append(canonical)
                seen.add(canonical)
        return valid

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def _suggest_links(
        self,
        concept_id: str,
        canonical_list: List[str],
    ) -> Dict[str, List[str]]:
        """Call cheap LLM to suggest outbound + inbound links."""
        prompt = self.prompts.render(
            "orphan_link_completion.jinja",
            concept_id=concept_id,
            canonical_list=canonical_list,
        )

        response = await self._client.chat.completions.create(
            model=self.OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        return self._parse_structured(raw)

    def _parse_structured(self, raw: str) -> Dict[str, List[str]]:
        """Parse {"outbound": [...], "inbound": [...]} from string."""
        if raw.startswith("```json"):
            raw = raw[7:].strip()
        if raw.startswith("```"):
            raw = raw[3:].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
        try:
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                return {"outbound": [], "inbound": []}
            outbound = obj.get("outbound", [])
            inbound = obj.get("inbound", [])
            return {
                "outbound": [str(x).strip().lower() for x in outbound if x],
                "inbound": [str(x).strip().lower() for x in inbound if x],
            }
        except json.JSONDecodeError:
            return {"outbound": [], "inbound": []}
