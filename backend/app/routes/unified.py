from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.ai.unified_schemas import UnifiedInput, UnifiedOutput
from app.ai.unified_agent import (
    process_unified_input,
    get_session_history,
    clear_session
)
from app.db import get_db

router = APIRouter(prefix="/unified", tags=["Unified AI Copilot"])


@router.post("/process", response_model=UnifiedOutput)
async def process_copilot_input(
    input_data: UnifiedInput,
    db: Session = Depends(get_db)
):
    """
    Unified endpoint for all AI Copilot interactions
    
    Handles:
    - Context-aware suggestions
    - Interactive chat
    - Voice commands
    - Form filling
    - Navigation
    
    Maintains session memory across interactions
    """
    return await process_unified_input(input_data)


@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    history = get_session_history(session_id)
    return {"session_id": session_id, "history": history}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clear session data"""
    clear_session(session_id)
    return {"message": "Session cleared", "session_id": session_id}


@router.get("/health")
async def health_check():
    """Health check for unified copilot"""
    return {"status": "healthy", "agent": "unified_copilot"}