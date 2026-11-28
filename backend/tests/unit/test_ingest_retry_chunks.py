"""a retried ingest must reuse the chunks a previous attempt saved, not store or embed them again."""
import asyncio
import uuid

import httpx
import openai
import pytest

import core.logger  # noqa: F401  registers logger.success, which the pipeline calls
from db import models
from schemas.graph import GraphData
from services import ingestion_processor
from services.chunking_service import RecursiveMarkdownSplitter

PROJECT_ID = uuid.uuid4()
FILE_KEY = "uploads/photosynthesis.pdf"
MARKDOWN = "# Light reactions\nThylakoids split water.\n# Calvin cycle\nRubisco fixes carbon.\n# Stroma\nFluid."
REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


class FakeQuery:
    def __init__(self, db, entities):
        self.db = db
        self.entities = entities

    def filter(self, *args):
        return self

    def first(self):
        model = self.entities[0]
        if model is models.File:
            return self.db.files[0] if self.db.files else None
        return None

    def all(self):
        # only the (content, embedding_provider) column query reads chunks this way
        return [(c.content, c.embedding_provider) for c in self.db.chunks]

    def delete(self, synchronize_session=None):
        removed = len(self.db.chunks)
        self.db.chunks = []
        return removed


class FakeDB:
    """one shared store across attempts, like the real database"""

    def __init__(self):
        self.files = []
        self.chunks = []

    def query(self, *entities):
        return FakeQuery(self, entities)

    def add(self, row):
        if isinstance(row, models.File):
            row.id = uuid.uuid4()
            self.files.append(row)

    def add_all(self, rows):
        self.chunks.extend(rows)

    def flush(self):
        pass

    def commit(self):
        pass

    def close(self):
        pass


class FakeJobs:
    def __init__(self):
        self.metadata = {"project_id": str(PROJECT_ID), "filename": "photosynthesis.pdf"}
        self.status = None

    def get_job(self, job_id):
        return {"metadata": dict(self.metadata)}

    def update_progress(self, job_id, status, progress=None, details=None):
        self.status = status

    def update_metadata(self, job_id, updates):
        self.metadata.update(updates)

    def get_extraction_cache(self, job_id):
        return None

    def set_extraction_cache(self, job_id, data):
        pass


class FakeEmbedder:
    calls = []

    def __init__(self, gemini_key=None, openai_key=None):
        self.provider = "gemini"

    def get_embeddings(self, texts):
        FakeEmbedder.calls.append(list(texts))
        return [[0.0] * 1536 for _ in texts]


class FakeStorage:
    def download_file(self, key):
        return b"%PDF-fake"


class FakePDF:
    def extract_content(self, path):
        return MARKDOWN


class FakeBuilder:
    resolver = None

    def build(self, graphs):
        return GraphData(nodes=[])


class FakeConnector:
    _embeddings = None

    def connect_orphans(self, graph):
        return graph


class FakeValidator:
    def __init__(self, openrouter_key=None):
        pass

    async def get_invalid_concepts(self, ids):
        return set()


class FakeOrphans:
    def __init__(self, openrouter_key=None):
        pass

    async def fix_degree_zero_nodes(self, graph):
        return graph


class FakePersistence:
    def __init__(self, db):
        pass

    def save_graph(self, project_id, graph):
        pass


@pytest.fixture
def pipeline(monkeypatch):
    db = FakeDB()
    jobs = FakeJobs()
    FakeEmbedder.calls = []
    monkeypatch.setattr(ingestion_processor, "SessionLocal", lambda: db)
    monkeypatch.setattr(ingestion_processor, "get_storage_service", lambda: FakeStorage())
    monkeypatch.setattr(ingestion_processor, "get_job_service", lambda: jobs)
    monkeypatch.setattr(ingestion_processor, "PDFService", FakePDF)
    monkeypatch.setattr(ingestion_processor, "EmbeddingService", FakeEmbedder)
    monkeypatch.setattr(ingestion_processor, "GraphBuilder", FakeBuilder)
    monkeypatch.setattr(ingestion_processor, "GraphConnector", FakeConnector)
    monkeypatch.setattr(ingestion_processor, "ConceptValidator", FakeValidator)
    monkeypatch.setattr(ingestion_processor, "OrphanLinkService", FakeOrphans)
    monkeypatch.setattr(ingestion_processor, "GraphPersistenceService", FakePersistence)

    def run(extraction_error=None):
        async def extract(self, text, gemini_key=None, openrouter_key=None):
            if extraction_error:
                raise extraction_error
            return [], {"extraction_chunks": 1, "failed_chunks": 0}

        monkeypatch.setattr(ingestion_processor.IngestionProcessor, "_run_graph_extraction", extract)
        processor = ingestion_processor.IngestionProcessor(
            job_id=f"job-{uuid.uuid4()}",
            file_key=FILE_KEY,
            gemini_key="test-key",
            openrouter_key="test-key",
            retry_pending=True,
        )
        return asyncio.run(processor.process())

    return db, jobs, run


def expected_texts():
    return sorted(c.page_content for c in RecursiveMarkdownSplitter().split_text(MARKDOWN))


def stored_texts(db):
    return sorted(c.content for c in db.chunks)


class TestRetriedIngest:
    def test_retry_after_extraction_timeout_keeps_one_set_of_chunks(self, pipeline):
        db, jobs, run = pipeline
        with pytest.raises(openai.APITimeoutError):
            run(extraction_error=openai.APITimeoutError(request=REQUEST))
        assert jobs.status == "processing"

        result = run()

        assert jobs.status == "completed"
        assert len(db.files) == 1
        assert stored_texts(db) == expected_texts()
        assert result["chunks"] == len(expected_texts())

    def test_retry_does_not_embed_saved_chunks(self, pipeline):
        db, _, run = pipeline
        with pytest.raises(openai.APITimeoutError):
            run(extraction_error=openai.APITimeoutError(request=REQUEST))
        run()

        assert len(FakeEmbedder.calls) == 1

    def test_partial_set_is_replaced_with_a_full_one(self, pipeline):
        db, _, run = pipeline
        with pytest.raises(openai.APITimeoutError):
            run(extraction_error=openai.APITimeoutError(request=REQUEST))
        db.chunks = db.chunks[:1]

        run()

        assert stored_texts(db) == expected_texts()
        assert len(FakeEmbedder.calls) == 2

    def test_doubled_set_from_an_earlier_retry_is_collapsed(self, pipeline):
        db, _, run = pipeline
        with pytest.raises(openai.APITimeoutError):
            run(extraction_error=openai.APITimeoutError(request=REQUEST))
        db.chunks += [
            models.Chunk(file_id=c.file_id, content=c.content, embedding_provider=c.embedding_provider)
            for c in db.chunks
        ]

        run()

        assert stored_texts(db) == expected_texts()
        assert len(FakeEmbedder.calls) == 2

    def test_chunks_from_another_provider_are_replaced(self, pipeline):
        db, _, run = pipeline
        with pytest.raises(openai.APITimeoutError):
            run(extraction_error=openai.APITimeoutError(request=REQUEST))
        for chunk in db.chunks:
            chunk.embedding_provider = "openai"

        run()

        assert stored_texts(db) == expected_texts()
        assert {c.embedding_provider for c in db.chunks} == {"gemini"}
