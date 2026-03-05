# brainlattice backend

fastapi-based extraction engine. ingests pdfs, extracts unified knowledge graphs via per-chunk OpenRouter extraction, and stores the topological structures.

## local development

**mandatory keys** (`backend/.env`):

- `DATABASE_URL`: required for persistence. The application heavily utilizes `pgvector` and `JSONB` for storing text embeddings and complex extraction logic. **SQLite is completely unsupported.**
  - **Local Development / Serverless Postgres:** Use a managed postgres database like [Neon](https://neon.tech) or a local Postgres instance. Create a database, configure `pgvector`, and set your connection string.
    - `DATABASE_URL=postgres://user:password@host/neondb?sslmode=require`

**note:** no AI API keys are required in the backend environment _for the web app_. the frontend web app strictly uses keys provided by the client in the request headers (BYOK). **however**, if you want to run the local test script (`test_local_pipeline.py`), you must provide `GEMINI_API_KEY` and `OPENROUTER_API_KEY` in `backend/.env` (and optionally `OPENAI_API_KEY` for embeddings).

other keys (R2, Upstash) are optional for local dev.

**run database migrations (if using postgres):**

```bash
# install the base schema and the critical pgvector hnsw indices
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/006_add_hnsw_index.sql
```

**run local server:**

```bash
uv sync
uv run uvicorn main:app --reload
```

**run local pipeline tests:**

```bash
uv run python scripts/test_local_pipeline.py
```

## production deployment

taking the backend from 0 to 1 on aws lambda requires setting up the surrounding serverless infrastructure first.

### 1. neon (serverless postgres)

- create a project on [neon.tech](https://neon.tech)
- copy the pooled connection string
- add to `.env` as `DATABASE_URL`

### 2. cloudflare r2 (object storage)

- create an r2 bucket on your cloudflare dashboard
- generate an api token (with admin read/write)
- add to `.env`:
  - `R2_BUCKET` (bucket name)
  - `R2_ACCOUNT_ID`
  - `R2_ACCESS_KEY_ID`
  - `R2_SECRET_ACCESS_KEY`
  - `R2_S3_API_URL` (looks like `https://<account_id>.r2.cloudflarestorage.com`)

### 3. upstash (redis & qstash)

- **redis**: create a database. copy the `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.
- **qstash**: grab your `QSTASH_TOKEN`, `QSTASH_CURRENT_SIGNING_KEY`, and `QSTASH_NEXT_SIGNING_KEY` from the qstash dashboard.

### 4. aws & serverless framework

the backend deploys as a lambda container using `mangum`.

**pre-requisites:**

- `aws configure` set up locally with an iam user that has lambda/ecr permissions.
- serverless framework installed globally: `npm i -g serverless`
- docker daemon running locally.

**deploy steps:**

1. create an ecr repository in aws (or let serverless try to create it, but explicit is better).
2. authenticate your local docker daemon to aws ecr (replace `<region>` and `<aws_account_id>`):

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
```

3. deploy the stack (this automatically builds the docker image, pushes it to ecr, and wires up lambda/api gateway):

```bash
BUILDX_NO_DEFAULT_ATTESTATIONS=1 sls deploy
```

## internal pipeline tracking

1. **api (`ingest.py`)**: takes pdf -> dumps to storage -> enqueues async job.
2. **processing (`ingestion_processor.py`)**: chunks + embeds -> extracts seed from headers (OpenRouter) -> per-chunk extraction (OpenRouter) -> entity resolution -> concept validation filter -> connects orphan components -> orphan link completion -> persists to postgres.
3. **persistence (`persistence_service.py`)**: commits nodes/links to postgres.
4. **dead-letter sweeper (`internal.py`)**: manually sweep and kill stuck processing jobs by sending a POST request to `/api/internal/sweep-jobs` with header `x-internal-key: <INTERNAL_SECRET_KEY>`.

## codebase mapping

- `main.py`: fastapi root
- `core/config.py`: env var validation
- `services/llm/`: seed extraction, chunk extraction (OpenRouter), concept validation, orphan link completion, note generation (Gemini).
- `services/`: contains decoupled components (storage, job tracking, queueing) and the core processor logic.
