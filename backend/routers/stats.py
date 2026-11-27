from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import logging
from sqlalchemy import text
from db.session import SessionLocal

router = APIRouter()
logger = logging.getLogger(__name__)

COPIES_COUNTER = "cli_copies"

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
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT value FROM counters WHERE name = :name"),
            {"name": COPIES_COUNTER},
        ).first()
        copies_count = row[0] if row else 0
    except Exception as e:
        logger.error(f"failed to fetch copies count: {e}")
    finally:
        db.close()

    return DownloadStats(
        npm_downloads=npm_count,
        cli_copies=copies_count,
        total=npm_count + copies_count
    )

@router.post("/copy")
async def track_cli_copy():
    db = SessionLocal()
    try:
        db.execute(
            text(
                "INSERT INTO counters (name, value) VALUES (:name, 1) "
                "ON CONFLICT (name) DO UPDATE SET value = counters.value + 1"
            ),
            {"name": COPIES_COUNTER},
        )
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        logger.error(f"failed to increment copies count: {e}")
        return {"status": "error", "message": "counter unavailable"}
    finally:
        db.close()
