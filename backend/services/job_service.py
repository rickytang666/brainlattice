"""async job state, stored in postgres."""
import logging
from typing import Any, Dict, Optional

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm.attributes import flag_modified

from db.session import SessionLocal
from db import models

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = ("completed", "failed")

# neon's free tier is 0.5 GB and job rows carry graph previews, so old ones are pruned
JOB_RETENTION = timedelta(days=7)


def _serialize(job: models.Job) -> Dict[str, Any]:
    return {
        "id": job.id,
        "type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "metadata": job.job_metadata or {},
        "result": job.result,
    }


class PostgresJobService:
    """job state in the pipeline's own database, reusing its pooled connection"""

    def create_job(
        self, job_id: str, job_type: str, metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            job = db.get(models.Job, job_id)
            if job is None:
                job = models.Job(id=job_id, job_type=job_type)
                db.add(job)

            job.job_type = job_type
            job.status = "pending"
            job.progress = 0
            job.job_metadata = metadata or {}
            job.result = None

            cutoff = datetime.now(timezone.utc) - JOB_RETENTION
            db.execute(delete(models.Job).where(models.Job.updated_at < cutoff))
            db.commit()
            return _serialize(job)
        finally:
            db.close()

    def update_metadata(self, job_id: str, updates: Dict[str, Any]):
        db = SessionLocal()
        try:
            job = db.get(models.Job, job_id)
            if job is None:
                return
            merged = dict(job.job_metadata or {})
            merged.update(updates)
            job.job_metadata = merged
            flag_modified(job, "job_metadata")
            db.commit()
        finally:
            db.close()

    def update_progress(
        self,
        job_id: str,
        status: str,
        progress: int = None,
        details: Dict[str, Any] = None,
    ):
        db = SessionLocal()
        try:
            job = db.get(models.Job, job_id)
            if job is None:
                return
            job.status = status
            if progress is not None:
                job.progress = progress
            if details and status in TERMINAL_STATUSES:
                job.result = details
            # failed jobs keep the cache so a retry can skip extraction
            if status == "completed":
                job.extraction_cache = None
            db.commit()
        finally:
            db.close()

    def set_extraction_cache(self, job_id: str, data: Any):
        db = SessionLocal()
        try:
            job = db.get(models.Job, job_id)
            if job is None:
                return
            job.extraction_cache = data
            db.commit()
            logger.info(f"cached extraction results for job {job_id}")
        finally:
            db.close()

    def get_extraction_cache(self, job_id: str) -> Optional[Any]:
        db = SessionLocal()
        try:
            job = db.get(models.Job, job_id)
            if job is None or job.extraction_cache is None:
                return None
            logger.info(f"found cached extraction results for job {job_id}")
            return job.extraction_cache
        finally:
            db.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            job = db.get(models.Job, job_id)
            return _serialize(job) if job else None
        finally:
            db.close()


class LocalJobService:
    """in-memory job state for local dev without a database"""

    _jobs: Dict[str, Dict[str, Any]] = {}
    _caches: Dict[str, Any] = {}

    def create_job(
        self, job_id: str, job_type: str, metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        job = {
            "id": job_id,
            "type": job_type,
            "status": "pending",
            "progress": 0,
            "metadata": metadata or {},
            "result": None,
        }
        self._jobs[job_id] = job
        return job

    def update_metadata(self, job_id: str, updates: Dict[str, Any]):
        job = self._jobs.get(job_id)
        if job:
            job["metadata"].update(updates)

    def update_progress(
        self,
        job_id: str,
        status: str,
        progress: int = None,
        details: Dict[str, Any] = None,
    ):
        job = self._jobs.get(job_id)
        if not job:
            return
        job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if details and status in TERMINAL_STATUSES:
            job["result"] = details
        if status == "completed":
            self._caches.pop(job_id, None)

    def set_extraction_cache(self, job_id: str, data: Any):
        self._caches[job_id] = data

    def get_extraction_cache(self, job_id: str) -> Optional[Any]:
        return self._caches.get(job_id)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._jobs.get(job_id)
        return dict(job) if job else None


def get_job_service():
    from core.config import get_settings

    if get_settings().DATABASE_URL:
        return PostgresJobService()
    logger.info("no database url, falling back to in-memory job service")
    return LocalJobService()
