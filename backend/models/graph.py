from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class Concept(BaseModel):
    name: str
    description: str
    level: int  # hierarchy level
    special_notes: Optional[str] = None

class Relationship(BaseModel):
    source: str
    target: str
    relationship_type: str  # "prerequisite", "related", "example", etc.

class StructuredTextRequest(BaseModel):
    text: str

class StructuredTextResponse(BaseModel):
    structured_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class DigestRequest(BaseModel):
    text: str

class DigestResponse(BaseModel):
    digest_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class RelationshipRequest(BaseModel):
    structured_data: Dict[str, Any]

class RelationshipResponse(BaseModel):
    graph_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class OverviewRequest(BaseModel):
    graph_data: Dict[str, Any]

class OverviewResponse(BaseModel):
    overview_text: str
    success: bool
    error_message: Optional[str] = None

class AudioScriptRequest(BaseModel):
    graph_data: Dict[str, Any]

class AudioScriptResponse(BaseModel):
    script_text: str
    success: bool
    error_message: Optional[str] = None

class AudioRequest(BaseModel):
    script_text: str

class AudioResponse(BaseModel):
    audio_url: str
    success: bool
    error_message: Optional[str] = None
