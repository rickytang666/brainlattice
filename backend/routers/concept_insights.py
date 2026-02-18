from fastapi import APIRouter, HTTPException
from services.llm.insights import generate_concept_insights
from models.concept_insights import ConceptInsightsRequest, ConceptInsightsResponse

router = APIRouter()

@router.post("/concept-insights", response_model=ConceptInsightsResponse)
async def get_concept_insights(request: ConceptInsightsRequest):
    """get insights for a concept"""
    try:
        insights = await generate_concept_insights(request.concept_name, request.context_data)
        return ConceptInsightsResponse(insights=insights, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"insights error: {str(e)}")
