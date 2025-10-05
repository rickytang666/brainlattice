from fastapi import APIRouter, HTTPException
from services.ai_service import generate_concept_insights
from models.concept_insights import ConceptInsightsRequest, ConceptInsightsResponse

router = APIRouter()

@router.post("/concept-insights", response_model=ConceptInsightsResponse)
async def get_concept_insights(request: ConceptInsightsRequest):
    """
    Use Gemini 2.0 Flash Lite to generate concise insights about a concept
    """
    try:
        insights = await generate_concept_insights(
            concept_name=request.concept_name,
            context_data=request.context_data
        )
        
        return ConceptInsightsResponse(
            concept_name=insights["concept_name"],
            overview=insights["overview"],
            related_concepts=insights["related_concepts"],
            important_formulas=insights["important_formulas"],
            key_theorems=insights["key_theorems"],
            success=insights["success"],
            error=insights.get("error")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating concept insights: {str(e)}")
