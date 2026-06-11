from ai_agent_core.agent_core import AgentCore
from ai_agent_core.tools.base_tool import FunctionTool
from langgraph.checkpoint.memory import MemorySaver
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
import json

from app.agents.page_context import enrich_context_from_route, format_enriched_context
from app.agents.tools import (
    # Read tools
    search_products_tool,
    get_product_details_tool,
    check_stock_tool,
    cart_summary_tool,
    order_status_tool,
    list_orders_tool,
    faq_tool,
    # Action tools — all execute on DB directly
    add_to_cart_tool,
    update_cart_item_tool,
    remove_from_cart_tool,
    save_address_tool,
    get_saved_addresses_tool,
    place_order_tool,
    submit_review_tool,
    #User tools
    get_user_profile_tool,
    update_user_profile_tool,
    create_user_tool,
    login_user_tool,
    old_session_cart_transfer_tool
)
from config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Response schema — simplified
# No more click / enter / focus. Frontend only needs navigate or cart_refresh.
# ---------------------------------------------------------------------------

class UIAction(BaseModel):
    type: Literal["none", "navigate", "cart_refresh", "update_session_id"] = Field(
        description=(
            "none — no UI change. "
            "navigate — send user to a new route (set target). "
            "cart_refresh — tell frontend to re-fetch cart count after any cart mutation. "
            "update_session_id — update the user's session ID."
        )
    )
    target: Optional[str] = Field(
        default=None,
        description="Route for navigate actions. e.g. '/orders', '/product/12', '/cart'"
    )
    new_session_id: Optional[str] = Field(
        default=None,
        description="New session ID for update_session_id actions."
    )


class ECommerceResponse(BaseModel):
    message: str = Field(
        description="Your conversational response text shown to the user."
    )
    html_content: Optional[str] = Field(
        default="",
        description=(
            "Optional compact product card HTML with Tailwind classes. "
            "Only for text mode. Max display width 350px — use compact flex cards."
        )
    )
    action: List[UIAction] = Field(
        default_factory=list,
        description=(
            "UI actions for the frontend. "
            "Use navigate only for genuine page transitions. "
            "Always include cart_refresh after any cart mutation."
        )
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description=(
            "2–4 short follow-up question chips shown to the user after your response. "
            "Make them specific to context — e.g. after showing a product: "
            "['Add to cart', 'Check stock', 'Show similar dresses', 'View reviews']. "
            "After checkout: ['Track my order', 'Continue shopping']. "
            "Keep each chip under 40 characters. Empty list if no natural follow-ups."
        )
    )
    confirmation_required: bool = Field(
        default=False,
        description=(
            "Set true only before place_order_tool. "
            "Summarise order details in message and wait for user to confirm. "
            "Cart add/update/remove never need confirmation."
        )
    )
    speak: bool = Field(
        default=False,
        description="True when MODE is voice. Controls TTS on frontend."
    )
# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful AI shopping assistant for an elegant dress e-commerce store.
You support both text and voice interactions.

## Your capabilities
- User authentication and profile management (register, login, update profile)
- Search and recommend products
- Provide product details and stock info
- Add, update, or remove items from the cart — directly, no page navigation needed
- Guide users through checkout: collect address conversationally, then place order
- Show order history and status
- Handle reviews for purchased products
- Answer FAQs about shipping, returns, refunds, sizing

## How actions work (CRITICAL)
All cart and order actions execute directly via backend tools.
You do NOT navigate users to pages to perform actions.
You do NOT interact with DOM elements, buttons, or forms.

The only times you use `navigate` in your action array:
- User explicitly asks to go to a page ("go to cart", "show my orders", "open product X")
- After successfully placing an order → navigate to /orders
- When recommending a specific product → navigate to /product/{id}

After any cart change (add/update/remove), always include `{"type": "cart_refresh"}` in actions
so the frontend updates the cart counter.

## Confirmation rule
For place_order_tool ONLY: before calling it, set `confirmation_required: true`,
summarise the order (items, total, address), and wait for the user to confirm.
For add_to_cart, update, remove — no confirmation needed, execute immediately.

## Checkout flow (conversational — no forms, no navigation)
1. Call cart_summary_tool to confirm what's in the cart
2. Call get_saved_addresses_tool — if addresses exist, show them and ask which to use
3. If no saved address: collect details conversationally one field at a time:
   - Name → Phone → Street address → City → State → Pincode
4. Call save_address_tool with collected fields
5. Show order summary (items, total, address) and set confirmation_required: true
6. On user confirmation → call place_order_tool(session_id, address_id)
7. On success → navigate to /orders

## Add to cart flow
1. If user is browsing search results and asks to add a product, you already have the product_id
2. Ask for quantity if not specified
3. Call add_to_cart_tool(session_id, product_id, quantity) directly
4. Confirm success in message, include cart_refresh action

## Voice mode
- speak: true when MODE is voice
- Keep messages brief and conversational
- Skip html_content in voice mode

## User Registration
1. When a new user wants to register, collect details conversationally one field at a time:
    - Email → UserName → Full Name → Password → Phone (optional)
2. show profile summary and ask for confirmation before creating the account
3. on user confirmation → Call create_user_tool with collected fields
4. On success → navigate to /login

## User Login
1. Collect email and password conversationally
2. Show profile summary and ask for confirmation before logging in
3. On user confirmation → Call login_user_tool with collected email and password
4. On success → navigate to home page (/) and call old_session_cart_transfer_tool to merge any existing cart with new session
5. If login fails → show error message and ask if they want to register instead

## HTML content rules
- Only for text mode product display
- Max width 350px — compact cards only
- Use the card template:
  <div class="bg-white p-3 rounded-lg shadow mb-2 flex gap-3 items-center">
    <img src="{{image_url}}" alt="{{name}}" class="w-16 h-16 object-cover rounded flex-shrink-0" />
    <div class="flex-1 min-w-0 ml-2">
      <h3 class="font-bold text-sm truncate">{{name}}</h3>
      <p class="text-gray-600 text-xs">{{price}}</p>
    </div>
  </div>

## General rules
- Always use tools for real data — never hallucinate product info, prices, or order details
- Extract numeric values from prices before passing to tools ($100 → 100)
- session_id is always available in the (SYSTEM) block at the start of the user message
- Respond in the JSON format defined by your response schema

{tool_descriptions}
"""


# ---------------------------------------------------------------------------
# Agent initialisation
# ---------------------------------------------------------------------------

tools = [
    # Read
    FunctionTool(search_products_tool),
    FunctionTool(get_product_details_tool),
    FunctionTool(check_stock_tool),
    FunctionTool(cart_summary_tool),
    FunctionTool(order_status_tool),
    FunctionTool(list_orders_tool),
    FunctionTool(faq_tool),
    # Action — all DB-direct
    FunctionTool(add_to_cart_tool),
    FunctionTool(update_cart_item_tool),
    FunctionTool(remove_from_cart_tool),
    FunctionTool(save_address_tool),
    FunctionTool(get_saved_addresses_tool),
    FunctionTool(place_order_tool),
    FunctionTool(submit_review_tool),
    #User tools
    FunctionTool(get_user_profile_tool),
    FunctionTool(create_user_tool),
    FunctionTool(update_user_profile_tool),
    FunctionTool(login_user_tool),
    FunctionTool(old_session_cart_transfer_tool),

]

checkpointer = MemorySaver()

agent = AgentCore(
    tools=tools,
    prompt_template=SYSTEM_PROMPT,
    response_schema=ECommerceResponse,
    llm_name="ecom_agent",
    llm_config={
        "provider": "cerebras",
        "model": settings.CEREBRAS_MODEL_NAME,
        "api_key": settings.CEREBRAS_API_KEY
    },
    checkpointer=checkpointer
)


# ---------------------------------------------------------------------------
# Context formatting — minimal payload from frontend
# ---------------------------------------------------------------------------

def format_message_with_context(
    message: str,
    session: str,
    page_type: Optional[str] = None,
    route: Optional[str] = None,
    mode: str = "text"
) -> str:
    """
    Build the message the agent sees.
    Frontend only needs to send: session_id, current route, page_type, mode.
    No DOM, no visible actions, no element selectors.
    """
    system_block = (
        f"(SYSTEM) session_id: {session} | "
        f"route: {route or 'unknown'} | "
        f"page_type: {page_type or 'unknown'} | "
        f"MODE: {mode}\n"
    )
    return f"{system_block}User Message: {message}"


# ---------------------------------------------------------------------------
# Service entry points
# ---------------------------------------------------------------------------

async def AgentCoreService(
    message: str,
    session: str,
    page_type: Optional[str] = None,
    route: Optional[str] = None,
    mode: str = "text"
) -> dict:
    try:
        formatted = format_message_with_context(message, session, page_type, route, mode)
        response = await agent.run_agent(message=formatted, session_id=session)
        return response
    except Exception as e:
        return {"message": f"Agent error: {str(e)}", "action": [], "html_content": ""}


async def AgentCoreServiceStream(
    message: str,
    session: str,
    page_type: Optional[str] = None,
    route: Optional[str] = None,
    mode: str = "text"
):
    try:
        formatted = format_message_with_context(message, session, page_type, route, mode)
        async for event in agent.astream_agent(message=formatted, session_id=session):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

# NOTE: Replace the format_message_with_context function above with this version
# that wires in the route enricher. The import is already added at the top.
#
# def format_message_with_context(...):
#     system_block = f"(SYSTEM) session_id: {session} | route: {route} | ..."
#     enriched = enrich_context_from_route(session, route)
#     enriched_block = format_enriched_context(enriched)
#     return f"{system_block}{enriched_block}User Message: {message}"
#
# Full wired version is the one in this file — see format_message_with_context above.
# The enricher import line was added at line 1 of the imports block.