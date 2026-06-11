"""
Prompt Builder responsible for constructing prompts sent to the LLM.
"""

import json
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel
from ai_agent_core.config.settings import DEFAULT_PROMPT_TEMPLATE
from ai_agent_core.tools.tool_registry import ToolRegistry

from ai_agent_core.utils.logger import setup_logger

logger = setup_logger(__name__)

class PromptBuilder:
    """
    Assembles prompts that include system instructions, conversation history,
    user messages, and available tool descriptions.
    """
    def __init__(self, template: Optional[str] = None):
        """
        Initializes the PromptBuilder.
        If no template is provided, the DEFAULT_PROMPT_TEMPLATE from settings is used.
        """
        self.template = template or DEFAULT_PROMPT_TEMPLATE

    def _format_tools(self) -> str:
        """Formats the list of registered tools into a string."""
        tools = ToolRegistry.get_all()
        if not tools:
            return "No tools available."
        
        descriptions = []
        for tool in tools:
            descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(descriptions)

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Formats the conversation history."""
        if not history:
            return "No previous conversation history."
        
        lines = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role.capitalize()}: {content}")
        return "\n".join(lines)

    def _format_schema(self, schema_class: Type[BaseModel]) -> str:
        """Converts a Pydantic model into a simplified JSON schema string for the LLM."""
        schema_json = schema_class.model_json_schema()
        defs = schema_json.get("$defs", {})
        
        def resolve_schema(props: Dict[str, Any]) -> Dict[str, Any]:
            simple = {}
            for prop_name, prop_info in props.items():
                # Handle nested array items
                if prop_info.get("type") == "array" and "items" in prop_info:
                    items = prop_info["items"]
                    if "$ref" in items:
                        ref_name = items["$ref"].split("/")[-1]
                        if ref_name in defs:
                            nested_props = defs[ref_name].get("properties", {})
                            simple[prop_name] = [resolve_schema(nested_props)]
                            continue
                
                # Handle direct nested objects
                if "$ref" in prop_info:
                    ref_name = prop_info["$ref"].split("/")[-1]
                    if ref_name in defs:
                        nested_props = defs[ref_name].get("properties", {})
                        simple[prop_name] = resolve_schema(nested_props)
                        continue

                field_type = prop_info.get("type", "any")
                description = prop_info.get("description", "")
                if description:
                    simple[prop_name] = f"{field_type} — {description}"
                else:
                    simple[prop_name] = field_type
            return simple

        simple_schema = resolve_schema(schema_json.get("properties", {}))
        return json.dumps(simple_schema, indent=2)

    def _build_response_instructions(self, response_schema: Optional[Type[BaseModel]] = None, escape_for_langchain: bool = False) -> str:
        """
        Builds the response format instructions for the LLM.
        Only includes the final response schema — tool calling is handled natively by LangChain.
        """
        instructions = ""
        if response_schema:
            response_schema_str = self._format_schema(response_schema)
            if escape_for_langchain:
                # LangChain templates interpret { and } as variables.
                # We must double them for the JSON format block to render correctly.
                response_schema_str = response_schema_str.replace("{", "{{").replace("}", "}}")
                
            instructions += (
                "\n\n### FINAL RESPONSE FORMAT\n"
                "**IMPORTANT:** Use your NATIVE tool-calling capability for intermediate steps. "
                "Do NOT use JSON format when calling tools.\n"
                "NEVER output more than one JSON object in a single message.\n\n"
                "ONLY when you have the final answer, respond in this EXACT JSON format:\n"
                + response_schema_str + "\n\n"
                "**STRICT RULES FOR JSON FIELDS:**\n"
                "- 'metrics': MUST be an ARRAY of objects (e.g. [{\"label\": \"Title\", \"value\": 10}]). NEVER use a single object.\n"
                "- 'insights', 'actions', 'follow_up_questions': MUST be ARRAYS of strings or objects as specified. NEVER use a single object.\n"
                "- The 'message' field should contain your natural language response."
            )
        return instructions

    def build_chat_prompt(self, response_schema: Optional[Type[BaseModel]] = None):
        """
        Builds a LangChain ChatPromptTemplate for use with create_tool_calling_agent.
        Includes MessagesPlaceholder('agent_scratchpad') for tool observations.
        """
        logger.info(f"Building chat prompt with response_schema: {response_schema.__name__ if response_schema else 'None'}")
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        # Build the system message from the user's dynamic template
        tool_descriptions = self._format_tools()
        
        # Replace {tool_descriptions} in the template (escaped for LangChain)
        safe_tools = tool_descriptions.replace("{", "{{").replace("}", "}}")
        system_message = self.template.replace("{tool_descriptions}", safe_tools)
        
        # Clean up any leftover legacy placeholders (backward compatibility)
        system_message = system_message.replace("{history}", "")
        system_message = system_message.replace("{user_message}", "")
        
        # Append response schema instructions
        system_message += self._build_response_instructions(response_schema, escape_for_langchain=True)

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def build(self, user_message: str, history: List[Dict[str, Any]] = None, response_schema: Optional[Type[BaseModel]] = None) -> str:
        """
        Constructs the final prompt string (legacy method for non-agent use).
        """
        logger.info(f"Building legacy prompt for user_message: {user_message[:50]}...")
        history = history or []
        tool_descriptions = self._format_tools()
        formatted_history = self._format_history(history)
        
        prompt = self.template.format(
            tool_descriptions=tool_descriptions,
            history=formatted_history,
            user_message=user_message
        )
        
        prompt += self._build_response_instructions(response_schema)
            
        return prompt

    # Alias for backward compatibility
    build_prompt = build

