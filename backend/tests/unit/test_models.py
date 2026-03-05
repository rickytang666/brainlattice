import pytest
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.models import Base, Project, File, Chunk, GraphNode

# basic model validation (no DB; pgvector/JSONB not exercised)
def test_project_model():
    p = Project(title="Test Project", status="processing")
    assert p.title == "Test Project"
    assert p.status == "processing"

def test_file_model():
    f = File(filename="test.pdf", s3_path="pdfs/test.pdf")
    assert f.filename == "test.pdf"
    assert f.s3_path == "pdfs/test.pdf"

def test_chunk_model():
    c = Chunk(content="chunk content")
    assert c.content == "chunk content"


def test_graph_node_model():
    n = GraphNode(
        project_id=uuid.uuid4(),
        concept_id="calculus",
        content="branch of mathematics",
        outbound_links=["limit", "derivative"],
    )
    assert n.concept_id == "calculus"
    assert n.content == "branch of mathematics"
    assert "limit" in n.outbound_links
