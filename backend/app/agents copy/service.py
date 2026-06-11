from ai_agent_core.agent_core import AgentCore
from ai_agent_core.tools.base_tool import FunctionTool
from langgraph.checkpoint.memory import MemorySaver
from typing import Optional, List
from pydantic import BaseModel, Field
from app.agents.tools import (
        search_products_tool,
        get_product_details_tool,
        check_stock_tool,
        cart_summary_tool,
        order_status_tool,
        faq_tool,
        agent_flow_rules
)
from app.agents.page_context import (request_page_context_tool, get_page_context_tool)
from config import get_settings

import json

settings = get_settings()


class UIAction(BaseModel):
    type: str = Field(description="'none', 'navigate', 'add_to_cart', 'click', etc.")
    target: Optional[str] = Field(default=None, description="URL or element selector")
    data: Optional[str] = Field(default=None, description="Additional data for action")
    require_confirmation: bool = Field(default=False)

class ECommerceResponse(BaseModel):
    message: str = Field(description="Your response text to the user")
    html_content: Optional[str] = Field(default="", description="Optional HTML content of product details with Tailwind classes")
    action: List[UIAction] = Field(default_factory=list, description="List of UI actions to perform")
    speak: bool = Field(default=False, description="True if Voice mode")
    context_requested: bool = Field(default=False, description="Set to true to request page context from frontend")


# System prompt for the assistant
SYSTEM_PROMPT = """You are a helpful AI shopping assistant for an elegant dress e-commerce store with voice and navigation capabilities.

Your role is to:
- Help customers discover and search for dresses
- Provide detailed product information
- Check stock availability
- Answer questions about cart and orders
- Provide information about store policies (shipping, returns, refunds)
- Navigate users to relevant pages when requested


**Agent action guide:**
    Navigation Rules:
        When user says:
        - "Open product X" / "Show me product X" → {{"type": "navigate", "target": "/product/{{id}}"}}
        - "Go to cart" / "Open cart" → {{"type": "navigate", "target": "/cart"}}
        - "Checkout" / "Proceed to checkout" → {{"type": "navigate", "target": "/checkout"}}
        - "My orders" / "Track order" → {{"type": "navigate", "target": "/orders"}}
        - "Go home" / "Show all dresses" → {{"type": "navigate", "target": "/"}}
        - Otherwise → {{"type": "none", "target": null}}

    Add to Cart Flow:
        step 1: Navigate to product page.
        step 2: Ask no of quantity and other options if needed based on page context.
        step 3: Return action with confirmation for adding to cart:
        Note: Use the 'enter' action type to securely type the exact quantity into the input field instead of clicking buttons multiple times.
        action:[
            {{"type":"enter", "target": "#product_quantity", "data": "3", "require_confirmation": false}},
            {{"type":"click", "target": "#add_to_cart", "data": "Add to cart", "require_confirmation": True}},
        ]

    Click | Focus | Enter  Rules:
    Look for Page Context Usage:
    - If the user asks you to perform DOM actions on the current page, first call `get_page_context_tool` using the `session_id` provided in the `(SYSTEM)` block at the start of learning to inspect the stored DOM blocks.
    - Check if the DOM block you receive matches the `(SYSTEM) Current Page Context` string provided at the start of the user's prompt.
    - If the context from `get_page_context_tool` is empty, or the route/URL inside the data does not match the system context route exactly, or the context is not relevant/require more details for the user's request, DO NOT guess selectors or return actions yet. Instead, you MUST immediately return `context_requested: true` in your JSON output.
    - Returning `context_requested: true` tells the frontend to securely intercept your response and upload the current layout via a hidden message. 
    - Once you have the context verified, build actions securely.
    - Each step should be based of page context. Do not ask for all fields at once.     
    

**Interaction Modes (from context):**
- MODE: text → speak: false
- MODE: voice → speak: true

**HTML Content Response Rules:**
- Can include rich HTML with Tailwind styling
- CRITICAL: The AI Assistant chat UI has a strict maximum width of 350px. All HTML generated MUST be compact, vertically aligned, and fit within this narrow view without horizontal scrolling. Use smaller images, compact padding, flex-col or tight flex-row, text-sm, and word-wrap. Avoid large tables.
- Use product cards with images in a narrow, compact style:
  <div class="bg-white p-3 rounded-lg shadow mb-2 flex gap-3 items-center">
    <img src="{{image_url}}" alt="{{name}}" class="w-16 h-16 object-cover rounded flex-shrink-0" />
    <div class="flex-1 min-w-0">
      <h3 class="font-bold text-sm truncate">{{name}}</h3>
      <p class="text-gray-600 text-xs">{{price}}</p>
      <a href="/product/{{id}}" class="text-pink-600 text-xs hover:underline">View</a>
    </div>
  </div>

**REMEMBER:**
- ALWAYS respond in the JSON format above
- ALWAYS use tools for real data
- ALWAYS navigate to product page when you suggest List of products (on voice mode).
- CRITICAL: If you tell the user you are navigating them to a page, you MUST populate the `action` array with the `{"type": "navigate", "target": "..."}` JSON dictionary. NEVER leave the action array empty `[]` when performing UI Navigation.
- Extract numeric values from prices ($100 → 100)
- Adapt message format based on mode (text vs voice)
- Detect navigation intent and set action accordingly
- Never hallucinate information
- If request needed action and type is 'click' then mention short note on "data":{"Need permission to add the product to cart"} or similar based on action.

Use the available tools when users ask about products.
{tool_descriptions}
"""


async def test_agent():
    tools = [
        FunctionTool(search_products_tool),
        FunctionTool(get_product_details_tool),
        FunctionTool(check_stock_tool),
        FunctionTool(cart_summary_tool),
        FunctionTool(order_status_tool),
        FunctionTool(faq_tool),
        FunctionTool(agent_flow_rules)
    ]

    # Initialize LangGraph checkpointer
    checkpointer = MemorySaver()

    agent = AgentCore(
        tools=tools,
        prompt_template=SYSTEM_PROMPT,
        response_schema=ECommerceResponse,
        llm_name="ecom_test",
        # Switching to Cerebras for fast inference or OpenAI based on availability
        llm_config={"provider": "cerebras", "model": "llama3.1-8b","api_key":settings.CEREBRAS_API_KEY},
        checkpointer=checkpointer
    )

    session_id = "ecom_sess_1"

    try:
        msg = 'hello'
        
        # Use run_agent with session_id for stateful persistence
        response = await agent.run_agent(message=msg, session_id=session_id)
        
        print("\n-------------------------")
        print("Message:", response.get('message'))
        print("HTML:", response.get('html_content'))
        print("Actions:", response.get('action'))
        print("-------------------------\n")

        msg = 'Any party dress'
        
        # Use run_agent with session_id for stateful persistence
        response = await agent.run_agent(message=msg, session_id=session_id)
        
        print("\n-------------------------")
        print("Message:", response.get('message'))
        print("HTML:", response.get('html_content'))
        print("Actions:", response.get('action'))
        print("-------------------------\n")
    except Exception as e:
        print(f"Error: {e}")

tools = [
        FunctionTool(search_products_tool),
        FunctionTool(get_product_details_tool),
        FunctionTool(check_stock_tool),
        FunctionTool(cart_summary_tool),
        FunctionTool(order_status_tool),
        FunctionTool(faq_tool),
        FunctionTool(agent_flow_rules),
        FunctionTool(request_page_context_tool),
        FunctionTool(get_page_context_tool) 
    ]

# Initialize LangGraph checkpointer
checkpointer = MemorySaver()

agent = AgentCore(
    tools=tools,
    prompt_template=SYSTEM_PROMPT,
    response_schema=ECommerceResponse,
    llm_name="ecom_test",
    # Switching to Cerebras for fast inference or OpenAI based on availability
    # llm_config={"provider": "cerebras", "model": "llama3.1-8b","api_key":settings.CEREBRAS_API_KEY,"streaming":True},
    llm_config={"provider": "google", "model": settings.GOOGLE_MODEL_NAME,"api_key":settings.GOOGLE_API_KEY},
    checkpointer=checkpointer
)

def format_message_with_context(message: str, page_type: Optional[str], route: Optional[str], session: str) -> str:
    context_prefix = ""
    if page_type or route:
        context_prefix = f"[(SYSTEM) Current Page type: {page_type or 'Unknown'}, route: {route or 'Unknown'}, session_id: {session}]\n"
    return f"{context_prefix}User Message: {message}\n"

async def AgentCoreService(message:str, session:str, page_type: Optional[str] = None, route: Optional[str] = None):

    try:        
        formatted_message = format_message_with_context(message, page_type, route, session)
        # Use run_agent with session_id for stateful persistence
        response = await agent.run_agent(message=formatted_message, session_id=session)
        return response
    except Exception as e:
        return f'Error: {e}'
    
async def AgentCoreServiceStream(message:str, session:str, page_type: Optional[str] = None, route: Optional[str] = None):

    try:        
        formatted_message = format_message_with_context(message, page_type, route, session)
        # Use run_agent with session_id for stateful persistence
        async for event in agent.astream_agent(message=formatted_message, session_id=session):
            json_data = json.dumps(event)
            yield f"data: {json_data}\n\n"
            
    except Exception as e:
        error_event = {
            "type": "error",
            "data": f"Agent encountered an error: {str(e)}"
        }
        yield f"data: {json.dumps(error_event)}\n\n"

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent())

