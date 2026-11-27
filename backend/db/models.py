from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector
from db.session import Base
import uuid

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    project_metadata = Column(JSONB, server_default="{}")

class File(Base):
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    filename = Column(String, nullable=False)
    s3_path = Column(String)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # openai text-embedding-3-small (1536 dims)
    chunk_metadata = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "idx_chunk_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

class Job(Base):
    """async job state"""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    job_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    progress = Column(Integer, nullable=False, default=0)
    # never holds byok keys; see core.auth.BYOK_FIELDS
    job_metadata = Column(JSONB, server_default="{}")
    result = Column(JSONB, nullable=True)
    extraction_cache = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_jobs_updated_at", "updated_at"),
    )


class Counter(Base):
    """simple named counters (e.g. cli copy tracking)"""
    __tablename__ = "counters"

    name = Column(String, primary_key=True)
    value = Column(Integer, nullable=False, default=0)


class GraphNode(Base):
    __tablename__ = "graph_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    aliases = Column(ARRAY(String), server_default="{}")
    outbound_links = Column(ARRAY(String), server_default="{}")
    inbound_links = Column(ARRAY(String), server_default="{}")
    node_metadata = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # index for fast concept lookup within a project
    __table_args__ = (
        Index("idx_project_concept", "project_id", "concept_id"),
    )
