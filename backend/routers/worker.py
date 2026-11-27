"""worker endpoint invoked by cloud tasks."""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from core.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


class WorkerTask(BaseModel):
    action: str = "ingest"
    job_id: Optional[str] = None
    file_key: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    gemini_key: Optional[str] = None
    openai_key: Optional[str] = None
    openrouter_key: Optional[str] = None


# sync so fastapi runs it in a threadpool; google cert fetching is blocking http
def verify_task_caller(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> bool:
    """reject any caller that isn't our cloud tasks queue"""
    expected_sa = settings.CLOUD_TASKS_INVOKER_SA
    if not expected_sa:
        # fail closed: a configured queue with no invoker SA means an open worker
        if settings.CLOUD_TASKS_QUEUE:
            logger.error("CLOUD_TASKS_INVOKER_SA unset while a queue is configured")
            raise HTTPException(status_code=503, detail="worker auth misconfigured")
        logger.warning("worker auth disabled; no queue configured (local dev)")
        return True

    # google-auth skips the audience check when audience is None
    if not settings.WORKER_PUBLIC_URL:
        logger.error("WORKER_PUBLIC_URL unset; cannot verify token audience")
        raise HTTPException(status_code=503, detail="worker auth misconfigured")

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="unauthorized")

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            token, google_requests.Request(), audience=settings.WORKER_PUBLIC_URL
        )
    except Exception as e:
        logger.warning(f"rejected worker token: {e}")
        raise HTTPException(status_code=401, detail="unauthorized")

    if claims.get("email") != expected_sa or not claims.get("email_verified"):
        logger.warning(f"worker token has unexpected subject: {claims.get('email')}")
        raise HTTPException(status_code=401, detail="unauthorized")

    return True


@router.post("/worker")
async def run_task(
    task: WorkerTask,
    authorized: bool = Depends(verify_task_caller),
) -> Dict[str, Any]:
    # never log the task body: it carries byok api keys
    logger.info(f"worker job={task.job_id} action={task.action}")

    if task.action == "ingest":
        if not task.job_id or not task.file_key:
            raise HTTPException(status_code=400, detail="missing job_id or file_key")

        from services.ingestion_processor import IngestionProcessor

        processor = IngestionProcessor(
            job_id=task.job_id,
            file_key=task.file_key,
            gemini_key=task.gemini_key,
            openai_key=task.openai_key,
            openrouter_key=task.openrouter_key,
            user_id=task.user_id,
        )
        result = await processor.process()

    elif task.action == "prepare_export":
        if not task.project_id:
            raise HTTPException(status_code=400, detail="missing project_id")

        from services.export_processor import ExportProcessor

        processor = ExportProcessor(
            project_id=task.project_id,
            user_id=task.user_id,
            gemini_key=task.gemini_key,
            openai_key=task.openai_key,
            openrouter_key=task.openrouter_key,
        )
        result = await processor.process()

    else:
        raise HTTPException(status_code=400, detail=f"unknown action: {task.action}")

    return {"status": "completed", **(result or {})}
