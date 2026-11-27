-- move job state and the cli copy counter off redis into postgres
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR PRIMARY KEY,
    job_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    job_metadata JSONB DEFAULT '{}',
    result JSONB,
    extraction_cache JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- supports sweeping stale jobs
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs (updated_at);

CREATE TABLE IF NOT EXISTS counters (
    name VARCHAR PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);

-- carry over the cli copy count from redis; adjust the value before running
INSERT INTO counters (name, value) VALUES ('cli_copies', 0)
ON CONFLICT (name) DO NOTHING;
