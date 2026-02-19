import os
import uuid
import logging
from typing import Dict, Any, Optional

from services.storage_service import S3StorageService
from services.job_service import JobService
from services.queue_service import QStashService
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class IngestionOrchestrator:
    """
    handles high-level api ingestion:
    upload to r2 -> create job in redis -> publish task to qstash
    """

    def __init__(self):
        self.storage = S3StorageService()
        self.jobs = JobService()
        self.queue = QStashService()

    async def init_ingestion(self, filename: str, content: bytes, project_id: Optional[str] = None) -> Dict[str, Any]:
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
            logger.info(f"Uploading {filename} to {s3_key}...")
            self.storage.upload_file(content, s3_key)
            
            # create job record
            job_id = str(uuid.uuid4())
            metadata = {
                "filename": filename, 
                "file_id": file_id, 
                "s3_key": s3_key,
                "project_id": project_id
            }
            
            self.jobs.create_job(
                job_id=job_id,
                job_type="ingest_pdf",
                metadata=metadata
            )
            
            # publish task to worker
            worker_url = os.getenv("WORKER_PUBLIC_URL")
            if not worker_url:
                logger.warning("WORKER_PUBLIC_URL not set. Skipping QStash publish.")
                msg_id = "local_only"
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
            logger.exception("Failed to initialize ingestion")
            raise e
