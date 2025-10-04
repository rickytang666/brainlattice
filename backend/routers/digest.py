from fastapi import APIRouter, HTTPException
from services.ai_service import generate_ai_digest
from models.graph import DigestRequest, DigestResponse

router = APIRouter()

@router.post("/digest", response_model=DigestResponse)
async def create_ai_digest(request: DigestRequest):
    """
    Use OpenRouter (Grok 4 Fast) to create concise AI-optimized concept outline
    """
    try:
        digest_data = await generate_ai_digest(request.text)
        
        return DigestResponse(
            digest_data=digest_data,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating AI digest: {str(e)}")
