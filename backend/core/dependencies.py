from fastapi import Header, HTTPException
from typing import Optional
from pydantic import BaseModel

class UserContext(BaseModel):
    user_id: str
    gemini_key: Optional[str] = None
    openai_key: Optional[str] = None

def get_user_context(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-API-Key")
) -> UserContext:
    """
    dependency to extract common user and API key headers.
    """
    return UserContext(
        user_id=x_user_id,
        gemini_key=x_gemini_key,
        openai_key=x_openai_key
    )
