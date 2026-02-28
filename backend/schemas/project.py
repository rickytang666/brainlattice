from pydantic import BaseModel
from typing import Optional, Dict, Any

class ProjectTransferRequest(BaseModel):
    source_id: str
    target_id: str

class ProjectTransferResponse(BaseModel):
    transferred_count: int
    success: bool
    error_message: Optional[str] = None

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
