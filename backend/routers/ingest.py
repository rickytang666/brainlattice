from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from services.storage_service import S3StorageService
from services.job_service import JobService
from services.queue_service import QStashService
from core.config import get_settings
import uuid
import os

router = APIRouter()
settings = get_settings()

@router.post("/ingest/upload")
async def upload_file(
    file: UploadFile = File(...),
    # db: Session = Depends(get_db) # in future for project linkage
):
    """
    1. upload file to r2.
    2. create job in redis.
    3. trigger async worker via qstash.
    """
    try:
        storage = S3StorageService()
        jobs = JobService()
        queue = QStashService()
        
        # 1. upload to r2
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1]
        s3_key = f"uploads/{file_id}{ext}"
        
        content = await file.read()
        storage.upload_file(content, s3_key)
        
        # 2. create job
        job_id = str(uuid.uuid4())
        jobs.create_job(
            job_id=job_id,
            job_type="ingest_pdf",
            metadata={"filename": file.filename, "file_id": file_id, "s3_key": s3_key}
        )
        
        # 3. publish to qstash
        worker_url = os.getenv("WORKER_PUBLIC_URL", "https://placeholder-until-deployed")
        
        msg_id = queue.publish_task(
            destination_url=worker_url,
            payload={"job_id": job_id, "file_key": s3_key, "action": "ingest"}
        )
        
        return {
            "status": "queued",
            "job_id": job_id,
            "msg_id": msg_id,
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest failed: {str(e)}")

@router.get("/ingest/status/{job_id}")
async def get_status(job_id: str):
    """check job status"""
    jobs = JobService()
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job
