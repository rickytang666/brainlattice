from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from db.session import get_db
from db import models
from core.dependencies import get_user_context, UserContext

router = APIRouter()

@router.post("/project/{project_id}/export/obsidian")
async def trigger_obsidian_export(
    project_id: str,
    db: Session = Depends(get_db),
    context: UserContext = Depends(get_user_context)
):
    """trigger the asynchronous obsidian vault export process"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == context.user_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="project not found")

        # update metadata status
        metadata = project.project_metadata or {}
        metadata["export"] = {
            "status": "pending",
            "progress": 0,
            "message": "export requested..."
        }
        project.project_metadata = metadata
        flag_modified(project, "project_metadata")
        db.commit()

        # trigger background worker
        from services.task_orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator()
        await orchestrator.trigger_export(
            project_id=project_id,
            user_id=context.user_id,
            gemini_key=context.gemini_key,
            openai_key=context.openai_key
        )

        return {"success": True, "message": "export triggered"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"export trigger error: {str(e)}")

@router.get("/project/{project_id}/export/status")
async def get_export_status(
    project_id: str,
    db: Session = Depends(get_db),
    context: UserContext = Depends(get_user_context)
):
    """get current status of obsidian export"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == context.user_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="project not found")

        metadata = project.project_metadata or {}
        return metadata.get("export", {"status": "none"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"status error: {str(e)}")

@router.get("/project/{project_id}/export/download")
async def download_obsidian_export(
    project_id: str,
    db: Session = Depends(get_db),
    context: UserContext = Depends(get_user_context)
):
    """get signed download URL for the obsidian vault zip"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == context.user_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="project not found")

        metadata = project.project_metadata or {}
        export_meta = metadata.get("export", {})
        
        if export_meta.get("status") != "complete":
            raise HTTPException(status_code=400, detail="export not ready")

        file_key = export_meta.get("download_url")
        if not file_key:
            raise HTTPException(status_code=404, detail="export file not found")

        from services.storage_service import get_storage_service
        storage = get_storage_service()
        download_url = storage.get_download_url(file_key)

        return {"download_url": download_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"download error: {str(e)}")
