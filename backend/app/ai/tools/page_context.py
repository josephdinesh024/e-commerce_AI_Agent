from langchain.tools import tool
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json

# Global storage for page context (in production, use Redis or session store)
_page_context_store: Dict[str, Dict[str, Any]] = {}

@tool
def request_page_context_tool(
    session_id: str,
    reason: str = "Need to understand page structure for user request"
) -> str:
    """
    Request the current page context from the frontend.
    
    This tool signals the frontend to send detailed page structure including:
    - Forms and their fields
    - Buttons and their actions
    - Links
    - Products
    - Cart information
    - User information
    
    Args:
        session_id: The user's session ID
        reason: Why page context is needed (helps with logging)
    
    Returns:
        A message indicating context is being requested
    """
    return json.dumps({
        "status": "context_requested",
        "session_id": session_id,
        "message": "Page context will be provided in next interaction",
        "instruction": "Frontend should call /chat/context endpoint with page context"
    })


@tool
def get_page_context_tool(session_id: str) -> str:
    """
    Get the stored page context for a session.
    
    Args:
        session_id: The user's session ID
    
    Returns:
        JSON string containing page context or message if not available
    """
    context = _page_context_store.get(session_id)
    
    if not context:
        return json.dumps({
            "status": "no_context",
            "message": "No page context available. Request it first using request_page_context_tool."
        })
    
    return json.dumps(context, indent=2)


def store_page_context(session_id: str, context: Dict[str, Any]):
    """
    Store page context for a session
    
    Args:
        session_id: The user's session ID
        context: The page context data
    """
    _page_context_store[session_id] = context


def clear_page_context(session_id: str):
    """
    Clear page context for a session
    
    Args:
        session_id: The user's session ID
    """
    if session_id in _page_context_store:
        del _page_context_store[session_id]


def has_page_context(session_id: str) -> bool:
    """
    Check if page context exists for a session
    
    Args:
        session_id: The user's session ID
    
    Returns:
        True if context exists, False otherwise
    """
    return session_id in _page_context_store