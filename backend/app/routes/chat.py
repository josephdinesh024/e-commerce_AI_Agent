from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.ai.schemas import ChatRequest, ChatMessage, ChatRequestNew
from app.ai.graph.agent import run_agent, get_session_history, clear_session
from app.db import get_db
import json
from typing import AsyncGenerator, Optional

router = APIRouter(prefix="/chat", tags=["AI Assistant"])


async def generate_response(message: str, session_id: str, history: list, mode: str = "text", page_type: Optional[str] = None,route: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Generate streaming response from the agent
    
    Args:
        mode: "text" or "voice" - determines response format
    """
    try:
        full_response = ""
        
        # Collect the full response first
        async for chunk in run_agent(message, session_id, history, mode, page_type, route):  # Pass mode here
            if chunk["type"] == "done":
                full_response = chunk["content"]
                break
            elif chunk["type"] == "error":
                full_response = chunk["content"]
                break
        
        # Parse the JSON response
        try:
            response_data = json.loads(full_response)
        except:
            # Fallback if not valid JSON
            response_data = {
                "message": full_response,
                "action": {"type": "none", "target": None},
                "speak": mode == "voice"
            }
        
        # Stream the message word by word
        if response_data.get("message"):
            words = response_data["message"].split()
            chunk_size = 3
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i+chunk_size]
                chunk_text = " ".join(chunk_words)
                if i + chunk_size < len(words):
                    chunk_text += " "
                
                data = {
                    "type": "stream",
                    "content": chunk_text,
                    "done": False
                }
                yield f"data: {json.dumps(data)}\n\n"
        
        # Send final done signal with full structured response
        final_data = {
            "type": "done",
            "content": json.dumps(response_data),  # Send structured JSON
            "done": True
        }
        yield f"data: {json.dumps(final_data)}\n\n"
        
    except Exception as e:
        error_data = {
            "type": "error",
            "content": json.dumps({
                "message": "I apologize, but I encountered an error. Please try again.",
                "action": {"type": "none", "target": None},
                "speak": mode == "voice"
            }),
            "done": True
        }
        yield f"data: {json.dumps(error_data)}\n\n"


async def generate_response_text(message: str, session_id: str, history: list) -> AsyncGenerator[str, None]:
    """
    Generate streaming response from the agent
    """
    try:
        full_response = ""
        
        # Collect the full response first
        async for chunk in run_agent(message, session_id, history):
            if chunk["type"] == "done":
                full_response = chunk["content"]
                break
            elif chunk["type"] == "error":
                full_response = chunk["content"]
                break
        
        # Now stream it to the user word by word
        if full_response:
            words = full_response.split()
            chunk_size = 3  # Send 3 words at a time
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i+chunk_size]
                chunk_text = " ".join(chunk_words)
                if i + chunk_size < len(words):
                    chunk_text += " "
                
                data = {
                    "type": "stream",
                    "content": chunk_text,
                    "done": False
                }
                yield f"data: {json.dumps(data)}\n\n"
        
        # Send final done signal with full response
        final_data = {
            "type": "done",
            "content": full_response,
            "done": True
        }
        yield f"data: {json.dumps(final_data)}\n\n"
        
    except Exception as e:
        error_data = {
            "type": "error",
            "content": f"I apologize, but I encountered an error: {str(e)}. Please try again.",
            "done": True
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Stream chat responses from the AI assistant
    
    Accepts:
    - message: User's input message
    - session_id: User's session ID
    - conversation_history: Previous messages (optional)
    - mode: "text" or "voice" (optional, defaults to "text")
    
    Returns:
    - Server-Sent Events stream with AI responses including navigation actions
    """
    history = []
    if request.conversation_history:
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
    
    # Get mode from request (default to "text")
    mode = getattr(request, 'mode', 'text')
    
    return StreamingResponse(
        generate_response(request.message, request.session_id, history, mode, request.page_type, request.route),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/analyze")
async def chat(request: ChatRequestNew, db: Session = Depends(get_db)):
    """
    Stream chat responses from the AI assistant
    
    Accepts:
    - message: User's input message
    - session_id: User's session ID
    - mode: "text" or "voice" (optional, defaults to "text")
    
    Returns:
    - Server-Sent Events stream with AI responses including navigation actions
    """
    
    
    return await run_agent(request.message, request.session_id, [], request.mode, request.page_type, request.route)

@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    from app.agents.service import agent
    try:
        history = agent.get_session_history(session_id)
    except ValueError:
        history = []
    return {"session_id": session_id, "history": history}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clear session data"""
    clear_session(session_id)
    return {"message": "Session cleared", "session_id": session_id}

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


@router.post("/context")
async def receive_page_context(context_data: dict):
    """
    Receive page context from frontend
    
    Frontend sends this when agent requests it or when needed
    """
    from app.agents.page_context import store_page_context
    
    session_id = context_data.get("session_id")
    page_context = context_data.get("context")
    
    if not session_id or not page_context:
        return {"status": "error", "message": "Missing session_id or context"}
    
    # Store the context
    store_page_context(session_id, page_context)
    
    return {
        "status": "success",
        "message": "Page context received and stored",
        "session_id": session_id
    }

@router.get("/context/{session_id}")
async def get_page_context(session_id: str):
    """
    Get page context from frontend
    
    Frontend sends this when agent requests it or when needed
    """
    from app.agents.page_context import get_page_context_tool
    
    
    return {
        "status": "success",
        "context": get_page_context_tool(session_id),
        "session_id": session_id
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