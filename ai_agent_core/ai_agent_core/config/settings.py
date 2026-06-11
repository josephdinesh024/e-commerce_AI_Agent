"""
Settings module for the ai_agent_core package.
Provides default configurable values.
"""

from typing import Dict, Any

DEFAULT_LLM_CONFIG: Dict[str, Any] = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.0
}

# Default memory time-to-live in seconds (1 hour)
DEFAULT_MEMORY_TTL: int = 3600

# Default log level
LOG_LEVEL: str = "INFO"

DEFAULT_PROMPT_TEMPLATE: str = """You are a helpful AI assistant.
Answer the user's queries to the best of your ability.

IMPORTANT: Only use a tool when the user's question specifically requires it.
For greetings, general questions, or anything not related to tools, respond directly without calling any tool.

You have access to the following tools:
{tool_descriptions}
"""
