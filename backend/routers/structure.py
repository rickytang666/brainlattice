from fastapi import APIRouter, HTTPException
from services.ai_service import generate_structured_json
from models.graph import StructuredTextRequest, StructuredTextResponse

router = APIRouter()

@router.post("/structure", response_model=StructuredTextResponse)
async def structure_text(request: StructuredTextRequest):
    """
    Use Gemini 2.5 Flash Lite to convert raw text to structured JSON
    """
    try:
        structured_json = await generate_structured_json(request.text)
        
        return StructuredTextResponse(
            structured_data=structured_json,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error structuring text: {str(e)}")
