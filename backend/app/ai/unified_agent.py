from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
# from langchain_cerebras import ChatCerebras
from langchain_core.prompts import ChatPromptTemplate
from config import get_settings
from app.ai.unified_schemas import (
    UnifiedInput, UnifiedOutput, SessionMemory, SessionMessage,
    MessageType, MessageRole, UIAction, ResponseData, PopupData
)
import json
import uuid
from datetime import datetime

settings = get_settings()

# In-memory session store (in production, use Redis)
session_store: Dict[str, SessionMemory] = {}

# Initialize LLM
unified_llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name=settings.MODEL_NAME,
    temperature=0.4,
)

# llm = ChatCerebras(
#     api_key=settings.CEREBRAS_API_KEY,
#     model_name=settings.CEREBRAS_MODE_NAME,
#     temperature=settings.TEMPERATURE
# )

UNIFIED_SYSTEM_PROMPT = """You are a Unified Voice-First Contextual AI Copilot for an e-commerce platform.

You combine three capabilities:
1. Proactive context awareness
2. Interactive chat assistance
3. Voice-based interaction with form filling

CRITICAL: Always return valid JSON in this exact format:
{{
  "session_update": {{
    "session_id": "string",
    "mode": "voice" | "text",
    "history": [...],
    "pending_action": {{...}} | null,
    "current_page": "/path"
  }},
  "response": {{
    "message": "your response",
    "speak": true | false
  }},
  "ui_action": {{
    "type": "none" | "navigate" | "update_form" | "highlight_element" | "show_message",
    "target": "string or null",
    "data": {{}},
    "require_confirmation": true | false
  }},
  "popup": {{
    "show": false,
    "message": "",
    "type": "info"
  }},
  "confidence": 0.0-1.0
}}

VOICE MODE RULES:
- When mode="voice", set speak: true
- Keep responses conversational and concise
- No HTML in voice responses
- Ask for information step by step

LOGIN FLOW (voice mode):
Step 1: Ask "Please tell me your email address"
Step 2: After email → Ask "Now tell me your password"
Step 3: After password → Return update_form action with confirmation

Example:
User confirms help on login page →
You: "Please tell me your email address."
User: "sunder@12"
You: "Got it. Now tell me your password."
User: "sunder"
You: Return {{
  "ui_action": {{
    "type": "update_form",
    "target": "login_form",
    "data": {{"email": "sunder@12", "password": "sunder"}},
    "require_confirmation": true
  }}
}}

CORRECTION HANDLING:
User: "Not sunder, it's sundher"
You: Update pending_action with corrected value before submission

SECURITY:
- Never auto-submit forms
- Always require confirmation for sensitive actions
- Never log passwords
- Clear sensitive data after use

CONTEXT AWARENESS:
- Login page + idle > 8s → Offer help
- Product page + viewing > 20s → Suggest related items
- Cart page + items + idle > 10s → Suggest checkout

INTERRUPTION:
- If interrupt_previous=true, cancel ongoing response
- Process new input immediately

BACKGROUND MODE:
- Continue session even if UI closed
- Don't spam popups if already dismissed

Current session state: {session_state}
Current input: {input_data}

Return ONLY valid JSON. No markdown, no explanation."""

prompt = ChatPromptTemplate.from_messages([
    ("system", UNIFIED_SYSTEM_PROMPT)
])


def get_or_create_session(session_id: str, mode: MessageType) -> SessionMemory:
    """Get existing session or create new one"""
    if session_id not in session_store:
        session_store[session_id] = SessionMemory(
            session_id=session_id,
            mode=mode,
            history=[],
            pending_action=None,
            current_page="/"
        )
    return session_store[session_id]


def update_session_history(
    session: SessionMemory,
    role: MessageRole,
    message: str,
    msg_type: MessageType
):
    """Add message to session history"""
    session.history.append(SessionMessage(
        role=role,
        type=msg_type,
        content=message
    ))
    session.last_updated = datetime.now()


async def process_unified_input(input_data: UnifiedInput) -> UnifiedOutput:
    """
    Main unified agent processing
    Handles context awareness, chat, voice, and form filling
    """
    try:
        # Get or create session
        session = get_or_create_session(input_data.session_id, input_data.mode)
        
        # Update session page
        if input_data.route:
            session.current_page = input_data.route
        
        # Update mode
        session.mode = input_data.mode
        
        # Handle interruption
        if input_data.interrupt_previous:
            session.pending_action = None
        
        # Add user message if provided
        if input_data.message:
            update_session_history(
                session,
                MessageRole.user,
                input_data.message,
                input_data.mode
            )
        
        # Build context for LLM
        session_dict = session.model_dump()
        input_dict = input_data.model_dump()
        
        # Invoke LLM
        chain = prompt | unified_llm
        response = chain.invoke({
            "session_state": json.dumps(session_dict, default=str, indent=2),
            "input_data": json.dumps(input_dict, indent=2)
        })
        
        # Parse response
        response_text = response.content.strip()
        
        # Clean markdown if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        # Parse JSON
        response_data = json.loads(response_text)
        
        # Update session with assistant response
        if response_data.get("response", {}).get("message"):
            update_session_history(
                session,
                MessageRole.assistant,
                response_data["response"]["message"],
                session.mode
            )
        
        # Update pending action
        if response_data.get("ui_action", {}).get("type") != "none":
            session.pending_action = response_data.get("ui_action")
        
        # Save session
        session_store[session.session_id] = session
        
        # Add session to response
        response_data["session_update"] = session.model_dump()
        
        # Validate and return
        return UnifiedOutput(**response_data)
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response: {response_text}")
        return create_safe_default(input_data.session_id, input_data.mode)
    
    except Exception as e:
        print(f"Unified agent error: {e}")
        import traceback
        traceback.print_exc()
        return create_safe_default(input_data.session_id, input_data.mode)


def create_safe_default(session_id: str, mode: MessageType) -> UnifiedOutput:
    """Create safe default response"""
    session = get_or_create_session(session_id, mode)
    
    return UnifiedOutput(
        session_update=session,
        response=ResponseData(
            message="",
            speak=False
        ),
        ui_action=UIAction(
            type="none",
            target=None,
            data=None,
            require_confirmation=False
        ),
        popup=PopupData(
            show=False,
            message="",
            type="info"
        ),
        confidence=0.5
    )


def clear_session(session_id: str):
    """Clear session data"""
    if session_id in session_store:
        del session_store[session_id]


def get_session_history(session_id: str) -> list:
    """Get session conversation history"""
    session = session_store.get(session_id)
    if session:
        return [msg.model_dump() for msg in session.history]
    return []