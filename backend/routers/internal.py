from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.config import get_settings
from db.session import SessionLocal
import logging

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

async def verify_internal_key(x_internal_key: str = Header(None)):
    """dependency to verify the internal secret key is present and correct"""
    if not settings.INTERNAL_SECRET_KEY:
        # if not configured, this route is disabled
        raise HTTPException(status_code=503, detail="internal routes disabled")
    if not x_internal_key or x_internal_key != settings.INTERNAL_SECRET_KEY:
        raise HTTPException(status_code=401, detail="unauthorized access")
    return True

@router.post("/sweep-jobs")
async def sweep_failed_jobs(authorized: bool = Depends(verify_internal_key)):
    """
    sweeps the database for stranded 'processing' jobs that have been stuck.
    flips their status to 'failed' to prevent infinite spinners on the frontend.
    """
    db = SessionLocal()
    try:
        # treat any project stuck for > 30 minutes as failed
        sql = text("""
            UPDATE projects 
            SET status = 'failed' 
            WHERE status = 'processing' 
            AND updated_at < NOW() - INTERVAL '30 minutes'
            RETURNING id;
        """)
        
        result = db.execute(sql)
        swept_ids = [row[0] for row in result.fetchall()]
        db.commit()
        
        if swept_ids:
            logger.warning(f"swept {len(swept_ids)} zombie jobs: {swept_ids}")
            
        return {"status": "success", "swept_count": len(swept_ids), "swept_ids": swept_ids}
        
    except Exception as e:
        db.rollback()
        logger.error(f"sweeper job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
