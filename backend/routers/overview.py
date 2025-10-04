from fastapi import APIRouter, HTTPException
from services.ai_service import generate_overview
from models.graph import OverviewRequest, OverviewResponse

router = APIRouter()

@router.post("/overview", response_model=OverviewResponse)
async def generate_study_overview(request: OverviewRequest):
    """
    Use GPT-4o Mini to generate study guide overview from knowledge graph
    """
    try:
        overview = await generate_overview(request.graph_data)
        
        return OverviewResponse(
            overview_text=overview,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating overview: {str(e)}")
