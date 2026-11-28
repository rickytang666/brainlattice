-- vectors from different embedding providers can't be compared, so record which one wrote each chunk
-- existing rows stay null: the provider that wrote them wasn't recorded
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding_provider VARCHAR;
