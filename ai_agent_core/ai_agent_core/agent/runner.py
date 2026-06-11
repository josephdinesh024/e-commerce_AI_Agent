from typing import List, Dict, Any, Type, Optional, Annotated, Union, TypedDict
import operator
import json
from pydantic import BaseModel, ValidationError
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from ai_agent_core.prompts.prompt_builder import PromptBuilder
from ai_agent_core.schema.response_schema import AgentResponse
from ai_agent_core.utils.logger import setup_logger
from ai_agent_core.tools.tool_executor import ToolExecutor

logger = setup_logger(__name__)

class AgentState(TypedDict):
    """The state of the agent, tracking messages and iteration count."""
    messages: Annotated[List[BaseMessage], operator.add]

class AgentRunner:
    """
    The core driver of the agent using LangGraph.
    Supports both stateful (checkpoint) and stateless (list) execution.
    """
    def __init__(
        self, 
        llm: Any, 
        prompt_builder: PromptBuilder, 
        langchain_tools: List = None,
        max_iterations: int = 5, 
        response_schema: Optional[Type[BaseModel]] = None,
        checkpointer: Optional[BaseCheckpointSaver] = None
    ):
        self.llm = llm
        self.prompt_builder = prompt_builder
        self.max_iterations = max_iterations
        self.response_schema = response_schema
        self.langchain_tools = langchain_tools or []
        self.checkpointer = checkpointer

        # Bind tools to the LLM
        tools_to_bind = list(self.langchain_tools) if self.langchain_tools else []
        if self.response_schema:
            # Bind the schema so Groq Tool Calling doesn't fail if the model tries to call it
            tools_to_bind.append(self.response_schema)
            
        if tools_to_bind and hasattr(self.llm, "bind_tools"):
            self.llm_with_tools = self.llm.bind_tools(tools_to_bind)
        else:
            logger.warning(f"LLM {type(self.llm).__name__} does not support bind_tools or no tools to bind.")
            self.llm_with_tools = self.llm

        # Build the graph
        self.app = self._build_graph()

    def _build_graph(self):
        """Constructs the LangGraph StateGraph."""
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self._call_model)
        workflow.add_node("execute_tools", self._call_tools)
        
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "execute_tools",
                "end": END
            }
        )
        workflow.add_edge("execute_tools", "agent")

        return workflow.compile(checkpointer=self.checkpointer)

    async def _call_model(self, state: AgentState):
        """Invokes the LLM with the current message state."""
        messages = state['messages']
        
        # Build chat prompt to get the system template
        chat_prompt = self.prompt_builder.build_chat_prompt(response_schema=self.response_schema)
        system_content = chat_prompt.messages[0].prompt.template
        
        # Ensure we don't duplicate system messages in the history
        has_system = any(isinstance(m, SystemMessage) for m in messages)
        system_msg = SystemMessage(content=system_content) if not has_system else messages[0]
        other_msgs = messages if not has_system else messages[1:]
            
        # Truncate history to avoid context length limits (e.g. Cerebras max 8192 tokens)
        # Safely keep only the last 5 HumanMessage turns, plus subsequent AI/Tool messages
        MAX_TURNS = 5
        human_indices = [i for i, m in enumerate(other_msgs) if isinstance(m, HumanMessage)]
        if len(human_indices) > MAX_TURNS:
            cutoff_idx = human_indices[-MAX_TURNS]
            truncated_msgs = other_msgs[cutoff_idx:]
        else:
            truncated_msgs = other_msgs
            
        # --- Sanitize history to prevent provider strict-validation errors (e.g. Gemini thought_signature) ---
        sanitized_msgs = []
        for msg in truncated_msgs:
            if isinstance(msg, AIMessage) and getattr(msg, 'tool_calls', None):
                text_content = msg.content if isinstance(msg.content, str) else str(msg.content or "")
                calls_text = "\n".join([f"Action: Called tool '{tc['name']}' with args: {tc.get('args', {})}" for tc in msg.tool_calls])
                content = f"{text_content}\n\n{calls_text}".strip()
                sanitized_msgs.append(AIMessage(content=content))
            elif isinstance(msg, ToolMessage):
                sanitized_msgs.append(HumanMessage(content=f"System: Tool Response for '{msg.name or msg.tool_call_id}':\n{msg.content}"))
            else:
                sanitized_msgs.append(msg)
                
        full_messages = [system_msg] + sanitized_msgs
        
        logger.debug(f"Calling LLM with {len(full_messages)} messages. (Truncated from {len(messages)})")
        response = await self.llm_with_tools.ainvoke(full_messages)
        
        # Fallback: Check if the model returned a JSON tool call in text content 
        # instead of native tool_calls attribute (common in some 8B models)
        if hasattr(response, 'content') and not response.tool_calls:
            try:
                raw_content = response.content
                if isinstance(raw_content, list):
                    text_parts = []
                    for part in raw_content:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                    content = " ".join(text_parts).strip()
                else:
                    content = str(raw_content).strip()
                import re
                
                tool_calls_detected = []
                decoder = json.JSONDecoder()
                idx = 0
                
                while idx < len(content):
                    match = re.search(r'\{', content[idx:])
                    if not match:
                        break
                    
                    try:
                        obj, curr_idx = decoder.raw_decode(content[idx + match.start():])
                        
                        # 1. Detect Native-like JSON Tool Call (name/arguments)
                        tool_name = obj.get("name")
                        if tool_name and ("arguments" in obj or "parameters" in obj or "product_id" in obj):
                            args = obj.get("arguments", obj.get("parameters", obj))
                            if isinstance(args, dict) and "name" in args: args.pop("name")
                            
                            logger.info(f"Detected text-encoded native tool call: {tool_name}")
                            tool_calls_detected.append({
                                "name": tool_name,
                                "args": args if isinstance(args, dict) else {"input": args},
                                "id": f"call_{tool_name}_{len(messages)}_{len(tool_calls_detected)}"
                            })
                        
                        # 2. Detect Legacy Pattern (action/input)
                        elif obj.get("action") and isinstance(obj["action"], str) and not obj.get("final", False):
                            action_name = obj["action"]
                            ui_actions = {"navigate", "add_to_cart", "click", "speak"}
                            if action_name not in ui_actions:
                                logger.info(f"Detected legacy action pattern tool call: {action_name}")
                                tool_calls_detected.append({
                                    "name": action_name,
                                    "args": obj.get("input", {}),
                                    "id": f"call_{action_name}_{len(messages)}_{len(tool_calls_detected)}"
                                })
                        
                        idx += match.start() + curr_idx
                    except json.JSONDecodeError:
                        idx += match.start() + 1
                        
                if tool_calls_detected:
                    response.tool_calls = tool_calls_detected
            except Exception as e:
                logger.debug(f"Fallback detector skipped: {e}")

        return {"messages": [response]}

    async def _call_tools(self, state: AgentState):
        """Executes tools requested by the AI using ToolExecutor."""
        last_message = state['messages'][-1]
        tool_messages = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Execute via ToolExecutor for consistent logging and error handling
            result = await ToolExecutor.aexecute(tool_name, tool_args)
            
            tool_messages.append(ToolMessage(
                tool_call_id=tool_call["id"],
                content=str(result)
            ))
            
        return {"messages": tool_messages}

    def _should_continue(self, state: AgentState):
        """Determines if the agent should call a tool or finish."""
        messages = state['messages']
        last_message = messages[-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            # Check if it called the response schema as a tool
            if self.response_schema:
                schema_name = self.response_schema.__name__.lower()
                for tc in last_message.tool_calls:
                    name = tc.get("name", "").lower()
                    if name == schema_name or name == f"{schema_name}_schema" or name == "agent_response":
                        # If it's the schema tool, we are done!
                        # We don't execute it, we just return "end"
                        return "end"
            return "continue"
        return "end"

    async def astream(self, message: str, history: List[BaseMessage], session_id: Optional[str] = None):
        """
        Asynchronously streams agent events using LangGraph astream_events.
        Yields: {"type": "progress|classified|executed|complete", "data": ...}
        """
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": self.max_iterations
        }
        input_messages = history + [HumanMessage(content=message)]
        
        logger.info(f"Streaming LangGraph ({'Checkpoint' if session_id else 'List'} mode)")
        last_message = None
        buffer = ""
        is_buffering_json = False

        async for event in self.app.astream_events({"messages": input_messages}, config=config, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node", "")
            
            # Track final message for stateless mode
            if kind == "on_chat_model_end":
                last_message = event.get("data", {}).get("output")
                
                # If no tool calls were detected, yield any buffered JSON artifacts
                if not (last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls):
                    if buffer:
                        yield {"type": "chunk", "data": buffer}
                
                # Reset buffer for next potential sequence
                buffer = ""
                is_buffering_json = False

            # 1. Progress: Model starts thinking
            if kind == "on_chat_model_start":
                yield {"type": "progress", "data": "Thinking..."}
            
            # 2. Executed: Tool starts execution
            elif kind == "on_tool_start":
                yield {
                    "type": "executed", 
                    "data": f"Gathering info from {event['name']}...",
                    "tool": event['name'],
                    "inputs": event['data'].get('input')
                }
            
            # 3. Classified: Node transition
            elif kind == "on_chain_end" and node == "agent":
                # This signifies the agent node finished its turn
                yield {"type": "classified", "data": "Determining next steps..."}

            # 4. Chunk: Token streaming from model (Optimized to filter tool-calls and metadata)
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    content = chunk.content
                    
                    # More aggressive filtering:
                    # Detect start of JSON or common metadata prefixes like "Action:" or "Thought:"
                    trimmed = content.strip()
                    if not is_buffering_json:
                        if trimmed.startswith('{') or trimmed.lower().startswith('action:') or trimmed.lower().startswith('thought:'):
                            is_buffering_json = True
                    
                    if is_buffering_json:
                        buffer += content
                        # If buffer looks like it finished a JSON object but then continues with text, 
                        # we might need to flush the text. But usually tool calls are at the end 
                        # or solitary. For now, keep it hidden during the turn.
                        continue
                        
                    yield {"type": "chunk", "data": content}

        # Final extraction of the state for the 'complete' event
        if self.checkpointer:
            final_state = self.app.get_state(config)
            messages = final_state.values.get("messages", [])
            last_msg_obj = messages[-1] if messages else None
        else:
            last_msg_obj = last_message

        final_msg = ""
        if last_msg_obj:
            if hasattr(last_msg_obj, 'tool_calls') and last_msg_obj.tool_calls:
                tc = last_msg_obj.tool_calls[-1] # Usually the last or only one
                tool_name = tc.get("name", "")
                schema_name = self.response_schema.__name__.lower() if self.response_schema else ""
                if tool_name.lower() in [schema_name, f"{schema_name}_schema", "agent_response"]:
                    final_msg = json.dumps(tc.get("args", {}))
            
            if not final_msg:
                final_msg = last_msg_obj.content if hasattr(last_msg_obj, 'content') else ""

        if final_msg:
            structured_resp = self._parse_output(final_msg)
            yield {"type": "complete", "data": structured_resp if isinstance(structured_resp, BaseModel) else structured_resp}

    async def run(self, message: str, history: List[BaseMessage], session_id: Optional[str] = None) -> Any:
        """
        Executes the agent graph.
        """
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": self.max_iterations
        }
        
        input_messages = history + [HumanMessage(content=message)]
        logger.info(f"Invoking LangGraph ({'Checkpoint' if session_id else 'List'} mode)")
        
        max_retries = 3
        current_messages = input_messages
        output_state = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Self-correction attempt {attempt}/{max_retries}")
                correction_msg = HumanMessage(content=f"Your previous response failed schema validation: {self._last_error}. Please try again.")
                if session_id:
                    current_messages = [correction_msg]
                else:
                    if output_state:
                        current_messages.append(output_state["messages"][-1])
                    current_messages.append(correction_msg)

            try:
                output_state = await self.app.ainvoke(
                    {"messages": current_messages},
                    config=config
                )
                last_msg_obj = output_state["messages"][-1]
                
                final_msg = ""
                if hasattr(last_msg_obj, 'tool_calls') and last_msg_obj.tool_calls:
                    tc = last_msg_obj.tool_calls[-1]
                    tool_name = tc.get("name", "")
                    schema_name = self.response_schema.__name__.lower() if self.response_schema else ""
                    if tool_name.lower() in [schema_name, f"{schema_name}_schema", "agent_response"]:
                        final_msg = json.dumps(tc.get("args", {}))
                
                if not final_msg:
                    final_msg = last_msg_obj.content if hasattr(last_msg_obj, "content") else ""
                
                if self.response_schema:
                    try:
                        return self._parse_output(final_msg, strict=True)
                    except (ValidationError, ValueError) as e:
                        self._last_error = str(e)
                        logger.warning(f"Validation failed on attempt {attempt}: {e}")
                        if attempt < max_retries:
                            continue
                        else:
                            return self._parse_output(final_msg, strict=False)
                else:
                    return self._parse_output(final_msg)
            except Exception as e:
                logger.error(f"LangGraph execution error: {e}")
                if "recursion_limit" in str(e).lower():
                    return AgentResponse(message="I'm sorry, I reached my iteration limit. Please try a simpler request.")
                raise e

    def _parse_output(self, output: Any, strict: bool = False) -> Any:
        """Parse the LLM output into the response schema."""
        if isinstance(output, list):
            text_parts = []
            for part in output:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
            output = " ".join(text_parts)
        elif not isinstance(output, str):
            output = str(output)

        if self.response_schema:
            try:
                # Try to find all JSON objects in the string
                import re
                decoder = json.JSONDecoder()
                idx = 0
                objects = []
                while idx < len(output):
                    match = re.search(r'\{', output[idx:])
                    if not match: break
                    try:
                        obj, curr_idx = decoder.raw_decode(output[idx + match.start():])
                        objects.append(obj)
                        idx += match.start() + curr_idx
                    except json.JSONDecodeError:
                        idx += match.start() + 1
                
                if not objects:
                    raise ValueError("No JSON found in output")

                # Try each object against the schema, prioritizing the last one or the one with most fields
                data = None
                for obj in reversed(objects):
                    if isinstance(obj, dict) and (obj.get("summary") or obj.get("intent")):
                        data = obj
                        break
                
                if not data:
                    data = objects[-1] if isinstance(objects[-1], dict) else {}

                # Adaptive type conversion for common schema fields
                for list_field in ["metrics", "insights", "actions", "follow_up_questions", "data_source"]:
                    if list_field in data and isinstance(data[list_field], dict):
                        # Convert {"key": "val"} -> [{"label": "key", "value": "val"}] or just list of values
                        val = data[list_field]
                        if list_field == "metrics":
                            data[list_field] = [{"label": k.replace("_", " ").title(), "value": v} for k, v in val.items()]
                        elif list_field == "insights":
                            data[list_field] = [str(v) for v in val.values()]
                        elif list_field == "actions":
                            # If it's {"recommendations": [...]}, flatten it
                            if "recommendations" in val and isinstance(val["recommendations"], list):
                                data[list_field] = [{"action": str(a), "priority": "medium"} for a in val["recommendations"]]
                            else:
                                data[list_field] = [{"action": str(v), "priority": "medium"} for v in val.values()]
                        elif list_field == "follow_up_questions":
                            if "questions" in val and isinstance(val["questions"], list):
                                data[list_field] = [str(q) for q in val["questions"]]
                            else:
                                data[list_field] = [str(v) for v in val.values()]
                        else:
                            data[list_field] = [str(v) for v in val.values()]

                return self.response_schema(**data)
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                if strict:
                    raise e
                logger.debug(f"JSON parsing/validation failed, falling back to adaptive mapping: {e}")

            if strict:
                 raise ValueError("No JSON found in output. Provide final answer in JSON format.")
            
            # Adaptive fallback mapping: Determine which fields the schema supports
            fields = getattr(self.response_schema, "model_fields", {})
            fallback_data = {}
            
            if "message" in fields:
                fallback_data["message"] = output
            elif "summary" in fields:
                fallback_data["summary"] = output
                
            if "intent" in fields and "intent" not in fallback_data:
                # Provide a safe default for literal types common in greetings
                fallback_data["intent"] = "general"
                
            try:
                return self.response_schema(**fallback_data)
            except ValidationError as ve:
                logger.warning(f"Adaptive fallback failed: {ve}. Returning raw text wrapped in core AgentResponse.")
                # If everything fails, we return the core AgentResponse to ensure the system doesn't crash
                return AgentResponse(message=output)
        
        return AgentResponse(message=output)
