import os
import uuid
import logging
from typing import Dict, Any, Optional

from services.storage_service import get_storage_service
from services.job_service import get_job_service
from services.queue_service import get_queue_service
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class IngestionOrchestrator:
    """
    handles high-level api ingestion:
    upload to r2 -> create job in redis -> publish task to qstash
    """

    def __init__(self):
        self.storage = get_storage_service()
        self.jobs = get_job_service()
        self.queue = get_queue_service()

    async def init_ingestion(
        self, 
        filename: str, 
        content: bytes, 
        project_id: Optional[str] = None, 
        background_tasks: Optional[Any] = None,
        user_id: Optional[str] = None,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        initializes ingestion process for a new file
        returns job details
        """
        try:
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
            metadata = {
                "filename": filename, 
                "file_id": file_id, 
                "s3_key": s3_key,
                "project_id": project_id,
                "user_id": user_id,
                "gemini_key": gemini_key,
                "openai_key": openai_key
            }
            
            self.jobs.create_job(
                job_id=job_id,
                job_type="ingest_pdf",
                metadata=metadata
            )
            
            # publish task to worker
            worker_url = os.getenv("WORKER_PUBLIC_URL")
            if not worker_url or not self.queue:
                if not worker_url:
                    logger.warning("WORKER_PUBLIC_URL not set. running locally via background task.")
                else:
                    logger.warning("QStash service not configured. running locally via background task.")
                    
                msg_id = "local_only"
                if background_tasks:
                    from services.ingestion_processor import IngestionProcessor
                    processor = IngestionProcessor(job_id=job_id, file_key=s3_key)
                    background_tasks.add_task(processor.process)
            else:
                msg_id = self.queue.publish_task(
                    destination_url=worker_url,
                    payload={"job_id": job_id, "file_key": s3_key, "action": "ingest"}
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
        openai_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        re-triggers ingestion for an existing job ID
        looks up details from Redis and re-publishes to QStash
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

            # update metadata with fresh user_id/gemini_key if provided
            if user_id:
                metadata["user_id"] = user_id
            if gemini_key:
                metadata["gemini_key"] = gemini_key
            if openai_key:
                metadata["openai_key"] = openai_key
                
            self.jobs.create_job(job_id=job_id, job_type="ingest_pdf", metadata=metadata)

            # update job status to reset it
            self.jobs.update_progress(job_id, "pending", 0)
            
            # re-publish to worker
            worker_url = os.getenv("WORKER_PUBLIC_URL")
            if not worker_url or not self.queue:
                if not worker_url:
                    logger.warning("WORKER_PUBLIC_URL not set. skipping qstash publish, running locally instead.")
                else:
                    logger.warning("QStash service not configured. running locally instead.")
                    
                msg_id = "local_only"
                if background_tasks:
                    from services.ingestion_processor import IngestionProcessor
                    processor = IngestionProcessor(job_id=job_id, file_key=s3_key)
                    background_tasks.add_task(processor.process)
            else:
                msg_id = self.queue.publish_task(
                    destination_url=worker_url,
                    payload={"job_id": job_id, "file_key": s3_key, "action": "ingest"}
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
