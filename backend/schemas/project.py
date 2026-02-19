from pydantic import BaseModel
from typing import Optional, Dict, Any

class ProjectSaveRequest(BaseModel):
    title: str

class ProjectSaveResponse(BaseModel):
    project_id: str
    success: bool
    error_message: Optional[str] = None

class ProjectGetResponse(BaseModel):
    project_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class UpdateTitleRequest(BaseModel):
    title: str
