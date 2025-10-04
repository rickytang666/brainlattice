from fastapi import APIRouter, HTTPException
from services.ai_service import generate_relationships
from models.graph import RelationshipRequest, RelationshipResponse

router = APIRouter()

@router.post("/relationships", response_model=RelationshipResponse)
async def extract_relationships(request: RelationshipRequest):
    """
    Use Gemini 2.5 Flash Lite to extract concept relationships from structured JSON
    """
    try:
        relationships = await generate_relationships(request.structured_data)
        
        return RelationshipResponse(
            graph_data=relationships,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting relationships: {str(e)}")
