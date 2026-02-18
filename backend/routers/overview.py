from fastapi import APIRouter, HTTPException
from services.llm.overview_generator import generate_overview
from models.graph import OverviewRequest, OverviewResponse

router = APIRouter()

@router.post("/overview", response_model=OverviewResponse)
async def create_overview(request: OverviewRequest):
    """generate markdown study overview"""
    try:
        text = await generate_overview(request.digest_data, request.graph_data)
        return OverviewResponse(overview_text=text, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"overview error: {str(e)}")
