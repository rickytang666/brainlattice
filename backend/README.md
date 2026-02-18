# brainlattice-backend

api server.

## setup

```bash
# install dependencies
uv sync

# run server
uv run uvicorn main:app
```

## env

copy `.env.example` to `.env`.

fill out all the required api keys

requires `secrets/firebase_private.json`.
