from fastapi import APIRouter, HTTPException
from services.llm.graph_generator import generate_relationships
from models.graph import RelationshipRequest, RelationshipResponse

router = APIRouter()

@router.post("/relationships", response_model=RelationshipResponse)
async def extract_relationships(request: RelationshipRequest):
    """transform digest into hierarchical graph"""
    try:
        data = await generate_relationships(request.structured_data)
        return RelationshipResponse(graph_data=data, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"graph error: {str(e)}")
