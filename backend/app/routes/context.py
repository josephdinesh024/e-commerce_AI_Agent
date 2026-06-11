from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.ai.context_schemas import ContextInput, ContextResponse
from app.ai.context_agent import analyze_context, should_show_suggestion
from app.db import get_db

router = APIRouter(prefix="/context", tags=["Context Agent"])


@router.post("/analyze", response_model=ContextResponse)
async def analyze_page_context(
    context: ContextInput,
    db: Session = Depends(get_db)
):
    """
    Analyze page context and return contextual suggestion
    
    This is the Context-Aware AI Copilot that proactively suggests help
    based on user behavior and page state.
    
    Returns:
    - Structured JSON with popup configuration
    - Action suggestions (never auto-executed)
    - Confidence score
    """
    # Quick pre-check to avoid unnecessary LLM calls
    context_dict = context.model_dump()
    
    # if not should_show_suggestion(
    #     context.page_type.value,
    #     context.user_idle_seconds,
    #     context_dict
    # ):
    #     # Return no suggestion
    #     return ContextResponse(
    #         show_popup=False,
    #         popup_message="",
    #         popup_type="info",
    #         action={"type": "none", "target": None},
    #         require_confirmation=False,
    #         confidence=0.5
    #     )
    
    # Analyze with LLM
    response = analyze_context(context)
    
    # Additional safety check
    if response.confidence < 0.6:
        response.show_popup = False
    
    return response


@router.get("/health")
async def health_check():
    """Check if context agent is working"""
    return {"status": "healthy", "agent": "context"}