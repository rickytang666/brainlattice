"""extraction responses arrive in loose markdown wrappers; truncated fences must still parse."""
import pytest

from services.llm.chunk_extractor import ChunkExtractor
from services.llm.seed_extractor import SeedExtractor
from services.llm.utils import strip_code_fence

GRAPH_JSON = '{"nodes": [{"id": "stroma", "outbound_links": ["thylakoid"]}]}'


@pytest.fixture
def chunk_extractor():
    return ChunkExtractor(openrouter_key="test-key")


class TestStripCodeFence:
    @pytest.mark.parametrize(
        "raw",
        [
            f"```json\n{GRAPH_JSON}\n```",
            f"```json\n{GRAPH_JSON}",
            f"```\n{GRAPH_JSON}",
            f"```JSON {GRAPH_JSON}\n```  ",
            GRAPH_JSON,
        ],
    )
    def test_returns_bare_json(self, raw):
        assert strip_code_fence(raw) == GRAPH_JSON


class TestChunkExtractorParsing:
    def test_unclosed_json_fence_parses(self, chunk_extractor):
        graph = chunk_extractor._parse_graph_data(f"```json\n{GRAPH_JSON}")
        assert [n.id for n in graph.nodes] == ["stroma"]
        assert graph.nodes[0].outbound_links == ["thylakoid"]

    def test_closed_fence_still_parses(self, chunk_extractor):
        graph = chunk_extractor._parse_graph_data(f"```json\n{GRAPH_JSON}\n```")
        assert [n.id for n in graph.nodes] == ["stroma"]

    def test_unclosed_bare_fence_with_list_parses(self, chunk_extractor):
        graph = chunk_extractor._parse_graph_data('```\n[{"id": "grana"}]')
        assert [n.id for n in graph.nodes] == ["grana"]


class TestSeedExtractorParsing:
    def test_unclosed_fence_parses(self):
        seeds = SeedExtractor(openrouter_key="test-key")._parse_json_array('```json\n["stroma", "grana"]')
        assert seeds == ["stroma", "grana"]
