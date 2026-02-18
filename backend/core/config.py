from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # app
    APP_NAME: str = "BrainLattice API"
    DEBUG: bool = False
    
    # database (neon)
    DATABASE_URL: str
    
    # cloudflare r2
    R2_BUCKET: str = "pdfs"
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_S3_API_URL: str
    
    # ai keys
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str
    OPENROUTER_API_KEY: str
    FISH_AUDIO_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings():
    """get cached settings"""
    return Settings()
