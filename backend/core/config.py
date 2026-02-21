from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # app config
    APP_NAME: str = "BrainLattice API"
    DEBUG: bool = False
    
    # database (neon postgres)
    DATABASE_URL: str
    
    # cloudflare r2 storage
    R2_BUCKET: Optional[str] = None
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_S3_API_URL: Optional[str] = None
    
    # ai api keys
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str
    OPENROUTER_API_KEY: str

    # upstash redis (job status tracking)
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None

    # qstash (async task queue)
    QSTASH_URL: str = "https://qstash.upstash.io"
    QSTASH_TOKEN: Optional[str] = None
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
