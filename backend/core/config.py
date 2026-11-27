from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # app config
    APP_NAME: str = "BrainLattice API"
    DEBUG: bool = False
    INTERNAL_SECRET_KEY: Optional[str] = None

    # clerk auth (jwt verification). set at least one of these in production;
    # without them the backend cannot verify identity.
    CLERK_JWKS_URL: Optional[str] = None
    CLERK_ISSUER: Optional[str] = None

    # comma-separated list of allowed browser origins. "*" only for local dev.
    CORS_ALLOW_ORIGINS: str = "*"
    
    # database (neon postgres)
    DATABASE_URL: str
    
    # cloudflare r2 storage
    R2_BUCKET: Optional[str] = None
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_S3_API_URL: Optional[str] = None

    # google cloud (async task queue)
    GCP_PROJECT_ID: Optional[str] = None
    CLOUD_TASKS_QUEUE: Optional[str] = None
    CLOUD_TASKS_LOCATION: str = "us-central1"
    # service account the queue mints oidc tokens as; the worker verifies it
    CLOUD_TASKS_INVOKER_SA: Optional[str] = None

    # full url of the /worker route: the queue's delivery target and the oidc audience
    WORKER_PUBLIC_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings():
    """get cached settings"""
    return Settings()
