from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import extract, digest, relationships, overview, audio_script, audio, project, concept_insights
from core.config import get_settings
from services.llm.providers import init_ai_services

# init settings
settings = get_settings()

# init ai services
try:
    init_ai_services()
except Exception as e:
    print(f"warning: ai services failed: {e}")

app = FastAPI(
    title="BrainLattice API",
    description="pdf to knowledge graph api",
    version="1.0.0"
)

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(extract.router, prefix="/api", tags=["extract"])
app.include_router(digest.router, prefix="/api", tags=["digest"])
app.include_router(relationships.router, prefix="/api", tags=["relationships"])
app.include_router(overview.router, prefix="/api", tags=["overview"])
app.include_router(audio_script.router, prefix="/api", tags=["audio-script"])
app.include_router(audio.router, prefix="/api", tags=["audio"])
app.include_router(project.router, prefix="/api", tags=["project"])
app.include_router(concept_insights.router, prefix="/api", tags=["concept-insights"])

@app.get("/")
async def root():
    return {"message": "api running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
