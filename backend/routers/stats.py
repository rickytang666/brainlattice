from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import logging
from core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

def get_redis_client():
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
        from upstash_redis import Redis
        return Redis(url=settings.UPSTASH_REDIS_REST_URL, token=settings.UPSTASH_REDIS_REST_TOKEN)
    return None

class DownloadStats(BaseModel):
    npm_downloads: int
    cli_copies: int
    total: int

@router.get("/downloads", response_model=DownloadStats)
async def get_download_stats():
    npm_count = 0
    try:
        # fetch from npm api
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.npmjs.org/downloads/point/last-year/brainlattice", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                npm_count = data.get("downloads", 0)
    except Exception as e:
        logger.error(f"failed to fetch npm stats: {e}")

    copies_count = 0
    redis = get_redis_client()
    if redis:
        try:
            val = redis.get("brainlattice:stats:copies")
            copies_count = int(val) if val else 0
        except Exception as e:
            logger.error(f"failed to fetch copies count from redis: {e}")

    return DownloadStats(
        npm_downloads=npm_count,
        cli_copies=copies_count,
        total=npm_count + copies_count
    )

@router.post("/copy")
async def track_cli_copy():
    redis = get_redis_client()
    if redis:
        try:
            # increment the copy counter
            redis.incr("brainlattice:stats:copies")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"failed to increment copies count in redis: {e}")
            return {"status": "error", "message": "redis error"}
    return {"status": "error", "message": "redis not configured"}
