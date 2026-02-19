from pydantic_settings import BaseSettings, SettingsConfigDict
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

    # upstash redis (job status)
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str

    # qstash (async worker)
    QSTASH_URL: str = "https://qstash.upstash.io"
    QSTASH_TOKEN: str
    QSTASH_CURRENT_SIGNING_KEY: str = ""
    QSTASH_NEXT_SIGNING_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings():
    """get cached settings"""
    return Settings()
