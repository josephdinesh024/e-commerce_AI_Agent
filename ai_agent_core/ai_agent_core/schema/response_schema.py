"""
Response schema definitions using Pydantic for validation and serialization.
"""

from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class AgentActionPattern(BaseModel):
    """
    Schema for parsing actions from the LLM.
    The planner expects this format from the LLM when determining actions.
    """
    thought: str = Field(description="Reasoning behind the action")
    action: str = Field(description="Name of the tool to execute")
    input: Union[str, Dict[str, Any]] = Field(description="Input parameters for the tool")
    final: bool = Field(default=False, description="Whether this action concludes the task")

class AgentResponse(BaseModel):
    """
    Standardized response structure returned by the AgentCore.
    """
    message: str = Field(default="", description="Text reply to the user")
    html_content: str = Field(default="", description="Optional HTML content")
    action: Optional[str] = Field(default=None, description="Description of action taken, if any")
    speak: bool = Field(default=True, description="Whether the UI/system should speak the response")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
