from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import project, ingest, export, internal, stats, worker
from core.auth import clerk_configured
from core.config import get_settings
from core.logger import setup_logger
import logging
import os

# initialize custom ansi lowercase logging
setup_logger()
logger = logging.getLogger(__name__)

# initialize settings
settings = get_settings()

# without clerk, any caller can claim any user id; cloud run always sets K_SERVICE
if os.getenv("K_SERVICE") and not clerk_configured():
    raise RuntimeError("CLERK_JWKS_URL or CLERK_ISSUER must be set when deployed")

app = FastAPI(
    title="BrainLattice API",
    description="pdf to knowledge graph api",
    version="1.0.0"
)

# cors middleware. defaults to "*" for local dev; set CORS_ALLOW_ORIGINS to the
# real frontend origins in production.
_origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
if _origins == ["*"]:
    logger.warning(
        "CORS_ALLOW_ORIGINS is '*'. set it to your frontend origins in production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routers
app.include_router(project.router, prefix="/api", tags=["project"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(internal.router, prefix="/api/internal", tags=["internal"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(worker.router, tags=["worker"])

@app.get("/")
async def root():
    return {"message": "api running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
