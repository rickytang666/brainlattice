# brainlattice-backend

pdf-to-graph extraction engine.

## setup

```bash
uv sync
cp .env.example .env  # fill keys
```

## dev

```bash
# api docs at /docs
uv run uvicorn main:app --reload
```

## test

```bash
uv run pytest
```

## build & run

```bash
docker build -t brainlattice-api .
docker run -p 8000:8000 --env-file .env brainlattice-api
```

## deploy

install `serverless` first.

```bash
BUILDX_NO_DEFAULT_ATTESTATIONS=1 sls deploy
```

## infra

- **api**: fastapi + mangum
- **worker**: lambda (15m timeout, 2gb ram)
- **storage**: s3 (r2)
- **database**: postgres (neon)
- **async**: qstash + redis (upstash)
