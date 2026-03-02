-- add an HNSW index to the chunks table for faster vector search
CREATE INDEX IF NOT EXISTS idx_chunk_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
