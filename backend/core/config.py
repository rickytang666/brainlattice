from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # app
    APP_NAME: str = "BrainLattice API"
    DEBUG: bool = False
    
    # keys
    GEMINI_API_KEY: str
    OPENROUTER_API_KEY: str
    FISH_AUDIO_API_KEY: str
    
    # firebase
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "secrets/firebase_private.json"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings():
    """get cached settings"""
    return Settings()
