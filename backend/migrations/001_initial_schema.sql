-- 001_initial_schema.sql
-- brainlattice schema for postgres 18 + neon auth

-- 1. enable extensions
create extension if not exists vector;

-- 2. projects table (with user context for auth)
create table if not exists projects (
    id uuid primary key default gen_random_uuid(),
    user_id uuid, -- links to neon_auth.users.id
    title text not null,
    status text not null default 'processing' check (status in ('processing', 'complete', 'failed')),
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- 3. files table
create table if not exists files (
    id uuid primary key default gen_random_uuid(),
    project_id uuid references projects(id) on delete cascade,
    filename text not null,
    s3_path text, 
    content text, 
    created_at timestamp with time zone default now()
);

-- 4. chunks table
create table if not exists chunks (
    id uuid primary key default gen_random_uuid(),
    file_id uuid references files(id) on delete cascade,
    content text not null,
    embedding vector(1536), -- sized for openai text-embedding-3-small
    chunk_metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default now()
);

-- 5. semantic & structural indexes
create index if not exists chunks_embedding_idx on chunks using hnsw (embedding vector_cosine_ops);
create index if not exists files_project_id_idx on files(project_id);
create index if not exists chunks_file_id_idx on chunks(file_id);
create index if not exists projects_user_id_idx on projects(user_id);
