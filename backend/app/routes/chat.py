from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db import get_db
import json
from typing import AsyncGenerator, Optional

router = APIRouter(prefix="/chat", tags=["AI Assistant"])



@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    from app.agents.service import get_agent
    try:
        history = get_agent().get_session_history(session_id)
    except ValueError:
        history = []
    return {"session_id": session_id, "history": history}



@router.get("/suggestions")
async def get_suggestions():
    """
    Get suggested queries for users
    """
    return {
        "suggestions": [
            "Show me trending dresses",
            "Do you have red dresses under $100?",
            "What's in my cart?",
            "Tell me about your return policy",
            "Show me evening gowns",
            "Check my order status"
        ]
    }


from app.agents.service import AgentCoreService, AgentCoreServiceStream
# from app.agents.page_context import request_page_context_tool, get_page_context_tool, store_page_context, clear_page_context    
from pydantic import BaseModel, Field

class AgentCoreRequest(BaseModel):
    message:str
    session_id:Optional[str]='user_01'
    page_type: Optional[str] = None
    route: Optional[str] = None
    mode: str = Field(default="text", description="Mode of response: 'text' or 'voice'")

# @router.get('/agent-core')
# async def AgentCore():
#     await test_agent()

#     return {'message':'Test completed'}


@router.post('/agent')
async def AgentCoreMethodsSync(request:AgentCoreRequest):
    
    return await AgentCoreService(request.message, request.session_id, request.page_type, request.route, request.mode)

@router.post('/agent-stream')
def AgentCoreMethodsStream(request:AgentCoreRequest):
    
    return StreamingResponse(
        AgentCoreServiceStream(request.message, request.session_id, request.page_type, request.route, request.mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    ) 