from typing import Any
from ai_agent_core.utils.logger import setup_logger
from ai_agent_core.tools.tool_registry import ToolRegistry

logger = setup_logger(__name__)

class ToolExecutor:
    """
    Responsible for executing tools safely and catching execution errors.
    """
    @classmethod
    async def aexecute(cls, action_name: str, input_data: Any) -> Any:
        """
        Resolves the tool from the registry and executes it with the given input.
        """
        logger.info(f"Executing tool '{action_name}' with input: {input_data}")
        try:
            tool = ToolRegistry.get(action_name)
            result = await tool.run(input_data)
            logger.info(f"Tool '{action_name}' executed successfully")
            return result
        except KeyError:
            logger.error(f"Tool '{action_name}' is not registered.")
            return f"Error: Tool '{action_name}' is not registered."
        except Exception as e:
            logger.error(f"Error executing tool '{action_name}': {str(e)}")
            return f"Error executing tool '{action_name}': {str(e)}"
