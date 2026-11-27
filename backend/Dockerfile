FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# dependency layer first so source edits don't rebuild the whole install
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

COPY . /app/

# cloud run supplies PORT; one worker because the pipeline is already async
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
