from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector
from db.session import Base
import uuid

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

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
        Index("chunks_embedding_idx", "embedding", postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64}),
    )

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
