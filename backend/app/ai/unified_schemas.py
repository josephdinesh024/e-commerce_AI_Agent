from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
from enum import Enum

# Session Management
class MessageType(str, Enum):
    voice = "voice"
    text = "text"

class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"

class SessionMessage(BaseModel):
    role: MessageRole
    type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SessionMemory(BaseModel):
    session_id: str
    mode: MessageType
    history: List[SessionMessage] = []
    pending_action: Optional[Dict[str, Any]] = None
    current_page: str = "/"
    last_updated: datetime = Field(default_factory=datetime.now)

# Input Schemas
class UnifiedInput(BaseModel):
    """Unified input for all agent interactions"""
    session_id: str
    message: Optional[str] = None
    mode: MessageType
    
    # Page context
    page_type: Optional[str] = None
    route: Optional[str] = None
    user_idle_seconds: int = 0
    
    # Additional context
    form_state: Optional[Dict[str, Any]] = None
    product_context: Optional[Dict[str, Any]] = None
    cart_context: Optional[Dict[str, Any]] = None
    
    # Flags
    interrupt_previous: bool = False
    popup_confirmed: bool = False

# Output Schemas
class UIActionType(str, Enum):
    none = "none"
    navigate = "navigate"
    update_form = "update_form"
    highlight_element = "highlight_element"
    show_message = "show_message"
    focus_input = "focus_input"

class UIAction(BaseModel):
    type: UIActionType
    target: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    require_confirmation: bool = False

class ResponseData(BaseModel):
    message: str
    speak: bool

class PopupData(BaseModel):
    show: bool
    message: str = ""
    type: str = "info"

class UnifiedOutput(BaseModel):
    """Unified output for all agent interactions"""
    session_update: Optional[SessionMemory] = None
    response: ResponseData
    ui_action: UIAction
    popup: PopupData
    confidence: float = Field(ge=0.0, le=1.0)