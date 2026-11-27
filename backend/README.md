# brainlattice backend

fastapi-based extraction engine. ingests pdfs, extracts unified knowledge graphs via per-chunk OpenRouter extraction, and stores the topological structures.

## local development

**mandatory keys** (`backend/.env`):

- `DATABASE_URL`: required for persistence. The application heavily utilizes `pgvector` and `JSONB` for storing text embeddings and complex extraction logic. **SQLite is completely unsupported.**
  - **Local development:** Use a managed postgres database like [Neon](https://neon.tech) or a local Postgres instance. Create a database, configure `pgvector`, and set your connection string.
    - `DATABASE_URL=postgres://user:password@host/neondb?sslmode=require`

**note:** no AI API keys are required in the backend environment _for the web app_. the frontend web app strictly uses keys provided by the client in the request headers (BYOK). **however**, if you want to run the local test script (`test_local_pipeline.py`), you must provide `GEMINI_API_KEY` and `OPENROUTER_API_KEY` in `backend/.env` (and optionally `OPENAI_API_KEY` for embeddings).

other keys (R2, Cloud Tasks) are optional for local dev. without a queue configured, jobs run as in-process background tasks.

**run database migrations (if using postgres):**

```bash
# install the base schema and the critical pgvector hnsw indices
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/006_add_hnsw_index.sql
# job state and counters
psql $DATABASE_URL -f migrations/007_jobs_and_counters.sql
```

**run local server:**

```bash
uv sync
uv run uvicorn main:app --reload
```

**run tests:**

```bash
# plain `uv run pytest` can't import `core`
uv run python -m pytest tests/unit -v
```

**run local pipeline (e2e):**

```bash
# 1. start backend: uv run uvicorn main:app --reload
# 2. run:
uv run python scripts/test_local_pipeline.py --file path/to/doc.pdf
```

**scripts:**

| script                           | purpose                                  |
| -------------------------------- | ---------------------------------------- |
| `scripts/test_local_pipeline.py` | e2e: upload PDF → poll → save graph json |
| `scripts/parse_pdf.py`           | extract markdown from PDF (debug, no LLM) |
| `scripts/clear_gemini_caches.py` | delete lingering Gemini context caches   |

## production deployment

the backend runs as a container (`Dockerfile`) on cloud run, with cloud tasks as the job queue.

### 1. neon (postgres)

- create a project on [neon.tech](https://neon.tech)
- copy the pooled connection string
- add to `.env` as `DATABASE_URL`
- run every file in `migrations/` in order

### 2. cloudflare r2 (object storage)

- create an r2 bucket on your cloudflare dashboard
- generate an api token (with admin read/write)
- add to `.env`:
  - `R2_BUCKET` (bucket name)
  - `R2_ACCOUNT_ID`
  - `R2_ACCESS_KEY_ID`
  - `R2_SECRET_ACCESS_KEY`
  - `R2_S3_API_URL` (looks like `https://<account_id>.r2.cloudflarestorage.com`)

### 3. google cloud tasks (job queue)

- `GCP_PROJECT_ID`, `CLOUD_TASKS_QUEUE`, `CLOUD_TASKS_LOCATION`: the queue jobs are published to
- `CLOUD_TASKS_INVOKER_SA`: the service account the queue signs oidc tokens as. `/worker` rejects every other caller, and returns 503 if a queue is configured without it
- `WORKER_PUBLIC_URL`: the full url of the `/worker` route, also the token audience

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
