from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import project, ingest, export
from core.config import get_settings
from core.logger import setup_logger
import logging

# initialize custom ansi lowercase logging
setup_logger()
logger = logging.getLogger(__name__)

# initialize settings
settings = get_settings()

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
app.include_router(export.router, prefix="/api", tags=["export"])

@app.get("/")
async def root():
    return {"message": "api running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
