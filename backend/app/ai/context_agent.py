from typing import Dict, Any
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import get_settings
from app.ai.context_schemas import ContextInput, ContextResponse
from app.ai.graph.agent import get_or_create_session, MessageType, MessageRole, update_session_history
import json

settings = get_settings()

# Initialize LLM for context agent
# context_llm = ChatGroq(
#     groq_api_key=settings.GROQ_API_KEY,
#     model_name=settings.MODEL_NAME,
#     temperature=0.3,  # Lower temperature for more consistent suggestions
# )

context_llm = ChatGoogleGenerativeAI(
    api_key=settings.GOOGLE_API_KEY,
    model=settings.GOOGLE_MODEL_NAME,
    temperature=settings.TEMPERATURE
)

CONTEXT_AGENT_PROMPT = """You are a Context-Aware AI Copilot for an e-commerce platform.

Your job is to analyze user behavior and page context to provide helpful, non-intrusive suggestions.

CRITICAL RULES:
1. Return ONLY valid JSON (no markdown, no explanation)
2. NEVER auto-execute sensitive actions
3. NEVER request passwords or personal info
4. Only suggest when genuinely helpful
5. Respect user privacy and autonomy

CONTEXT-BASED TRIGGERS:

LOGIN PAGE:
- If user_idle_seconds > 8 AND form fields not filled → Suggest help
- Message: "Need help logging in? I can guide you step by step."
- require_confirmation: true

PRODUCT PAGE:
- If time_spent > 15 seconds → Suggest related items or size guide
- Message: "Would you like to see similar dresses or check available sizes or need add product to cart?"
- require_confirmation: false

CART PAGE:
- If items_count > 0 AND user_idle_seconds > 10 → Suggest checkout
- Message: "Ready to checkout? I can guide you through shipping and payment."
- action.type: "navigate", action.target: "/checkout"
- require_confirmation: true

CHECKOUT PAGE:
- If form incomplete → Suggest reviewing fields
- Message: "Need help completing your order? Let me assist you."
- require_confirmation: false

HOME PAGE:
- Generally no suggestions unless idle > 20s
- Message: "Looking for something specific? I can help you find it."

ORDERS PAGE:
- No proactive suggestions (respect privacy)

CONFIDENCE SCORING:
- High confidence (0.8-1.0): Clear user need, helpful suggestion
- Medium confidence (0.6-0.8): Potentially helpful
- Low confidence (<0.6): Don't show popup

OUTPUT FORMAT (strict JSON):
{{
  "show_popup": true/false,
  "popup_message": "helpful message",
  "popup_type": "info" | "assist" | "warning",
  "action": {{
        "type": "none" | "navigate"  | "click" | "focus" | "enter",
        "target": "URL" | "element_selector" | null,
        "data": "additional data for action, e.g. form field value, or path to navigate"
    }}
  "require_confirmation": true/false,
  "confidence": 0.0-1.0
}}

Note: Actions are optionals, Suggest only when action like "navigate", "click" to add or increase product quantity.

If no suggestion needed, return:
{{
  "show_popup": false,
  "popup_message": "",
  "popup_type": "info",
  "require_confirmation": false,
  "confidence": 0.5
}}

CURRENT CONTEXT:
{context}

Return ONLY the JSON response. No other text."""

prompt = ChatPromptTemplate.from_messages([
    ("system", CONTEXT_AGENT_PROMPT),
    MessagesPlaceholder(variable_name="chat_history", optional=True)
])

def analyze_context(context_input: ContextInput) -> ContextResponse:
    """
    Analyze page context and return suggestion
    
    Args:
        context_input: Page context information
    
    Returns:
        ContextResponse with popup configuration
    """
    try:
        chat_history = []
        session = None
        if context_input.session_id:
            session = get_or_create_session(context_input.session_id, MessageType("text"))
            # Prepare chat history
        
            if session.history:
                for msg in session.history[-6:]:
                    if msg.role == MessageRole.user:
                        chat_history.append(HumanMessage(content=msg.content))
                    elif msg.role == MessageRole.assistant:
                        # Extract just the message from JSON if present
                        content = msg.content
                        try:
                            parsed = json.loads(content)
                            content = parsed.get("message", content)
                        except:
                            pass
                        chat_history.append(AIMessage(content=content))

        # Convert input to dict for prompt
        context_dict = context_input.model_dump()
        context_str = json.dumps(context_dict, indent=2)
        
        # Invoke LLM
        chain = prompt | context_llm
        response = chain.invoke({
            "context": context_str,
            "chat_history": chat_history
            })
        
        # Parse response
        response_text = response.content.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        
        # Parse JSON
        response_data = json.loads(response_text)
        # Validate with Pydantic
        validated_response = ContextResponse(**response_data)
    
        if session:
            #Add assistant response to session history
            update_session_history(
                session,
                MessageRole.assistant,
                validated_response.popup_message,
                MessageType("text")
            )
        # Validate with Pydantic
        return validated_response
        
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        # Return safe default
        return ContextResponse(
            show_popup=False,
            popup_message="",
            popup_type="info",
            action={"type": "none", "target": None},
            require_confirmation=False,
            confidence=0.0
        )
    except Exception as e:
        print(f"Context agent error: {e}")
        import traceback
        traceback.print_exc()
        # Return safe default
        return ContextResponse(
            show_popup=False,
            popup_message="",
            popup_type="info",
            action={"type": "none", "target": None},
            require_confirmation=False,
            confidence=0.0
        )


def should_show_suggestion(
    page_type: str,
    user_idle_seconds: int,
    context_data: Dict[str, Any]
) -> bool:
    """
    Quick rule-based check before calling LLM
    Reduces unnecessary API calls
    """
    # Don't spam suggestions
    if user_idle_seconds < 3:
        return False
    
    # Page-specific rules
    if page_type == "login":
        return user_idle_seconds > 8
    
    if page_type == "product":
        product_context = context_data.get("product_context", {})
        if product_context:
            time_spent = product_context.get("time_spent", 0)
            return time_spent > 20
        else:
            return context_data.get("user_idle_seconds", 0) > 20
    
    if page_type == "cart":
        items = context_data.get("cart_context", {}).get("items_count", 0)
        return items > 0 and user_idle_seconds > 10
    
    if page_type == "checkout":
        return user_idle_seconds > 5
    
    if page_type == "home":
        return user_idle_seconds > 30
    
    # No suggestions for orders page (privacy)
    if page_type == "orders":
        return False
    
    return False