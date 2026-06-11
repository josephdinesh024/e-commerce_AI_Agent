from typing import List, Optional, Dict, Any, Type, Union
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from ai_agent_core.tools.base_tool import BaseTool
from ai_agent_core.tools.tool_registry import ToolRegistry
from ai_agent_core.llm.llm_manager import LLMManager
from ai_agent_core.prompts.prompt_builder import PromptBuilder
from ai_agent_core.agent.runner import AgentRunner
from ai_agent_core.utils.logger import setup_logger

logger = setup_logger(__name__)

class AgentCore:
    """
    Main interface for the AI Agent system using LangGraph.
    Provides dual-mode memory: Checkpoint (Stateful) and List (Stateless).
    """
    def __init__(
        self,
        tools: Optional[List[BaseTool]] = None,
        llm_name: str = "default",
        llm_config: Optional[Dict[str, Any]] = None,
        prompt_template: Optional[str] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        max_iterations: int = 5
    ):
        """
        Initializes the agent Core with optional checkpointer for stateful memory.
        """
        # 1. Register tools
        ToolRegistry.clear()
        if tools:
            logger.info(f"Registering {len(tools)} tools")
            for tool in tools:
                ToolRegistry.register(tool)
                 
        # 2. Setup LLM
        self.llm = LLMManager.get_llm(name=llm_name, config=llm_config)

        # 3. Construct Prompt Builder
        self.prompt_builder = PromptBuilder(template=prompt_template)
        self.response_schema = response_schema
        self.checkpointer = checkpointer
        
        # 4. Convert tools
        langchain_tools = [tool.to_langchain_tool() for tool in ToolRegistry.get_all()]

        # 5. Initialize Runner (LangGraph based)
        logger.info(f"Initializing LangGraph AgentRunner. Mode: {'Stateful' if checkpointer else 'Stateless'}")
        self.runner = AgentRunner(
            llm=self.llm,
            prompt_builder=self.prompt_builder,
            langchain_tools=langchain_tools,
            response_schema=self.response_schema,
            checkpointer=self.checkpointer,
            max_iterations=max_iterations
        )

    async def astream_agent(
        self, 
        message: str, 
        session_id: Optional[str] = None, 
        history_list: Optional[List[Union[Dict[str, Any], BaseMessage]]] = None
    ):
        """
        Asynchronous generator for agent events (streaming).
        Yields: {"type": "progress|classified|executed|complete", "data": ...}
        """
        logger.info(f"astream_agent called. session_id: {session_id}")
        
        # Validation & Routing (Same as run_agent)
        if self.checkpointer:
            if not session_id:
                raise ValueError("session_id is required when a checkpointer is initialized (Checkpoint Mode).")
            langchain_history = []
        else:
            if history_list is None:
                 raise ValueError("history_list is required when no checkpointer is provided (List Mode).")
            langchain_history = self._parse_history(history_list)

        # Stream
        async for event in self.runner.astream(
            message=message, 
            history=langchain_history, 
            session_id=session_id
        ):
            yield event

    async def run_agent(
        self, 
        message: str, 
        session_id: Optional[str] = None, 
        history_list: Optional[List[Union[Dict[str, Any], BaseMessage]]] = None
    ) -> Dict[str, Any]:
        """
        Primary execution method supporting two memory modes.
        
        Mode 1 (Checkpoint): Pass session_id. LangGraph handles persistence.
        Mode 2 (List): Pass history_list. core processes it statelessly.
        """
        logger.info(f"run_agent called. session_id: {session_id}, history_len: {len(history_list) if history_list else 0}")
        
        # Validation & Routing
        if self.checkpointer:
            if not session_id:
                raise ValueError("session_id is required when a checkpointer is initialized (Checkpoint Mode).")
            # In Checkpoint Mode, we don't manually load history from here; LangGraph does it via thread_id.
            langchain_history = []
        else:
            if history_list is None:
                 raise ValueError("history_list is required when no checkpointer is provided (List Mode).")
            # Convert history_list to LangChain messages
            langchain_history = self._parse_history(history_list)

        # Execute
        agent_response = await self.runner.run(
            message=message, 
            history=langchain_history, 
            session_id=session_id
        )
        
        # Return structured output
        if hasattr(agent_response, "model_dump"):
            return agent_response.model_dump()
        return {"message": str(agent_response)}

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the chat history for a session from the checkpointer.
        Returns a list of dicts: [{'role': 'user'|'agent', 'content': '...', 'html_content': '...', 'action': ...}]
        """
        if not self.checkpointer:
            raise ValueError("No checkpointer available to retrieve history.")
            
        config = {"configurable": {"thread_id": session_id}}
        state = self.runner.app.get_state(config)
        
        messages = state.values.get("messages", [])
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                # Filter out tool calls for clean history retrieval if requested/needed
                if not msg.tool_calls:
                    import json
                    try:
                        content = msg.content
                        if isinstance(content, list):
                            text_parts = [part["text"] if isinstance(part, dict) and "text" in part else str(part) for part in content]
                            content_str = " ".join(text_parts)
                        else:
                            content_str = str(content)
                            
                        # Extract JSON object from potential markdown wrapping
                        start = content_str.find("{")
                        end = content_str.rfind("}")
                        
                        if start != -1 and end != -1:
                            json_str = content_str[start:end + 1]
                            parsed = json.loads(json_str)
                            history.append({
                                "role": "agent",
                                "content": parsed.get("message", content_str),
                                "html_content": parsed.get("html_content", ""),
                                "action": parsed.get("action", [])
                            })
                        else:
                            history.append({"role": "agent", "content": content_str})
                    except Exception:
                        history.append({"role": "agent", "content": str(msg.content)})
        return history

    def _parse_history(self, history_list: List[Union[Dict[str, Any], BaseMessage]]) -> List[BaseMessage]:
        """Converts raw history list into LangChain BaseMessages."""
        messages = []
        for msg in history_list:
            if isinstance(msg, BaseMessage):
                messages.append(msg)
                continue
            
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        return messages

    # Backward compatibility wrap
    async def run(self, session_id: str, message: str) -> Dict[str, Any]:
        """Legacy run method. Defaults to Checkpoint mode if session_id is provided."""
        return await self.run_agent(message=message, session_id=session_id)
