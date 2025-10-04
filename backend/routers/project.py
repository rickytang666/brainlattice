from fastapi import APIRouter, HTTPException
from services.db_service import save_project_data, get_project_data
from models.graph import ProjectSaveRequest, ProjectSaveResponse, ProjectGetResponse
import uuid

router = APIRouter()

@router.post("/project/save", response_model=ProjectSaveResponse)
async def save_project(request: ProjectSaveRequest):
    """
    Save project data (digest + graph) to Firebase
    """
    try:
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Save to Firebase
        success = save_project_data(
            project_id=project_id,
            reference_data=request.digest_data,
            graph_data=request.graph_data
        )
        
        if success:
            return ProjectSaveResponse(
                project_id=project_id,
                success=True
            )
        else:
            raise Exception("Failed to save to Firebase")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving project: {str(e)}")

@router.get("/project/{project_id}", response_model=ProjectGetResponse)
async def get_project(project_id: str):
    """
    Retrieve project data from Firebase
    """
    try:
        project_data = get_project_data(project_id)
        
        if project_data:
            return ProjectGetResponse(
                project_data=project_data,
                success=True
            )
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving project: {str(e)}")
