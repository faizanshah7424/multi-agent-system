from typing import Any, Dict, List, Protocol, Type, runtime_checkable
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """
    Metadata representation describing an agent execution tool.
    """

    name: str = Field(..., description="Unique tool identifier name.")
    description: str = Field(..., description="Action summary used by agent planners.")
    args_schema: Type[BaseModel] = Field(
        ..., description="Pydantic validation schema class."
    )
    required_capabilities: List[str] = Field(
        default_factory=list, description="Capabilities required to use this tool."
    )


@runtime_checkable
class IToolRegistry(Protocol):
    """
    Protocol managing role-based capability boundaries on tools.
    """

    def register_tool(
        self, name: str, tool_instance: Any, capabilities: List[str]
    ) -> None:
        """
        Adds a tool instance to the global catalog with capability requirements.
        """
        ...

    def get_agent_tools(
        self, agent_role: str, agent_capabilities: List[str]
    ) -> List[Any]:
        """
        Retrieves all tools permitted for an agent's capabilities and role.
        """
        ...


@runtime_checkable
class ISkillRegistry(Protocol):
    """
    Protocol loading and executing dynamic procedural workflow skill files.
    """

    def register_skill(self, name: str, skill_markdown_path: str) -> None:
        """
        Registers a markdown skill definition file.
        """
        ...

    def get_skill_instructions(self, name: str) -> str:
        """
        Retrieves instructions for a skill to load into the agent's context.
        """
        ...


@runtime_checkable
class IPromptLibrary(Protocol):
    """
    Protocol managing version-controlled prompt files.
    """

    def get_prompt(self, name: str, variables: Dict[str, str]) -> str:
        """
        Loads a prompt template, formats it, and returns the result.
        """
        ...
