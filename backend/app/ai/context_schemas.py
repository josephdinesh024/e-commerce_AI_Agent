from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from enum import Enum

# Context Input Schemas
class PageType(str, Enum):
    home = "home"
    login = "login"
    product = "product"
    cart = "cart"
    checkout = "checkout"
    orders = "orders"

class FormState(BaseModel):
    email_filled: bool = False
    password_filled: bool = False

class ProductContext(BaseModel):
    product_id: Optional[int] = None
    time_spent: int = 0  # seconds

class CartContext(BaseModel):
    items_count: int = 0

class ContextInput(BaseModel):
    page_type: PageType
    route: str
    user_idle_seconds: int = 0
    session_id: Optional[str] = None
    form_state: Optional[FormState] = None
    product_context: Optional[ProductContext] = None
    cart_context: Optional[CartContext] = None

# Context Output Schemas
class PopupType(str, Enum):
    info = "info"
    assist = "assist"
    warning = "warning"

class ActionType(str, Enum):
    none = "none"
    navigate = "navigate"
    focus = "focus"
    click = "click"
    enter = "enter"

class Action(BaseModel):
    type: ActionType
    target: Optional[str] = None
    data: Optional[str] = None

class ContextResponse(BaseModel):
    show_popup: bool
    popup_message: str = ""
    popup_type: PopupType
    action: Optional[Action]= None
    require_confirmation: bool
    confidence: float = Field(ge=0.0, le=1.0)