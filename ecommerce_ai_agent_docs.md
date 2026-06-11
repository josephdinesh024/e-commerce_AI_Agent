# E-Commerce AI Agent — Project Document

> **Version:** 1.0 · **Date:** May 2026 · **Status:** Active Development

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Architecture](#2-architecture)
3. [Agent Flows](#3-agent-flows)
4. [Developer Reference](#4-developer-reference)
5. [Deployment & Ops](#5-deployment--ops)

---

## 1 — Introduction

### 1.1 What This Is

The E-Commerce AI Agent is a conversational shopping assistant embedded directly into a dress store web application. It understands natural language (text or voice), executes backend operations on behalf of the customer, and guides them through the full purchase journey — from product discovery all the way to order placement — without requiring the customer to manually navigate forms or pages.

### 1.2 Key Capabilities

| Capability | How it works |
|---|---|
| **Product search & recommendations** | Keyword / price / color search against live database |
| **Product details** | Full info including stock level and ratings |
| **Cart management** | Add, update, remove items — all executed server-side |
| **Checkout** | Conversational address collection → order placement in one flow |
| **Order tracking** | Fetch live order status and history |
| **Reviews** | Submit and update product reviews |
| **Store policies (FAQ)** | Built-in static knowledge base for shipping, returns, sizing |
| **Voice mode** | Web Speech API STT + browser TTS; identical backend, different frontend rendering |

### 1.3 Design Philosophy

The agent follows a **Backend-Owns-All-Mutations** principle:

> All state changes (cart, orders, addresses, reviews) are executed directly by backend tools. The frontend never clicks buttons, fills forms, or scrapes DOM elements on behalf of the agent.

The frontend only reacts to three clean signals from the backend response:
- `navigate` → push the user to a new URL
- `cart_refresh` → re-fetch cart count badge
- `confirmation_required` → show a blocking confirm banner before an order is placed

This makes the agent robust to UI redesigns — the backend logic never changes when the frontend changes.

---

## 2 — Architecture

### 2.1 High-Level Component Map

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND (React)               │
│                                                 │
│  ┌──────────────────┐  ┌────────────────────┐   │
│  │  CopilotWidget   │  │  CopilotContext     │   │
│  │  (UI rendering)  │◄─│  (state + API calls)│  │
│  └──────────────────┘  └────────────────────┘   │
│          │ POST /chat/agent                      │
└──────────┼──────────────────────────────────────┘
           │ HTTP JSON
┌──────────▼──────────────────────────────────────┐
│                BACKEND (FastAPI)                │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │   /chat/agent  →  AgentCoreService       │   │
│  └──────────────────────────────────────────┘   │
│          │                                       │
│  ┌───────▼──────────────────────────────────┐   │
│  │         ai_agent_core (library)           │   │
│  │                                           │   │
│  │  AgentCore                                │   │
│  │    └─ AgentRunner (LangGraph StateGraph)  │   │
│  │         ├─ _call_model (async LLM call)   │   │
│  │         └─ _call_tools (ToolExecutor)     │   │
│  └───────────────────────┬───────────────────┘   │
│                          │                       │
│  ┌───────────────────────▼───────────────────┐   │
│  │            Tool Layer                     │   │
│  │  (Read tools + Action tools)              │   │
│  │  All tools are plain Python functions     │   │
│  └───────────────────────┬───────────────────┘   │
│                          │                       │
│  ┌───────────────────────▼───────────────────┐   │
│  │          PostgreSQL Database              │   │
│  │  Products · Carts · Orders · Addresses    │   │
│  │  Reviews · OrderItems · CartItems         │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 2.2 Layer Descriptions

#### Layer 1 — Frontend UI (`frontend/src/components/agentCopilot/`)

| File | Role |
|---|---|
| [`CopilotWidget.jsx`](file:///C:/folder-e/workspace/e-commerce/frontend/src/components/agentCopilot/CopilotWidget.jsx) | Renders the floating chat panel, message bubbles, suggestion chips, confirm banner, and voice button |
| [`CopilotContext.jsx`](file:///C:/folder-e/workspace/e-commerce/frontend/src/components/agentCopilot/CopilotContext.jsx) | React Context provider — owns all state, API calls, voice STT/TTS, and action dispatch |
| [`useCopilot.js`](file:///C:/folder-e/workspace/e-commerce/frontend/src/components/agentCopilot/useCopilot.js) | Convenience hook that exposes `CopilotContext` to any component |

**Key frontend data flow:**
1. User types or speaks → `sendMessage()` is called in `CopilotContext`
2. A `POST /chat/agent` request is made with `{ message, session_id, route, page_type, mode }`
3. The JSON response (`ECommerceResponse`) is parsed
4. `handleActions()` is called — dispatches `navigate` or fires `agent:cart_refresh` event
5. If `confirmation_required=true`, a blocking `ConfirmBanner` is shown
6. In voice mode, `speakMessage()` speaks the `message` text via browser TTS

#### Layer 2 — API Endpoint (`backend/app/routes/chat.py`)

The primary agent endpoint:

```
POST /chat/agent
```

Accepts `AgentCoreRequest`:
```python
class AgentCoreRequest(BaseModel):
    message: str
    session_id: str = 'user_01'
    page_type: Optional[str] = None
    route: Optional[str] = None
    mode: str = "text"   # "text" | "voice"
```

A streaming variant is also available at `POST /chat/agent-stream` for SSE output.

#### Layer 3 — Agent Service (`backend/app/agents/service.py`)

`AgentCoreService` is the async entry point:
1. Calls `format_message_with_context()` to prepend a system block: `(SYSTEM) session_id: X | route: /product/5 | page_type: product | MODE: text`
2. Calls `await agent.run_agent(message=formatted, session_id=session)`
3. Returns the structured `ECommerceResponse` dict to the route handler

#### Layer 4 — `ai_agent_core` Library (`C:/folder-e/workspace/ai_agent_core/`)

A reusable, provider-agnostic agent framework:

| Module | Responsibility |
|---|---|
| `AgentCore` | Public API — initialises tools, LLM, prompt builder, and runner |
| `AgentRunner` | Builds and executes the LangGraph `StateGraph`. Handles retry with self-correction on schema validation failures |
| `LLMManager` | Factory for LangChain chat model instances (OpenAI / Groq / Cerebras / Google / Ollama) |
| `PromptBuilder` | Injects `{tool_descriptions}` and `{response_schema}` into the system prompt template |
| `FunctionTool` | Wraps any plain Python function into a `BaseTool` compatible with LangChain's `StructuredTool` |
| `ToolExecutor` | Async dispatch layer — routes LLM tool calls to the correct registered `FunctionTool` |
| `ToolRegistry` | In-memory dict of all registered tools by name |

#### Layer 5 — Tool Layer (`backend/app/agents/tools.py`)

14 plain Python functions — no class inheritance required. Each is wrapped with `FunctionTool()` at startup.

#### Layer 6 — Database (`PostgreSQL`)

Managed by SQLAlchemy ORM. Core tables:

```
products        id, name, description, price, stock, image_url, is_listed
carts           id, session_id
cart_items      id, cart_id → carts, product_id → products, quantity
addresses       id, session_id, name, phone, address, city, state, pincode
orders          id, session_id, address_id → addresses, total_amount, status
order_items     id, order_id → orders, product_id → products, quantity, price
reviews         id, product_id → products, session_id, rating, comment
```

### 2.3 LangGraph Execution Model

The agent uses a `StateGraph` with two nodes:

```
[START]
   │
   ▼
[agent node]  ← calls LLM with current message history
   │
   ├── tool_calls present? ──YES──► [execute_tools node] ──► back to [agent node]
   │
   └── no tool_calls (or schema tool called) ──► [END]
```

- **Memory:** `MemorySaver` checkpointer keyed on `session_id` (thread_id). Conversation history persists in-process across requests.
- **Max iterations:** Configurable (default 5). Prevents infinite tool-call loops.
- **Self-correction:** On Pydantic `ValidationError`, the runner injects a correction message and retries up to 3 times before falling back to lenient parsing.

### 2.4 Response Schema (`ECommerceResponse`)

The structured JSON the LLM must always return:

```python
class ECommerceResponse(BaseModel):
    message: str                          # conversational text
    html_content: Optional[str] = ""      # product card HTML (text mode only)
    action: List[UIAction] = []           # navigate | cart_refresh | none
    suggestions: List[str] = []           # 2-4 follow-up chips
    confirmation_required: bool = False   # True only before place_order_tool
    speak: bool = False                   # True when MODE=voice

class UIAction(BaseModel):
    type: Literal["none", "navigate", "cart_refresh"]
    target: Optional[str] = None          # e.g. "/orders", "/product/12"
```

### 2.5 Context Injection

The frontend sends only two pieces of context metadata per request: `route` (current URL path) and `page_type`. These are embedded in a `(SYSTEM)` prefix prepended to the user message:

```
(SYSTEM) session_id: abc123 | route: /product/5 | page_type: product | MODE: text
User Message: Can you add this to my cart?
```

An optional `enrich_context_from_route()` function in [`page_context.py`](file:///C:/folder-e/workspace/e-commerce/backend/app/agents/page_context.py) can hydrate additional DB data (product details, cart contents, order list) directly into this system block based on the route — removing the need for the agent to call a read tool first.

### 2.6 LLM Provider Support

| Provider | LangChain Package | Config key |
|---|---|---|
| Google Gemini | `langchain-google-genai` | `"provider": "google"` |
| Groq | `langchain-groq` | `"provider": "groq"` |
| Cerebras | `langchain-cerebras` | `"provider": "cerebras"` |
| OpenAI | `langchain-openai` | `"provider": "openai"` |
| Ollama (local) | `langchain-ollama` | `"provider": "local"` |

The active provider is configured in `service.py`:
```python
llm_config = {
    "provider": "google",
    "model": settings.GOOGLE_MODEL_NAME,   # e.g. "gemini-3-pro-preview"
    "api_key": settings.GOOGLE_API_KEY
}
```

---

## 3 — Agent Flows

All flows follow this universal pattern:

```
User message
    │
    ▼
format_message_with_context()   → prepend (SYSTEM) block
    │
    ▼
LLM (with bound tools)          → decide intent → call tools
    │
    ▼
ToolExecutor.aexecute()         → run Python function → DB query/mutation
    │
    ▼
LLM receives tool result        → generate ECommerceResponse JSON
    │
    ▼
AgentRunner._parse_output()     → validate against Pydantic schema
    │
    ▼
AgentCoreService returns dict   → HTTP response to frontend
    │
    ▼
CopilotContext.sendMessage()    → render message, dispatch actions, TTS if voice
```

### 3.1 Product Search Flow

**Trigger:** "Show me red dresses under $100"

```
User: "Show me red dresses under $100"
  │
  ├─ LLM extracts intent: search, color=red, max_price=100
  │
  ├─ Calls: search_products_tool(keyword="dress", color="red", max_price=100.0)
  │      └─ DB: SELECT products WHERE price <= 100 AND (name ILIKE '%red%' OR desc ILIKE '%red%')
  │      └─ Returns: JSON array of up to 10 products with ratings
  │
  └─ Response:
       message: "Here are some beautiful red dresses under $100..."
       html_content: <compact product cards with images>
       action: []
       suggestions: ["Add to cart", "See more dresses", "Filter by size"]
```

### 3.2 Cart Add Flow

**Trigger:** "Add 2 of those to my cart" (after viewing search results)

```
User: "Add 2 of product #5 to my cart"
  │
  ├─ LLM knows product_id from previous context, quantity=2
  │
  ├─ Calls: add_to_cart_tool(session_id="abc123", product_id=5, quantity=2)
  │      └─ DB: GET or CREATE Cart → UPSERT CartItem (quantity += 2)
  │      └─ Returns: { success: true, message: "Added 2x ... to your cart" }
  │
  └─ Response:
       message: "Done! Added 2 Scarlet Evening Gown to your cart."
       action: [{ type: "cart_refresh" }]   ← frontend re-fetches cart count
       suggestions: ["View my cart", "Continue shopping", "Checkout"]
```

> **Note:** No page navigation is needed. The cart mutation happens directly via the tool. `cart_refresh` tells the frontend's cart badge to update.

### 3.3 Checkout Flow (Conversational)

The agent collects address details one field at a time without any form navigation:

```
Step 1 — Cart summary
  Agent: "Let me check your cart..."
  → cart_summary_tool(session_id) → shows items and total

Step 2 — Address selection
  → get_saved_addresses_tool(session_id)
  If found: "I have your saved address in Mumbai. Use this one?"
  If none:  "I'll need your shipping details. What's the recipient's name?"

Step 3 — Conversational address collection (only if no saved address)
  Agent asks → User replies, one field per turn:
  Name → Phone → Street → City → State → Pincode
  → save_address_tool(session_id, name, phone, ...) → returns address_id

Step 4 — Order confirmation  ← ONLY step requiring UI confirmation
  Response:
    message: "Order summary: 2x Scarlet Gown ($89.99 each), Total: $179.98.
              Ship to: Jane, 42 Rose St, Mumbai 400001. Confirm?"
    confirmation_required: true   ← frontend shows ConfirmBanner

Step 5 — Order placement (after user taps "Yes, confirm")
  User: "Yes, confirm"
  → place_order_tool(session_id, address_id)
       └─ DB: Validate stock → CREATE Order → CREATE OrderItems
              → Deduct stock → DELETE CartItems
  → Response:
       message: "Order #42 placed! Estimated delivery: 5-7 business days."
       action: [{ type: "navigate", target: "/orders" }]
```

### 3.4 Order Tracking Flow

**Trigger:** "Where is my order?" / "Show my orders"

```
User: "What's the status of my order?"
  │
  ├─ Calls: order_status_tool(session_id)
  │      └─ DB: SELECT orders WHERE session_id = ? ORDER BY created_at DESC LIMIT 1
  │      └─ Returns: order_id, status, total, items, shipping_address
  │
  └─ Response:
       message: "Order #42 (Pending) — 2x Scarlet Evening Gown, $179.98.
                 Shipping to Mumbai. Estimated delivery: 5-7 days."
       suggestions: ["View all orders", "Continue shopping"]
```

### 3.5 FAQ / Policy Flow

**Trigger:** "What's your return policy?"

```
User: "How do I return an item?"
  │
  ├─ Calls: faq_tool(question="How do I return an item?")
  │      └─ Keyword match: "return" → static answer string
  │
  └─ Response:
       message: "We accept returns within 30 days of delivery.
                 Items must be unused with original tags.
                 Refund processed within 7-10 business days..."
```

### 3.6 Voice Mode Flow

Voice mode uses the exact same backend — only the frontend changes:

```
User taps mic button
  │
  ├─ Browser webkitSpeechRecognition starts
  ├─ User speaks: "Show me red dresses"
  ├─ Auto-stop on silence → transcript captured
  │
  ├─ sendMessage(transcript, mode="voice")
  │      ← same POST /chat/agent but mode="voice"
  │
  ├─ Backend response:
  │    speak: true
  │    message: "Here are some beautiful red dresses..."
  │    html_content: ""   ← skipped in voice mode
  │
  └─ Frontend: speakMessage(response.message)
        └─ window.speechSynthesis.speak() — sentence by sentence
```

Voice interruption: If the user taps the microphone while the agent is speaking, `stopSpeaking()` cancels TTS immediately and STT starts fresh.

### 3.7 Review Submission Flow

**Trigger:** "I want to review the dress I bought"

```
User: "I'd like to rate the Scarlet Gown 5 stars"
  │
  ├─ LLM knows product_id from context or asks for it
  ├─ Calls: submit_review_tool(session_id, product_id=5, rating=5, comment="Loved it!")
  │      └─ DB: Verify user has ordered this product
  │           → UPSERT Review (unique per product+session)
  │
  └─ Response:
       message: "Thank you for your review! Your 5-star rating has been saved."
```

---

## 4 — Developer Reference

### 4.1 Complete Tools Catalog

| Tool Function | Type | Description | Key Args |
|---|---|---|---|
| `search_products_tool` | Read | Full-text + price + color product search | `keyword`, `min_price`, `max_price`, `color` |
| `get_product_details_tool` | Read | Full product info + reviews | `product_id` or `product_name` |
| `check_stock_tool` | Read | Stock status + low-stock warnings | `product_id` |
| `cart_summary_tool` | Read | Current cart items + total | `session_id` |
| `order_status_tool` | Read | Latest or specific order status | `session_id`, `order_id?` |
| `list_orders_tool` | Read | All orders for session | `session_id` |
| `faq_tool` | Read | Static keyword-matched store policies | `question` |
| `add_to_cart_tool` | **Action** | Add item to cart (DB write, stock-validated) | `session_id`, `product_id`, `quantity` |
| `update_cart_item_tool` | **Action** | Update quantity (0 = remove) | `session_id`, `product_id`, `quantity` |
| `remove_from_cart_tool` | **Action** | Remove item (alias for update qty=0) | `session_id`, `product_id` |
| `save_address_tool` | **Action** | Persist shipping address to DB | `session_id`, `name`, `phone`, `address`, `city`, `state`, `pincode` |
| `get_saved_addresses_tool` | Read | List all saved addresses | `session_id` |
| `place_order_tool` | **Action** | Create order + deduct stock + clear cart | `session_id`, `address_id` |
| `submit_review_tool` | **Action** | Post/update product review (purchase-gated) | `session_id`, `product_id`, `rating`, `comment?` |

All Read tools return `str` (JSON or plain string). All Action tools return `str` (JSON with `success: bool`).

### 4.2 Adding a New Tool

1. Write a plain Python function in [`backend/app/agents/tools.py`](file:///C:/folder-e/workspace/e-commerce/backend/app/agents/tools.py) with a descriptive docstring (the LLM sees this as the tool description):
   ```python
   def apply_discount_tool(session_id: str, coupon_code: str) -> str:
       """
       Apply a coupon code to the user's cart.
       Args:
           session_id: The user's session ID
           coupon_code: The coupon code to apply
       """
       # ... DB logic ...
       return json.dumps({"success": True, "discount": "$10.00"})
   ```

2. Import it in [`backend/app/agents/service.py`](file:///C:/folder-e/workspace/e-commerce/backend/app/agents/service.py) and add to the `tools` list:
   ```python
   from app.agents.tools import apply_discount_tool
   
   tools = [
       # existing tools...
       FunctionTool(apply_discount_tool),
   ]
   ```

3. Update the system prompt (`SYSTEM_PROMPT`) to describe when the agent should use it.

4. The tool will automatically appear in `{tool_descriptions}` injected by `PromptBuilder`.

### 4.3 API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat/agent` | **Primary agent endpoint** — synchronous JSON response |
| `POST` | `/chat/agent-stream` | Streaming SSE agent response |
| `GET` | `/chat/session/{session_id}/history` | Retrieve conversation history for a session |
| `DELETE` | `/chat/session/{session_id}` | Clear session memory |
| `GET` | `/products` | List all products |
| `GET` | `/products/{id}` | Product detail |
| `GET` | `/cart/{session_id}` | Cart contents |
| `POST` | `/cart` | Add to cart (REST fallback) |
| `GET` | `/orders/{session_id}` | Order list |
| `POST` | `/orders` | Place order (REST fallback) |
| `POST` | `/reviews` | Submit review (REST fallback) |
| `GET` | `/health` | Health check |

### 4.4 Request / Response Contract

**Request (POST /chat/agent):**
```json
{
  "message": "Show me red dresses under $100",
  "session_id": "user_abc123",
  "route": "/",
  "page_type": "home",
  "mode": "text"
}
```

**Response (ECommerceResponse):**
```json
{
  "message": "Here are some beautiful red dresses under $100!",
  "html_content": "<div class=\"bg-white p-3 ...\">...</div>",
  "action": [],
  "suggestions": ["Add to cart", "Filter by size", "See more"],
  "confirmation_required": false,
  "speak": false
}
```

**Action shapes:**
```json
{ "type": "navigate",     "target": "/product/5" }
{ "type": "cart_refresh", "target": null }
{ "type": "none",         "target": null }
```

### 4.5 Environment Variables

```env
# Backend ─ backend/.env

DATABASE_URL=postgresql://user:password@localhost:5432/dress_ecommerce

# LLM Providers (configure the one you use)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL_NAME=gemini-3-pro-preview

GROQ_API_KEY=gsk_...
MODEL_NAME=openai/gpt-oss-120b

CEREBRAS_API_KEY=...
CEREBRAS_MODE_NAME=gpt-oss-120b

FIREWORKS_API_KEY=...
FIREWORKS_MODE_NAME=accounts/fireworks/models/llama-v3p3-70b-instruct

# Agent tuning
MAX_ITERATIONS=10
TEMPERATURE=0.1
```

### 4.6 Session & Memory Model

- Sessions are identified by a `session_id` (a random UUID-like string generated client-side and stored in `localStorage`).
- `MemorySaver` (LangGraph in-memory checkpointer) stores the full `AgentState.messages` list keyed by `session_id` as `thread_id`.
- **Persistence scope:** In-process only. Sessions are lost on server restart. For production, replace `MemorySaver` with `PostgresSaver` or `RedisSaver`.
- **History retrieval:** `GET /chat/session/{session_id}/history` reads from the checkpointer and strips internal `(SYSTEM)` prefixes before returning clean history to the frontend.

### 4.7 Frontend Integration

To embed the copilot in any React app:

```jsx
import { CopilotProvider } from './components/agentCopilot/CopilotContext';
import CopilotWidget from './components/agentCopilot/CopilotWidget';

<CopilotProvider
  apiConfig={{
    endpoint: 'http://localhost:8000/chat/agent',
    headers: {}
  }}
  onCartRefresh={() => refetchCart()}
>
  <YourApp />
  <CopilotWidget />
</CopilotProvider>
```

**`apiConfig` props:**

| Prop | Type | Description |
|---|---|---|
| `endpoint` | `string` | Full URL to `/chat/agent` |
| `headers` | `object` | Optional auth headers |

**`onCartRefresh`**: A callback fired whenever the agent returns a `cart_refresh` action. Connect this to your CartContext's refetch function.

---

## 5 — Deployment & Ops

### 5.1 Local Development Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd e-commerce

# 2. Set up the backend virtual environment
cd backend
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
pip install -e ./../ai_agent_core  # editable install of the agent library

# 3. Configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL and at least one LLM API key

# 4. Apply database migrations
alembic upgrade head

# 5. (Optional) Seed sample data
python seed_data.py

# 6. Start the FastAPI server
uvicorn app.main:app --reload --port 8000

# 7. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev       # starts on http://localhost:5173 (or similar)
```

### 5.2 Directory Structure

```
e-commerce/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── service.py          ← agent initialisation + service entry points
│   │   │   ├── tools.py            ← all 14 tool functions
│   │   │   └── page_context.py     ← route-aware DB context enricher
│   │   ├── routes/
│   │   │   ├── chat.py             ← /chat/agent endpoint
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   └── ...
│   │   ├── models.py               ← SQLAlchemy ORM models
│   │   ├── db.py                   ← DB engine + session factory
│   │   └── main.py                 ← FastAPI app + router registration
│   ├── alembic/                    ← DB migrations
│   ├── config.py                   ← pydantic-settings config
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   └── src/
│       └── components/
│           └── agentCopilot/
│               ├── CopilotWidget.jsx
│               ├── CopilotContext.jsx
│               └── useCopilot.js
│
└── ai_agent_core/                  ← shared agent library (editable install)
    └── ai_agent_core/
        ├── agent_core.py           ← public API (AgentCore class)
        ├── agent/runner.py         ← LangGraph StateGraph execution
        ├── llm/llm_manager.py      ← multi-provider LLM factory
        ├── tools/
        │   ├── base_tool.py        ← BaseTool + FunctionTool
        │   ├── tool_registry.py    ← in-memory tool registry
        │   └── tool_executor.py    ← async tool dispatch
        ├── prompts/prompt_builder.py
        └── schema/response_schema.py
```

### 5.3 Production Checklist

| Item | Action Required |
|---|---|
| **Session persistence** | Replace `MemorySaver` with `langgraph.checkpoint.postgres.PostgresSaver` or a Redis-backed saver |
| **CORS** | In `main.py`, change `allow_origins=["*"]` to exact frontend origin(s) |
| **LLM API keys** | Store in a secrets manager (AWS Secrets Manager, GCP Secret Manager) — not in `.env` files |
| **Database** | Use a managed PostgreSQL service (RDS, Cloud SQL); enable SSL |
| **Rate limiting** | Add per-session rate limiting on `/chat/agent` to prevent LLM cost abuse |
| **Logging** | The `ai_agent_core` library uses Python's standard `logging` module. Configure a structured log handler (e.g. JSON to CloudWatch / Datadog) |
| **Error monitoring** | Integrate Sentry or similar for exception tracking |
| **Recursion limit** | Tune `max_iterations` in `AgentCore(max_iterations=...)` based on observed tool call depth |
| **Model swap** | The active LLM is in `service.py` → `llm_config`. No other code changes needed to switch providers |

### 5.4 Switching the LLM Provider

Edit the `agent` initialisation block in [`backend/app/agents/service.py`](file:///C:/folder-e/workspace/e-commerce/backend/app/agents/service.py):

```python
# Switch to Groq
llm_config = {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "api_key": settings.GROQ_API_KEY
}

# Switch to Cerebras (fastest inference)
llm_config = {
    "provider": "cerebras",
    "model": "llama3.1-8b",
    "api_key": settings.CEREBRAS_API_KEY
}

# Switch to local Ollama
llm_config = {
    "provider": "local",
    "model": "llama3.1:8b",
    "base_url": "http://localhost:11434"
}
```

> [!IMPORTANT]
> The `ai_agent_core` library is installed in **editable mode** (`pip install -e ./../ai_agent_core`). Changes to the library source take effect immediately without reinstalling.

### 5.5 Monitoring & Observability

**Key log lines to watch:**

| Log message | Meaning |
|---|---|
| `run_agent called. session_id: X, history_len: N` | New agent invocation |
| `Invoking LangGraph (Checkpoint mode)` | Agent graph starting |
| `Executing tool 'X' with input: {...}` | Tool is running |
| `Tool 'X' executed successfully` | Tool returned data |
| `Validation failed on attempt N` | LLM response didn't match schema — will retry |
| `LangGraph execution error: Recursion limit...` | Agent exceeded `max_iterations` — increase limit or simplify prompt |
| `LangGraph execution error: No synchronous function...` | **Fixed** — this was the bug where async nodes were invoked synchronously |

**Key metrics to track:**

| Metric | Target |
|---|---|
| p95 latency `/chat/agent` | < 5s for simple queries, < 12s for multi-tool flows |
| Tool call count per request | ≤ 3 for typical flows; > 5 suggests prompt or tool description issue |
| Schema validation retry rate | < 5%; high rate indicates system prompt needs tightening |
| `confirmation_required=true` rate | Should be ≈ 100% for order placements |

### 5.6 Known Limitations & Roadmap

| Limitation | Current state | Recommended fix |
|---|---|---|
| **Session memory is in-process** | `MemorySaver` resets on restart | Swap to `PostgresSaver` |
| **No authentication** | `session_id` is client-generated; any caller can use any session | Add JWT or cookie-based auth |
| **Single currency** | All prices in USD (`$`) | Add currency field to Product model |
| **FAQ is static** | Hard-coded keyword dict in `faq_tool` | Replace with vector search over a knowledge base (ChromaDB already in requirements) |
| **No image search** | Search is text-only | Add embedding-based visual search |
| **No pagination in search** | Returns max 10 results | Add `offset` / `page` parameter to `search_products_tool` |

---

*Document generated from direct source code analysis. Last updated: May 2026.*
