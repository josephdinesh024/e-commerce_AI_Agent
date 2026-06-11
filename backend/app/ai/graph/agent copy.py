import datetime
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
# from langchain_ollama import ChatOllama
from langchain_fireworks import ChatFireworks
from langchain_cerebras import ChatCerebras
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.tools.tools import get_tools
from app.ai.schemas import MessageType, MessageRole, SessionMessage, SessionMemory
from config import get_settings
import asyncio
import json

# Initialize settings and LLM
settings = get_settings()

# In-memory session store (in production, use Redis)
session_store: Dict[str, SessionMemory] = {}

# llm = ChatGroq(
#     groq_api_key=settings.GROQ_API_KEY,
#     model_name=settings.MODEL_NAME,
#     temperature=settings.TEMPERATURE,
#     streaming=True
# )

# llm = ChatFireworks(
#     api_key=settings.FIREWORKS_API_KEY,
#     model_name=settings.FIREWORKS_MODE_NAME,
#     temperature=settings.TEMPERATURE,
#     streaming=True
# )

llm = ChatCerebras(
    api_key=settings.CEREBRAS_API_KEY,
    model_name=settings.CEREBRAS_MODE_NAME,
    temperature=settings.TEMPERATURE
)

# llm = ChatOllama(
#     model="llama3.1:8b",
#     temperature=0.1
# )

# Get tools
tools = get_tools()

# System prompt for the assistant
SYSTEM_PROMPT = """You are a helpful AI shopping assistant for an elegant dress e-commerce store with voice and navigation capabilities.

Your role is to:
- Help customers discover and search for dresses
- Provide detailed product information
- Check stock availability
- Answer questions about cart and orders
- Provide information about store policies (shipping, returns, refunds)
- Navigate users to relevant pages when requested

**CRITICAL: Response Format**
You MUST respond in this JSON structure:
{{
  "message": "your response text here",
  "html_content": "HTML content of product details",
  "action": [
    {{
        "type": "none" | "navigate" | "add_to_cart" | "click" | "focus" | "enter",
        "target": "URL" | "element_selector" | null,
        "data": "additional data for action, e.g. form field value, or path to navigate",
        "require_confirmation": true | false
    }},
  ],
  "speak": true | false,
}}

To request page context you MUST response wiht json:
{{
"context_requested": true | false
}}

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
        Note: Always use Increase/ Decrease quantity button as sparate actions, no 'enter' types only 'click'.
        action:[
            {{"type":"click", "target":{{element_selector}}, "data":null, "require_confirmation": false}},
            {{"type":"click", "target":{{element_selector}}, "data":null, "require_confirmation": false}},
            {{"type":"click", "target":{{element_selector}}, "data": "Add to cart", "require_confirmation": True}},
        ]

    Click | Focus | Enter  Rules:
    Look for Page Context Usage:
    - If user wants to perform actions (login, fill form, add, click), check if you have page context
    - Use get_page_context_tool to check if context is available
    - If no context and action needed, use request_page_context_tool
    - Also check with current page titel and route, if no then navigate to correct page first.
    - Once you have context, build actions with page context.
    - Each step should be based of page context. Do not ask for all fields at once.     
    
    Note: Should use agent_flow_rules tool for detailed action rules based on flow type ('user_login', 'user_register', 'add_to_cart').

**Interaction Modes (from context):**
- MODE: text → speak: false
- MODE: voice → speak: true

**HTML Content Response Rules:**
- Can include rich HTML with Tailwind styling
- Use product cards with images:
  <div class="bg-white p-4 rounded-lg shadow">
    <img src="{{image_url}}" alt="{{name}}" class="w-full h-40 object-cover rounded-lg mb-2" />
    <h3 class="font-bold">{{name}}</h3>
    <p class="text-gray-600">{{price}}</p>
    <a href="/product/{{id}}" class="text-pink-600 hover:underline">View Details</a>
  </div>

**Tool Usage Rules:**
- search_products_tool: keyword, min_price (NUMBER), max_price (NUMBER), color
- get_product_details_tool: product_id or product_name
- check_stock_tool: product_id
- cart_summary_tool: session_id (provided in context)
- order_status_tool: order_id
- faq_tool: question
- request_page_context_tool: session_id, reason to make frontend send page context in next interaction.
- get_page_context_tool: session_id to get stored page context for current session.
    Note: First try to use get_page_context_tool to check if you have context, if not then use request_page_context_tool to ask frontend to send context in next user message.
- agent_flow_rules: flow type (e.g. "navigate", "add_to_cart", "user_login") to get specific action rules for that flow.

**REMEMBER:**
- ALWAYS respond in the JSON format above
- ALWAYS use tools for real data
- Extract numeric values from prices ($100 → 100)
- Adapt message format based on mode (text vs voice)
- Detect navigation intent and set action accordingly
- Never hallucinate information"""


# Create prompt template with session context
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT + "\n\nCurrent user session_id: {session_id}\nInteraction mode: {mode}\n Current page Title: {page_type}, Current page route url: {route}"),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create the agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create agent executor with better configuration
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # Set to True for debugging
    max_iterations=settings.MAX_ITERATIONS,
    handle_parsing_errors=True,
    return_intermediate_steps=False,
    early_stopping_method="generate"  # Important: ensures final answer is generated
)


def get_or_create_session(session_id: str, mode: MessageType) -> SessionMemory:
    """Get existing session or create new one"""
    if session_id not in session_store:
        session_store[session_id] = SessionMemory(
            session_id=session_id,
            mode=mode,
            history=[],
            route="/"
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

async def run_agent(message: str, session_id: str, conversation_history: list = None, mode: str = "text", page_type: Optional[str] = None, route: Optional[str] = None):
    """
    Run the agent with a user message
    
    Args:
        message: User's input message
        session_id: User's session ID
        conversation_history: Previous conversation messages
        mode: "text" or "voice" - determines response format
    
    Returns:
        Generator yielding response chunks
    """
    try:
        session = get_or_create_session(session_id, MessageType(mode))

        if route:
            session.route = route
        
        session.mode = MessageType(mode)
        
        # Prepare chat history
        chat_history = []
        if conversation_history:
            for msg in conversation_history[-6:]:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    # Extract just the message from JSON if present
                    content = msg["content"]
                    try:
                        parsed = json.loads(content)
                        content = parsed.get("message", content)
                    except:
                        pass
                    chat_history.append(AIMessage(content=content))
        
        # Invoke the agent with mode parameter
        response = await agent_executor.ainvoke({
            "input": message,
            "chat_history": chat_history,
            "session_id": session_id,
            "mode": mode,  # Pass mode to agent
            "page_type": page_type,
            "route": route
        })
        
        # Get the output
        output = response.get("output", "")
        
        if not output or not output.strip():
            output = json.dumps({
                "message": "I apologize, but I couldn't find any information for that request.",
                "action": {"type": "none", "target": None},
                "speak": mode == "voice"
            })
        
        # Try to parse as JSON, if fails wrap it
        try:
            parsed = json.loads(output)
            # Ensure required fields exist
            if "message" not in parsed:
                parsed["message"] = output
            if "action" not in parsed:
                parsed["action"] = {"type": "none", "target": None}
            if "speak" not in parsed:
                parsed["speak"] = (mode == "voice")
            output = json.dumps(parsed)
        except:
            # Not JSON, wrap it in structure
            output = json.dumps({
                "message": output,
                "action": {"type": "none", "target": None},
                "speak": mode == "voice"
            })
        
        # Return the structured response
        yield {
            "type": "done",
            "content": output,
            "done": True
        }
        
    except Exception as e:
        error_str = str(e)
        print(f"Agent error: {error_str}")
        import traceback
        traceback.print_exc()
        
        error_response = json.dumps({
            "message": "I apologize, but I encountered an error. Please try again.",
            "action": {"type": "none", "target": None},
            "speak": mode == "voice"
        })
        
        yield {
            "type": "error",
            "content": error_response,
            "done": True
        }

async def run_agent_text(message: str, session_id: str, conversation_history: list = None):
    """
    Run the agent with a user message
    
    Args:
        message: User's input message
        session_id: User's session ID
        conversation_history: Previous conversation messages
    
    Returns:
        Generator yielding response chunks
    """
    try:
        # Prepare chat history
        chat_history = []
        if conversation_history:
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
        
        # Invoke the agent (this executes tools and returns final answer)
        response = await agent_executor.ainvoke({
            "input": message,
            "chat_history": chat_history,
            "session_id": session_id, # Pass session_id for cart/order queries
            "mode": "text" 
        })
        
        # Get the output
        output = response.get("output", "")
        
        # Check if output is empty or just whitespace
        if not output or not output.strip():
            output = "I apologize, but I couldn't find any information for that request. Could you please rephrase your question?"
        
        # Return the complete response
        yield {
            "type": "done",
            "content": output,
            "done": True
        }
        
    except Exception as e:
        error_str = str(e)
        print(f"Agent error: {error_str}")  # Log error
        import traceback
        traceback.print_exc()
        
        # Provide helpful error message based on error type
        if "validation failed" in error_str:
            error_message = "I had trouble processing that request. Could you try rephrasing it? For example, instead of 'under $100', try 'under 100 dollars'."
        elif "session_id" in error_str:
            error_message = "I'm having trouble accessing your cart. Please make sure you're logged in."
        else:
            error_message = "I apologize, but I encountered an error. Please try rephrasing your question or try again."
        
        yield {
            "type": "error",
            "content": error_message,
            "done": True
        }

