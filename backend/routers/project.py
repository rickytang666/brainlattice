from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from db.session import get_db
from db import models
from schemas.project import ProjectSaveRequest, ProjectSaveResponse, ProjectGetResponse, UpdateTitleRequest, ProjectTransferRequest, ProjectTransferResponse
from fastapi import Header
import uuid

router = APIRouter()


@router.post("/project/save", response_model=ProjectSaveResponse)
async def save_project(
    request: ProjectSaveRequest,
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """save project metadata to postgres"""
    try:
        project = models.Project(
            title=request.title,
            status="complete",
            user_id=x_user_id if x_user_id else None
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return ProjectSaveResponse(project_id=str(project.id), success=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"save error: {str(e)}")

@router.get("/projects/list")
async def list_all_projects(
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """list all projects from postgres filtered by user_id"""
    try:
        projects = db.query(models.Project).filter(models.Project.user_id == x_user_id).all()
        return [
            {"id": str(p.id), "title": p.title, "status": p.status, "created_at": p.created_at} 
            for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"list error: {str(e)}")

@router.get("/project/{project_id}", response_model=ProjectGetResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """get project data"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
        ).first()
        if project:
            # format response
            return ProjectGetResponse(
                project_data={
                    "id": str(project.id),
                    "title": project.title,
                    "status": project.status,
                    "created_at": project.created_at
                },
                success=True
            )
        raise HTTPException(status_code=404, detail="not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get error: {str(e)}")

@router.patch("/project/{project_id}/title")
async def update_title(
    project_id: str,
    request: UpdateTitleRequest,
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """update project title"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
        ).first()
        if project:
            project.title = request.title
            db.commit()
            return {"success": True, "message": "updated"}
        raise HTTPException(status_code=404, detail="not found")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"update error: {str(e)}")

@router.delete("/project/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """delete project"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
        ).first()
        if project:
            db.delete(project)
            db.commit()
            return {"success": True, "message": "deleted"}
        raise HTTPException(status_code=404, detail="not found")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"delete error: {str(e)}")

@router.get("/project/{project_id}/graph")
async def get_project_graph(
    project_id: str,
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """get project graph data"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="project not found or unauthorized")

        nodes = db.query(models.GraphNode).filter(models.GraphNode.project_id == project_id).all()
        
        formatted_nodes = []
        for n in nodes:
            formatted_nodes.append({
                "id": str(n.concept_id),
                "aliases": n.aliases or [],
                "outbound_links": n.outbound_links or [],
                "inbound_links": n.inbound_links or [],
                "content": n.content,
                "metadata": n.node_metadata or {}
            })
            
        return {"nodes": formatted_nodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"graph get error: {str(e)}")

@router.get("/project/{project_id}/node/{concept_id}/note")
async def get_node_note(
    project_id: str,
    concept_id: str,
    regenerate: bool = Query(False, description="force regenerate note, ignore cache"),
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_gemini_key: str = Header(None, alias="X-Gemini-API-Key"),
    x_openai_key: str = Header(None, alias="X-OpenAI-API-Key")
):
    """get or generate note for a specific node"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="project not found or unauthorized")

        node = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == project_id,
            models.GraphNode.concept_id == concept_id
        ).first()
        
        if not node:
            raise HTTPException(status_code=404, detail="node not found")
            
        if node.content and not regenerate:
            return {
                "concept_id": concept_id, 
                "content": node.content, 
                "outbound_links": node.outbound_links or [],
                "cached": True
            }
            
        # generate note (either first time or regenerate)
        from services.llm.note_service import NodeNoteService
        note_service = NodeNoteService(gemini_key=x_gemini_key, openai_key=x_openai_key)
        
        note_content = await note_service.generate_note(
            db, 
            project_id, 
            concept_id, 
            outbound_links=node.outbound_links
        )
        
        # persist the generated note
        node.content = note_content
        db.commit()
        
        return {
            "concept_id": concept_id, 
            "content": note_content, 
            "outbound_links": node.outbound_links or [],
            "cached": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"note generation error: {str(e)}")

@router.post("/project/transfer", response_model=ProjectTransferResponse)
async def transfer_projects(
    request: ProjectTransferRequest,
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """transfer projects from one user to another (used during auth migration)"""
    try:
        # require the request sender to be the target owner
        if x_user_id != request.target_id:
            raise HTTPException(status_code=403, detail="unauthorized transfer")
            
        projects = db.query(models.Project).filter(models.Project.user_id == request.source_id).all()
        count = len(projects)
        
        for project in projects:
            project.user_id = request.target_id
            
        db.commit()
        return ProjectTransferResponse(transferred_count=count, success=True)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"transfer error: {str(e)}")

@router.post("/project/{project_id}/export/obsidian")
async def trigger_obsidian_export(
    project_id: str,
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_gemini_key: str = Header(..., alias="X-Gemini-API-Key"),
    x_openai_key: str = Header(None, alias="X-OpenAI-API-Key")
):
    """trigger the asynchronous obsidian vault export process"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
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
        from services.ingestion_orchestrator import IngestionOrchestrator
        orchestrator = IngestionOrchestrator()
        await orchestrator.trigger_export(
            project_id=project_id,
            user_id=x_user_id,
            gemini_key=x_gemini_key,
            openai_key=x_openai_key
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
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """get current status of obsidian export"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
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
    x_user_id: str = Header(..., alias="X-User-Id")
):
    """get signed download URL for the obsidian vault zip"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.user_id == x_user_id
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
