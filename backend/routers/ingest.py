from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from core.errors import to_http_error
from core.auth import BYOK_FIELDS
from core.dependencies import get_user_context, UserContext
from services.job_service import get_job_service

from core.config import get_settings
from schemas.ingest import RequestUploadRequest, FinalizeUploadRequest

router = APIRouter()
settings = get_settings()

@router.post("/ingest/request-upload")
async def request_upload(
    request: RequestUploadRequest,
    context: UserContext = Depends(get_user_context)
):
    """Phase 1: Get presigned URL for direct upload to R2"""
    try:
        from services.task_orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator()
        result = await orchestrator.request_ingestion(
            request.filename,
            user_id=context.user_id
        )
        return result
    except Exception as e:
        raise to_http_error(e, "upload request")

@router.post("/ingest/finalize-upload")
async def finalize_upload(
    background_tasks: BackgroundTasks,
    request: FinalizeUploadRequest,
    context: UserContext = Depends(get_user_context)
):
    """Phase 2: Trigger processing after the file has been uploaded to R2"""
    from services.task_orchestrator import ProjectNotFound, TaskOrchestrator

    try:
        orchestrator = TaskOrchestrator()
        result = await orchestrator.finalize_ingestion(
            project_id=request.project_id,
            s3_key=request.s3_key,
            filename=request.filename,
            background_tasks=background_tasks,
            user_id=context.user_id,
            gemini_key=context.gemini_key,
            openai_key=context.openai_key,
            openrouter_key=context.openrouter_key
        )
        return result
    except ProjectNotFound:
        raise HTTPException(status_code=404, detail="project not found")
    except Exception as e:
        raise to_http_error(e, "finalize")

@router.post("/ingest/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    context: UserContext = Depends(get_user_context)
):
    """
    uploads file to r2, creates a job, and dispatches it to the worker
    """
    try:
        from services.task_orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator()
        
        content = await file.read()
        
        MAX_FILE_SIZE = 25 * 1024 * 1024
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail="file too large. please split pdfs over 25mb to prevent processing timeouts."
            )
            
        result = await orchestrator.init_ingestion(
            file.filename, 
            content, 
            background_tasks=background_tasks,
            user_id=context.user_id,
            gemini_key=context.gemini_key,
            openai_key=context.openai_key,
            openrouter_key=context.openrouter_key
        )
        
        return result
        
    except Exception as e:
        raise to_http_error(e, "ingest")

def _get_owned_job(job_id: str, user_id: str) -> dict:
    job = get_job_service().get_job(job_id)
    # 404 rather than 403 for a non-owner: don't confirm the job exists
    if not job or (job.get("metadata") or {}).get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="job not found")
    return job

@router.get("/ingest/status/{job_id}")
async def get_status(
    job_id: str,
    context: UserContext = Depends(get_user_context)
):
    """check job status. only the job's owner may read it."""
    job = _get_owned_job(job_id, context.user_id)
    metadata = job.get("metadata") or {}

    # strip keys left on jobs created before they stopped being stored
    safe_metadata = {k: v for k, v in metadata.items() if k not in BYOK_FIELDS}
    return {**job, "metadata": safe_metadata}

@router.post("/ingest/retry/{job_id}")
async def retry_ingest(
    job_id: str, 
    background_tasks: BackgroundTasks,
    context: UserContext = Depends(get_user_context)
):
    """manually retry a failed ingestion job using its ID"""
    # retry rewrites the job's user_id to the caller, so it must check ownership first
    _get_owned_job(job_id, context.user_id)
    try:
        from services.task_orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator()
        result = await orchestrator.retry_ingestion(
            job_id, 
            background_tasks=background_tasks,
            user_id=context.user_id,
            gemini_key=context.gemini_key,
            openai_key=context.openai_key,
            openrouter_key=context.openrouter_key
        )
        return result
    except ValueError as e:
        # missing job is 404; anything else (e.g. absent api keys) is a bad request
        status = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status, detail=str(e))
    except Exception as e:
        raise to_http_error(e, "retry")
