from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import extract, digest, relationships, overview, audio_script, audio, project
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize AI services
from services.ai_service import init_ai_services
init_ai_services()

app = FastAPI(
    title="BrainLattice API",
    description="AI-powered PDF to Knowledge Graph conversion",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(extract.router, prefix="/api", tags=["extract"])
app.include_router(digest.router, prefix="/api", tags=["digest"])
app.include_router(relationships.router, prefix="/api", tags=["relationships"])
app.include_router(overview.router, prefix="/api", tags=["overview"])
app.include_router(audio_script.router, prefix="/api", tags=["audio-script"])
app.include_router(audio.router, prefix="/api", tags=["audio"])
app.include_router(project.router, prefix="/api", tags=["project"])

@app.get("/")
async def root():
    return {"message": "BrainLattice API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
