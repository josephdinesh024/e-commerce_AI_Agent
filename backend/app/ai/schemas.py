from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum

# Chat Schemas
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
    route: str = "/"
    last_updated: datetime = Field(default_factory=datetime.now)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    conversation_history: Optional[List[ChatMessage]] = []
    mode: MessageType = MessageType.text
    
    # Page context
    page_type: Optional[str] = None
    route: Optional[str] = None

class ChatRequestNew(BaseModel):
    message: str
    session_id: str
    mode: MessageType = MessageType.text
    
    # Page context
    page_type: Optional[str] = None
    route: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_used: Optional[str] = None

# Tool Schemas
class SearchProductsInput(BaseModel):
    """Input for searching products"""
    keyword: Optional[str] = Field(None, description="Search keyword for product name or description")
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    color: Optional[str] = Field(None, description="Color filter")

class ProductDetailsInput(BaseModel):
    """Input for getting product details"""
    product_id: Optional[int] = Field(None, description="Product ID")
    product_name: Optional[str] = Field(None, description="Product name to search for")

class StockCheckInput(BaseModel):
    """Input for checking stock"""
    product_id: int = Field(..., description="Product ID to check stock for")

class CartSummaryInput(BaseModel):
    """Input for getting cart summary"""
    session_id: str = Field(..., description="User session ID")

class OrderStatusInput(BaseModel):
    """Input for checking order status"""
    order_id: int = Field(..., description="Order ID to check")

class FAQInput(BaseModel):
    """Input for FAQ queries"""
    question: str = Field(..., description="User's question about policies, shipping, returns, etc.")

# Agent State
class AgentState(BaseModel):
    messages: List[Dict[str, Any]] = []
    user_input: str = ""
    tool_calls: List[Dict[str, Any]] = []
    tool_responses: List[str] = []
    final_response: str = ""
    session_id: str = ""
    iteration: int = 0
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True