import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, Set

from services.storage_service import get_storage_service
from services.job_service import get_job_service
from services.queue_service import get_queue_service
from core.auth import BYOK_FIELDS
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class ProjectNotFound(Exception):
    """the project doesn't exist or belongs to another user"""


# strong refs: the event loop holds only weak refs to tasks, so an unreferenced one can be collected mid-run
_local_tasks: Set[asyncio.Task] = set()


def _ingest_payload(job_id, file_key, user_id, gemini_key, openai_key, openrouter_key) -> Dict[str, Any]:
    return {
        "job_id": job_id,
        "file_key": file_key,
        "action": "ingest",
        "gemini_key": gemini_key,
        "openai_key": openai_key,
        "openrouter_key": openrouter_key,
        "user_id": user_id,
    }


async def _run_local(payload: Dict[str, Any]):
    """the in-process stand-in for the /worker route; nothing retries, so every failure is final"""
    from core.errors import describe_error
    from services.task_runner import record_failure, run_task

    try:
        await run_task(payload)
    except Exception as e:
        logger.exception(f"in-process {payload.get('action')} task failed")
        record_failure(payload, describe_error(e))


class TaskOrchestrator:
    """
    handles high-level api ingestion and task dispatching:
    upload to r2 -> create job -> publish task to the queue
    """

    def __init__(self):
        self.storage = get_storage_service()
        self.jobs = get_job_service()
        self.queue = get_queue_service()

    def _dispatch(self, payload: Dict[str, Any], background_tasks: Optional[Any] = None) -> str:
        """publishes a worker task to the queue, or runs it in-process when no queue is configured"""
        worker_url = settings.WORKER_PUBLIC_URL
        if worker_url and self.queue:
            return self.queue.publish_task(destination_url=worker_url, payload=payload)

        logger.warning(f"no task queue configured, running {payload['action']} in-process")
        if background_tasks is not None:
            background_tasks.add_task(_run_local, payload)
        else:
            # a running step re-enqueuing itself has no request to attach a background task to
            task = asyncio.get_running_loop().create_task(_run_local(payload))
            _local_tasks.add(task)
            task.add_done_callback(_local_tasks.discard)
        return "local_only"

    async def request_ingestion(
        self, 
        filename: str, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phase 1: Pre-allocate project and S3 key.
        Returns presigned URL for PUT.
        """
        from db.session import SessionLocal
        from db import models
        db = SessionLocal()
        project_id = None
        try:
            new_proj = models.Project(
                title=filename, 
                status="processing",
                user_id=user_id
            )
            db.add(new_proj)
            db.flush()
            project_id = str(new_proj.id)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1]
        s3_key = f"uploads/{file_id}{ext}"
        
        upload_url = self.storage.get_upload_url(s3_key)
        
        return {
            "upload_url": upload_url,
            "s3_key": s3_key,
            "project_id": project_id,
            "filename": filename
        }

    async def finalize_ingestion(
        self,
        project_id: str,
        s3_key: str,
        filename: str,
        user_id: Optional[str] = None,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        background_tasks: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Phase 2: Once file is in R2, trigger the processing job.
        """
        job_id = str(uuid.uuid4())
        # byok keys never enter job state; they travel only in the queue payload
        metadata = {
            "filename": filename, 
            "s3_key": s3_key,
            "project_id": project_id,
            "user_id": user_id,
        }
        
        # update project metadata with job_id for frontend tracking
        from db.session import SessionLocal
        from db import models
        db = SessionLocal()
        try:
            project = db.query(models.Project).filter(models.Project.id == project_id).first()
            if not project or project.user_id != user_id:
                raise ProjectNotFound(project_id)
            meta = project.project_metadata or {}
            meta["job_id"] = job_id
            project.project_metadata = meta
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(project, "project_metadata")
            db.commit()
        finally:
            db.close()

        self.jobs.create_job(
            job_id=job_id,
            job_type="ingest_pdf",
            metadata=metadata
        )
        
        msg_id = self._dispatch(
            _ingest_payload(job_id, s3_key, user_id, gemini_key, openai_key, openrouter_key),
            background_tasks,
        )
        
        return {
            "status": "queued",
            "job_id": job_id,
            "msg_id": msg_id,
            "project_id": project_id
        }

    async def init_ingestion(
        self, 
        filename: str, 
        content: bytes, 
        project_id: Optional[str] = None, 
        background_tasks: Optional[Any] = None,
        user_id: Optional[str] = None,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        openrouter_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        initializes ingestion process for a new file
        returns job details
        """
        try:
            # create postgres project if not provided
            if not project_id:
                from db.session import SessionLocal
                from db import models
                db = SessionLocal()
                try:
                    new_proj = models.Project(
                        title=filename, 
                        status="processing",
                        user_id=user_id
                    )
                    db.add(new_proj)
                    db.flush()
                    project_id = str(new_proj.id)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()
            
            # prepare storage key
            file_id = str(uuid.uuid4())
            ext = os.path.splitext(filename)[1]
            s3_key = f"uploads/{file_id}{ext}"
            
            # upload to r2
            logger.info(f"uploading {filename} to {s3_key}...")
            self.storage.upload_file(content, s3_key)
            logger.success(f"upload complete: {s3_key}")
            
            # create job record
            job_id = str(uuid.uuid4())
            # byok keys never enter job state (see finalize_ingestion)
            metadata = {
                "filename": filename, 
                "file_id": file_id, 
                "s3_key": s3_key,
                "project_id": project_id,
                "user_id": user_id,
            }
            
            self.jobs.create_job(
                job_id=job_id,
                job_type="ingest_pdf",
                metadata=metadata
            )
            
            msg_id = self._dispatch(
                _ingest_payload(job_id, s3_key, user_id, gemini_key, openai_key, openrouter_key),
                background_tasks,
            )
            
            return {
                "status": "queued",
                "job_id": job_id,
                "msg_id": msg_id,
                "filename": filename
            }

        except Exception as e:
            logger.exception("failed to initialize ingestion")
            raise e

    async def retry_ingestion(
        self, 
        job_id: str, 
        background_tasks: Optional[Any] = None,
        user_id: Optional[str] = None,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        openrouter_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        re-triggers ingestion for an existing job ID
        looks up the stored job and re-publishes it to the worker
        """
        try:
            job = self.jobs.get_job(job_id)
            if not job:
                raise ValueError(f"job {job_id} not found")
            
            metadata = job.get("metadata", {})
            s3_key = metadata.get("s3_key")
            filename = metadata.get("filename", "unknown.pdf")
            
            if not s3_key:
                raise ValueError(f"missing s3_key in job {job_id} metadata")

            # keys are never persisted, so a retry must carry fresh ones.
            if not gemini_key or not openrouter_key:
                raise ValueError(
                    "api keys are required to retry a job. they are not stored server-side."
                )

            if user_id:
                metadata["user_id"] = user_id
            # scrub keys left by jobs created before they stopped being stored
            for field in BYOK_FIELDS:
                metadata.pop(field, None)

            self.jobs.create_job(job_id=job_id, job_type="ingest_pdf", metadata=metadata)

            # reset job status
            self.jobs.update_progress(job_id, "pending", 0)
            
            msg_id = self._dispatch(
                _ingest_payload(
                    job_id, s3_key, metadata.get("user_id"), gemini_key, openai_key, openrouter_key
                ),
                background_tasks,
            )
            
            return {
                "status": "re-queued",
                "job_id": job_id,
                "msg_id": msg_id,
                "filename": filename
            }

        except Exception as e:
            logger.exception(f"failed to retry ingestion for job {job_id}")
            raise e

    async def trigger_export(
        self, 
        project_id: str, 
        user_id: str,
        gemini_key: str,
        openai_key: str = None,
        openrouter_key: str = None,
        background_tasks: Optional[Any] = None
    ) -> str:
        """
        triggers the vault export process by publishing a prepare_export task
        """
        try:
            payload = {
                "action": "prepare_export",
                "project_id": project_id,
                "user_id": user_id,
                "gemini_key": gemini_key,
                "openai_key": openai_key,
                "openrouter_key": openrouter_key
            }
            msg_id = self._dispatch(payload, background_tasks)
            
            return msg_id
            
        except Exception as e:
            logger.exception(f"failed to trigger export for project {project_id}")
            raise e

