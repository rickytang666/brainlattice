from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from db.session import get_db
from db import models
from schemas.project import ProjectSaveRequest, ProjectSaveResponse, ProjectGetResponse, UpdateTitleRequest
import uuid

router = APIRouter()


@router.post("/project/save", response_model=ProjectSaveResponse)
async def save_project(request: ProjectSaveRequest, db: Session = Depends(get_db)):
    """save project metadata to postgres"""
    try:
        project = models.Project(
            title=request.title,
            status="complete"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return ProjectSaveResponse(project_id=str(project.id), success=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"save error: {str(e)}")

@router.get("/projects/list")
async def list_all_projects(db: Session = Depends(get_db)):
    """list all projects from postgres"""
    try:
        projects = db.query(models.Project).all()
        return [
            {"id": str(p.id), "title": p.title, "status": p.status, "created_at": p.created_at} 
            for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"list error: {str(e)}")

@router.get("/project/{project_id}", response_model=ProjectGetResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """get project data"""
    try:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
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
async def update_title(project_id: str, request: UpdateTitleRequest, db: Session = Depends(get_db)):
    """update project title"""
    try:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
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
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """delete project"""
    try:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
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
async def get_project_graph(project_id: str, db: Session = Depends(get_db)):
    """get project graph data"""
    try:
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
):
    """get or generate note for a specific node"""
    try:
        node = db.query(models.GraphNode).filter(
            models.GraphNode.project_id == project_id,
            models.GraphNode.concept_id == concept_id
        ).first()
        
        if not node:
            raise HTTPException(status_code=404, detail="node not found")
            
        if node.content and not regenerate:
            return {"concept_id": concept_id, "content": node.content, "cached": True}
            
        # generate note (either first time or regenerate)
        from services.llm.note_service import NodeNoteService
        note_service = NodeNoteService()
        
        note_content = await note_service.generate_note(
            db, 
            project_id, 
            concept_id, 
            outbound_links=node.outbound_links
        )
        
        # persist the generated note
        node.content = note_content
        db.commit()
        
        return {"concept_id": concept_id, "content": note_content, "cached": False}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"note generation error: {str(e)}")
