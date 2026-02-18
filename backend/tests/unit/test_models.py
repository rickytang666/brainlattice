import pytest
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.models import Base, Project, File, Chunk

# use sqlite in-memory for basic model validation 
# note: pgvector types won't work in sqlite, so we mock them or just skip vector column checks
# for now, we just check instantiation and non-vector fields
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
