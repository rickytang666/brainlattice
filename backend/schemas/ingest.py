from pydantic import BaseModel
from typing import Optional

class RequestUploadRequest(BaseModel):
    filename: str

class FinalizeUploadRequest(BaseModel):
    project_id: str
    s3_key: str
    filename: str
