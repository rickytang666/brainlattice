from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import project, ingest
from core.config import get_settings
from core.logger import setup_logger
from services.llm.providers import init_ai_services
import logging

# initialize custom ansi lowercase logging
setup_logger()
logger = logging.getLogger(__name__)

# initialize settings
settings = get_settings()

# initialize ai services
try:
    init_ai_services()
except Exception as e:
    logger.warning(f"ai services failed: {e}")

app = FastAPI(
    title="BrainLattice API",
    description="pdf to knowledge graph api",
    version="1.0.0"
)

# cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routers
app.include_router(project.router, prefix="/api", tags=["project"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])

@app.get("/")
async def root():
    return {"message": "api running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
