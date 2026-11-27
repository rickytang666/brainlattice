"""re-ingesting a project must update graph nodes in place, not wipe their notes."""
import uuid
from pathlib import Path

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import postgresql

from db import models
from schemas.graph import GraphData, GraphNode as GraphNodeSchema
from services.graph.persistence_service import GraphPersistenceService, upsert_nodes_statement

PROJECT_ID = uuid.uuid4()
MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "008_unique_graph_nodes.sql"


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args):
        return self

    def all(self):
        return list(self.rows)


class FakeSession:
    def __init__(self, rows):
        self.rows = list(rows)
        self.statements = []
        self.deleted = []
        self.committed = False

    def query(self, model):
        return FakeQuery(self.rows)

    def delete(self, row):
        self.deleted.append(row)

    def execute(self, statement):
        self.statements.append(statement)

    @property
    def added(self):
        """concept ids the session's upserts would insert, in order"""
        ids = []
        for stmt in self.statements:
            params = stmt.compile(dialect=postgresql.dialect()).params
            keys = [k for k in params if k.startswith("concept_id_m")]
            ids += [params[k] for k in sorted(keys, key=lambda k: int(k.rsplit("_m", 1)[1]))]
        return ids

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def db_node(concept_id, content=None, outbound=None):
    return models.GraphNode(
        project_id=PROJECT_ID,
        concept_id=concept_id,
        content=content,
        aliases=[],
        outbound_links=outbound or [],
        inbound_links=[],
    )


def graph(*nodes):
    return GraphData(nodes=[GraphNodeSchema(id=cid, outbound_links=links) for cid, links in nodes])


class TestReingest:
    def test_surviving_node_keeps_content(self):
        stroma = db_node("stroma", content="# stroma\nfluid of the chloroplast", outbound=["old"])
        session = FakeSession([stroma])

        GraphPersistenceService(session).save_graph(str(PROJECT_ID), graph(("stroma", ["thylakoid"])))

        assert stroma.content == "# stroma\nfluid of the chloroplast"
        assert stroma.outbound_links == ["thylakoid"]
        assert stroma not in session.deleted
        assert session.added == []
        assert session.committed

    def test_new_concepts_added_and_stale_removed(self):
        kept = db_node("stroma", content="note")
        stale = db_node("mitochondria", content="old note")
        session = FakeSession([kept, stale])

        GraphPersistenceService(session).save_graph(
            str(PROJECT_ID), graph(("stroma", []), ("thylakoid", []))
        )

        assert session.added == ["thylakoid"]
        assert session.deleted == [stale]

    def test_legacy_duplicates_collapse_to_the_row_with_content(self):
        empty = db_node("stroma")
        with_note = db_node("stroma", content="note")
        session = FakeSession([empty, with_note])

        GraphPersistenceService(session).save_graph(str(PROJECT_ID), graph(("stroma", [])))

        assert session.deleted == [empty]
        assert with_note.content == "note"
        assert session.added == []

    def test_duplicate_incoming_concept_inserted_once(self):
        session = FakeSession([])

        GraphPersistenceService(session).save_graph(
            str(PROJECT_ID), graph(("stroma", []), ("stroma", ["x"]))
        )

        assert session.added == ["stroma"]


class TestUniqueness:
    def test_model_declares_unique_project_concept(self):
        uniques = [
            tuple(c.name for c in con.columns)
            for con in models.GraphNode.__table__.constraints
            if isinstance(con, UniqueConstraint)
        ]
        assert ("project_id", "concept_id") in uniques

    def test_migration_dedupes_before_adding_constraint(self):
        sql = MIGRATION.read_text()
        dedupe = sql.index("DELETE FROM graph_nodes")
        constraint = sql.index("UNIQUE (project_id, concept_id)")
        assert dedupe < constraint


class TestOverlappingIngest:
    """a concurrent or redelivered ingest may insert the same concept between our read and our write"""

    def compiled(self):
        rows = [{"id": uuid.uuid4(), "project_id": PROJECT_ID, "concept_id": "stroma", "aliases": [],
                 "outbound_links": ["thylakoid"], "inbound_links": [], "node_metadata": {}}]
        return str(upsert_nodes_statement(rows).compile(dialect=postgresql.dialect()))

    def test_insert_conflicts_on_project_concept_instead_of_raising(self):
        assert "ON CONFLICT (project_id, concept_id) DO UPDATE" in self.compiled()

    def test_conflict_updates_links_but_keeps_note_content(self):
        update = self.compiled().split("DO UPDATE SET", 1)[1]
        assert "outbound_links = excluded.outbound_links" in update
        assert "content" not in update

    def test_new_nodes_go_through_the_upsert(self):
        session = FakeSession([])
        GraphPersistenceService(session).save_graph(str(PROJECT_ID), graph(("stroma", [])))
        assert "ON CONFLICT" in str(session.statements[0].compile(dialect=postgresql.dialect()))

    def test_no_statement_when_nothing_is_new(self):
        session = FakeSession([db_node("stroma", content="note")])
        GraphPersistenceService(session).save_graph(str(PROJECT_ID), graph(("stroma", [])))
        assert session.statements == []
