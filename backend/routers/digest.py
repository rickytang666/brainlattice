from fastapi import APIRouter, HTTPException
from services.llm.digest_generator import generate_ai_digest
from models.graph import DigestRequest, DigestResponse

router = APIRouter()

@router.post("/digest", response_model=DigestResponse)
async def create_ai_digest(request: DigestRequest):
    """create ai-optimized concept outline"""
    try:
        data = await generate_ai_digest(request.text)
        return DigestResponse(digest_data=data, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"digest error: {str(e)}")
