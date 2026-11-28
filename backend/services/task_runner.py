"""runs one worker task payload; the /worker route and the in-process fallback share it."""
import logging
from typing import Any, Dict, Optional

from services.job_service import get_job_service

logger = logging.getLogger(__name__)


async def run_task(payload: Dict[str, Any], retry_pending: bool = False) -> Optional[Dict[str, Any]]:
    action = payload.get("action", "ingest")
    if action == "ingest":
        from services.ingestion_processor import IngestionProcessor

        processor = IngestionProcessor(
            job_id=payload.get("job_id"),
            file_key=payload.get("file_key"),
            gemini_key=payload.get("gemini_key"),
            openai_key=payload.get("openai_key"),
            openrouter_key=payload.get("openrouter_key"),
            user_id=payload.get("user_id"),
            retry_pending=retry_pending,
        )
        return await processor.process()

    if action == "prepare_export":
        from services.export_processor import ExportProcessor

        processor = ExportProcessor(
            project_id=payload.get("project_id"),
            user_id=payload.get("user_id"),
            gemini_key=payload.get("gemini_key"),
            openai_key=payload.get("openai_key"),
            openrouter_key=payload.get("openrouter_key"),
            retry_pending=retry_pending,
        )
        return await processor.process()

    raise ValueError(f"unknown action: {action}")


def record_failure(payload: Dict[str, Any], reason: str):
    """mark the job failed unless the processor already recorded a more specific error"""
    action = payload.get("action", "ingest")
    try:
        if action == "ingest":
            jobs = get_job_service()
            job = jobs.get_job(payload.get("job_id"))
            if job and job.get("status") != "failed":
                jobs.update_progress(payload.get("job_id"), "failed", details={"error": reason})
        else:
            from services.export_processor import mark_export_failed

            mark_export_failed(payload.get("project_id"), reason)
    except Exception:
        logger.exception(f"could not record failure for job={payload.get('job_id')} action={action}")
