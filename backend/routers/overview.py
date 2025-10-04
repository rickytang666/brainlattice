from fastapi import APIRouter, HTTPException
from services.ai_service import generate_overview
from models.graph import OverviewRequest, OverviewResponse

router = APIRouter()

@router.post("/overview", response_model=OverviewResponse)
async def generate_study_overview(request: OverviewRequest):
    """
    Use OpenRouter (Grok 4 Fast) to generate study guide overview from AI digest data
    """
    try:
        # Use digest_data (primary) or fallback to graph_data for backward compatibility
        data_to_use = request.digest_data if request.digest_data else request.graph_data
        overview = await generate_overview(data_to_use, request.graph_data)
        
        return OverviewResponse(
            overview_text=overview,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating overview: {str(e)}")
