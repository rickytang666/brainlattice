from fastapi import APIRouter, HTTPException
from services.db_service import save_project_data, get_project_data, list_projects, delete_project_data, update_project_title
from models.graph import ProjectSaveRequest, ProjectSaveResponse, ProjectGetResponse
from pydantic import BaseModel
import uuid

router = APIRouter()

class UpdateTitleRequest(BaseModel):
    title: str

@router.post("/project/save", response_model=ProjectSaveResponse)
async def save_project(request: ProjectSaveRequest):
    """save project (digest + graph) to firebase"""
    try:
        project_id = str(uuid.uuid4())
        success = save_project_data(
            project_id=project_id,
            reference_data=request.digest_data,
            graph_data=request.graph_data
        )
        if success:
            return ProjectSaveResponse(project_id=project_id, success=True)
        raise Exception("save failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"save error: {str(e)}")

@router.get("/projects/list")
async def list_all_projects():
    """list all projects"""
    try:
        return list_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"list error: {str(e)}")

@router.get("/project/{project_id}", response_model=ProjectGetResponse)
async def get_project(project_id: str):
    """get project data"""
    try:
        data = get_project_data(project_id)
        if data:
            return ProjectGetResponse(project_data=data, success=True)
        raise HTTPException(status_code=404, detail="not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get error: {str(e)}")

@router.patch("/project/{project_id}/title")
async def update_title(project_id: str, request: UpdateTitleRequest):
    """update project title"""
    try:
        if update_project_title(project_id, request.title):
            return {"success": True, "message": "updated"}
        raise HTTPException(status_code=404, detail="not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"update error: {str(e)}")

@router.delete("/project/{project_id}")
async def delete_project(project_id: str):
    """delete project"""
    try:
        if delete_project_data(project_id):
            return {"success": True, "message": "deleted"}
        raise HTTPException(status_code=404, detail="not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"delete error: {str(e)}")
