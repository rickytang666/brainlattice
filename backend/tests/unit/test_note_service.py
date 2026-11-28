"""rag context for a whole round comes from one embedding call and one vector search."""
import asyncio
from types import SimpleNamespace

from services.llm import note_service
from services.llm.note_service import NO_CONTEXT, NodeNoteService


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def get_embeddings(self, texts):
        self.calls.append(list(texts))
        return [[float(i), 0.5] for i in range(len(texts))]


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.params = []
        self.closed = False

    def execute(self, statement, params):
        self.params.append(params)
        return FakeResult(self.rows)

    def close(self):
        self.closed = True


class FakeModels:
    def __init__(self, text):
        self.text = text

    async def generate_content(self, model, contents, config):
        return SimpleNamespace(text=self.text)


def service(monkeypatch, rows=(), note_text=""):
    svc = NodeNoteService(gemini_key="test-key")
    svc.embedder = FakeEmbedder()
    svc.client = SimpleNamespace(aio=SimpleNamespace(models=FakeModels(note_text)))
    session = FakeSession(list(rows))
    monkeypatch.setattr(note_service, "SessionLocal", lambda: session)
    return svc, session


class TestPrepareContexts:
    def test_one_embedding_call_and_one_search_for_every_concept(self, monkeypatch):
        rows = [(0, "light reactions"), (0, "photosystem ii"), (2, "calvin cycle")]
        svc, session = service(monkeypatch, rows)

        contexts = svc.prepare_contexts("p1", ["thylakoid", "stroma", "rubisco"])

        assert svc.embedder.calls == [["thylakoid", "stroma", "rubisco"]]
        assert len(session.params) == 1
        assert contexts == ["light reactions\n\nphotosystem ii", NO_CONTEXT, "calvin cycle"]
        assert session.closed

    def test_vectors_sent_in_pgvector_text_form(self, monkeypatch):
        svc, session = service(monkeypatch)
        svc.prepare_contexts("p1", ["a", "b"])
        params = session.params[0]
        assert params["ords"] == [0, 1]
        assert params["vectors"] == ["[0.0,0.5]", "[1.0,0.5]"]
        assert params["project_id"] == "p1"

    def test_no_concepts_skips_both_calls(self, monkeypatch):
        svc, session = service(monkeypatch)
        assert svc.prepare_contexts("p1", []) == []
        assert svc.embedder.calls == [] and session.params == []


class TestGenerateNote:
    def test_links_outside_the_graph_become_plain_text(self, monkeypatch):
        svc, _ = service(monkeypatch, note_text="see [[stroma]] and [[made up]]")

        note = asyncio.run(svc.generate_note("thylakoid", "context", {"thylakoid", "stroma"}))

        assert "[[stroma]]" in note
        assert "[[made up]]" not in note and "made up" in note

    def test_missing_outbound_links_appended(self, monkeypatch):
        svc, _ = service(monkeypatch, note_text="a note")

        note = asyncio.run(svc.generate_note("thylakoid", "context", {"stroma"}, outbound_links=["stroma"]))

        assert note.endswith("## related\n\n- [[stroma]]")
