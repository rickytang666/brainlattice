from pydantic import BaseModel
from typing import List, Optional

class ConceptInsightsRequest(BaseModel):
    concept_name: str
    context_data: Optional[dict] = None

class ConceptInsightsResponse(BaseModel):
    concept_name: str
    overview: str
    related_concepts: List[str]
    important_formulas: List[str]
    key_theorems: List[str]
    success: bool
    error: Optional[str] = None
