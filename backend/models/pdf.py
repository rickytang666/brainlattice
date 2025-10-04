from pydantic import BaseModel
from typing import Optional

class PDFExtractionResponse(BaseModel):
    filename: str
    text: str
    success: bool
    error_message: Optional[str] = None
