from fastapi import APIRouter, HTTPException
from services.llm.audio_generator import generate_audio_script
from models.graph import AudioScriptRequest, AudioScriptResponse

router = APIRouter()

@router.post("/audio-script", response_model=AudioScriptResponse)
async def create_audio_script(request: AudioScriptRequest):
    """generate audio script from digest"""
    try:
        script = await generate_audio_script(request.digest_data, request.graph_data)
        return AudioScriptResponse(script_text=script, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"script error: {str(e)}")
