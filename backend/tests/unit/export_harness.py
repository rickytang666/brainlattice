"""fakes for driving ExportProcessor without a database, model, or storage."""
import asyncio
import uuid

import httpx
import openai
import pytest

from db import models
from services import export_processor, storage_service
from services.export_processor import ExportProcessor

PROJECT_ID = uuid.uuid4()
REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


def client_error(code=400):
    return openai.BadRequestError("bad request", response=httpx.Response(code, request=REQUEST), body=None)


def timeout():
    return openai.APITimeoutError(request=REQUEST)


def empty_note():
    # a per-note failure: other notes can still succeed
    return ValueError("model returned an empty note")


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args):
        return self

    def limit(self, n):
        return FakeQuery(self.rows[:n])

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)

    def count(self):
        return len(self.rows)


class FakeDB:
    def __init__(self, project, nodes):
        self.project = project
        self.nodes = nodes
        self.commits = 0

    def query(self, model):
        if model is models.Project:
            return FakeQuery([self.project])
        if model is models.GraphNode.concept_id:
            return FakeQuery([(n.concept_id,) for n in self.nodes])
        return FakeQuery(self.nodes)

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def close(self):
        pass


class FakeNotes:
    """fails each concept in `failures` with its error; counts calls per concept"""

    def __init__(self, failures, delay=0.0):
        self.failures = failures
        self.delay = delay
        self.calls = {}
        self.prepared = []
        self.in_flight = 0
        self.max_in_flight = 0
        self.timings = {}

    def prepare_contexts(self, project_id, concept_ids):
        self.prepared.append(list(concept_ids))
        return ["context" for _ in concept_ids]

    async def generate_note(self, concept_id, context_chunks, valid_concept_ids, outbound_links=None):
        self.calls[concept_id] = self.calls.get(concept_id, 0) + 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            if concept_id in self.failures:
                raise self.failures[concept_id]()
            return f"# {concept_id}\nreal note"
        finally:
            self.in_flight -= 1


class FakeStorage:
    def __init__(self):
        self.uploads = {}

    def upload_file(self, content, key):
        self.uploads[key] = content


@pytest.fixture
def harness(monkeypatch):
    def build(concepts, failures, content=None, stored_providers=frozenset(), openai_key=None, delay=0.0):
        project = models.Project(id=PROJECT_ID, title="bio", project_metadata={"export": {"status": "pending"}})
        nodes = [
            models.GraphNode(project_id=PROJECT_ID, concept_id=c, content=(content or {}).get(c), aliases=[])
            for c in concepts
        ]
        db = FakeDB(project, nodes)
        storage = FakeStorage()
        monkeypatch.setattr(export_processor, "SessionLocal", lambda: db)
        monkeypatch.setattr(storage_service, "get_storage_service", lambda: storage)

        def pending(self, _db, exhausted):
            return FakeQuery(
                [n for n in nodes if not ExportProcessor._has_note(n) and n.concept_id not in exhausted]
            )

        monkeypatch.setattr(ExportProcessor, "_pending_query", pending)
        monkeypatch.setattr(ExportProcessor, "_stored_embedding_providers", lambda self, _db: set(stored_providers))

        processor = ExportProcessor(
            project_id=str(PROJECT_ID), user_id="u", gemini_key="test-key", openai_key=openai_key
        )
        processor.note_service = FakeNotes(failures, delay=delay)
        enqueued = []

        async def enqueue():
            enqueued.append(1)

        processor._enqueue_next_step = enqueue
        return processor, project, nodes, storage, enqueued

    return build


def run_until_done(processor, max_steps=20):
    for _ in range(max_steps):
        result = asyncio.run(processor.process())
        if result["export_status"] != "batch_partial":
            return result
    raise AssertionError("export never finished")


def export_meta(project):
    return project.project_metadata["export"]
