from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db import models
from models.graph import ProjectSaveRequest, ProjectSaveResponse, ProjectGetResponse
from pydantic import BaseModel
import uuid

router = APIRouter()

class UpdateTitleRequest(BaseModel):
    title: str

@router.post("/project/save", response_model=ProjectSaveResponse)
async def save_project(request: ProjectSaveRequest, db: Session = Depends(get_db)):
    """save project metadata to postgres"""
    try:
        # for now, we just save the project record
        # in phase 2/3 we'll save files and chunks
        project = models.Project(
            title=request.graph_data.get('graph_metadata', {}).get('title', 'untitled project'),
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
    """get project data (currently minimal as we move storage to r2/neon)"""
    try:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            # return formatted data
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
