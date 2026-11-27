"""extraction responses arrive in loose markdown wrappers; truncated fences must still parse,
and chunks that fail anyway are counted rather than silently dropped."""
import asyncio

import pytest

from schemas.graph import GraphData
from services import ingestion_processor
from services.llm.chunk_extractor import ChunkExtractor, ExtractionParseError
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


class TestParseFailuresRaise:
    @pytest.mark.parametrize("raw", ["not json at all", '{"edges": []}', '"just a string"'])
    def test_unreadable_response_raises(self, chunk_extractor, raw):
        with pytest.raises(ExtractionParseError):
            chunk_extractor._parse_graph_data(raw)

    def test_empty_node_list_is_not_a_failure(self, chunk_extractor):
        assert chunk_extractor._parse_graph_data('{"nodes": []}').nodes == []

    def test_provider_error_propagates(self, chunk_extractor, monkeypatch):
        async def boom(prompt):
            raise RuntimeError("openrouter down")

        monkeypatch.setattr(chunk_extractor, "_call_openrouter", boom)
        with pytest.raises(RuntimeError):
            asyncio.run(chunk_extractor.extract_from_chunk("some text"))


class FakeChunk:
    def __init__(self, text):
        self.page_content = text


def run_extraction(monkeypatch, chunk_texts, fail_on):
    class FakeExtractor:
        def __init__(self, openrouter_key):
            pass

        async def extract_from_chunk(self, text, seed_list=None):
            if text in fail_on:
                raise fail_on[text]
            return GraphData(nodes=[{"id": text}])

    monkeypatch.setattr(ingestion_processor, "ChunkExtractor", FakeExtractor)
    monkeypatch.setattr(
        ingestion_processor, "create_extraction_chunks", lambda *a, **kw: [FakeChunk(t) for t in chunk_texts]
    )
    processor = object.__new__(ingestion_processor.IngestionProcessor)
    return asyncio.run(processor._run_graph_extraction("no headers here", openrouter_key="k"))


class TestFailedChunksCounted:
    def test_failed_chunk_counted_not_dropped(self, monkeypatch):
        graphs, stats = run_extraction(
            monkeypatch,
            ["stroma", "thylakoid", "grana"],
            {"thylakoid": ExtractionParseError("garbage")},
        )
        assert [g.nodes[0].id for g in graphs] == ["stroma", "grana"]
        assert stats == {"extraction_chunks": 3, "failed_chunks": 1}

    def test_every_chunk_failing_raises_the_cause(self, monkeypatch):
        cause = RuntimeError("invalid key")
        with pytest.raises(RuntimeError, match="invalid key"):
            run_extraction(monkeypatch, ["a", "b"], {"a": cause, "b": cause})
