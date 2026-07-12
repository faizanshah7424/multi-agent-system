from typing import Any, Dict, List, Optional
from core.registry.interface import IToolRegistry, ToolDefinition


class ToolRegistry(IToolRegistry):
    """
    Concrete Tool Registry managing tool registration, capability filtering,
    read/write permissions, and agent role-level restrictions.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}
        # Maps tool name to list of required capabilities
        self._capabilities: Dict[str, List[str]] = {}
        # Maps tool name to "READ_ONLY", "WRITE", or "ADMIN"
        self._permission_levels: Dict[str, str] = {}
        # Maps tool name to list of allowed agent roles
        self._allowed_roles: Dict[str, List[str]] = {}
        # Metadata definitions
        self._tool_definitions: Dict[str, ToolDefinition] = {}

    def register_tool(
        self,
        name: str,
        tool_instance: Any,
        capabilities: List[str],
        permission_level: str = "READ_ONLY",
        allowed_roles: Optional[List[str]] = None,
        tool_definition: Optional[ToolDefinition] = None,
    ) -> None:
        """
        Registers a tool into the system catalog.
        """
        self._tools[name] = tool_instance
        self._capabilities[name] = capabilities
        self._permission_levels[name] = permission_level
        self._allowed_roles[name] = allowed_roles or ["*"]
        if tool_definition:
            self._tool_definitions[name] = tool_definition

    def get_agent_tools(
        self, agent_role: str, agent_capabilities: List[str]
    ) -> List[Any]:
        """
        Filters and returns the list of tool instances that match the agent's role and capabilities.
        """
        allowed = []
        for name, instance in self._tools.items():
            # 1. Capability Check: agent must satisfy all required capabilities for the tool
            req_caps = self._capabilities[name]
            if not all(cap in agent_capabilities for cap in req_caps):
                continue

            # 2. Role Restriction Check
            roles = self._allowed_roles[name]
            if "*" not in roles and agent_role not in roles:
                continue

            allowed.append(instance)
        return allowed

    def get_tool_definition(self, name: str) -> Optional[ToolDefinition]:
        """Retrieves definition metadata for a tool."""
        return self._tool_definitions.get(name)

    def list_tools(self) -> List[str]:
        """Lists all registered tool names."""
        return list(self._tools.keys())
