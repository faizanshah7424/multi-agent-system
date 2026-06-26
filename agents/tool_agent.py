from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools import get_tool_instances
from core.registry import register_agent

@register_agent(
    name="tool_agent",
    role="Dynamic Tool Agent",
    description="Generic tool execution proxy equipped with all system tools.",
    capabilities=["tools_execution", "dynamic_routing"],
    tools=["file_reader", "file_writer", "dir_scanner", "python_executor", "web_search"]
)
class ToolAgent(BaseAgent):
    """
    Specialized agent equipped with all tools in the system.
    Serves as a generic tool execution proxy that can solve queries by dynamically
    composing multiple tools. Future-ready for third-party tools integration.
    """
    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.default_model,
            tools=get_tool_instances()  # Equip with every tool registered in tools/__init__.py
        )

    def run(self, task: str) -> str:
        """
        Executes a task using the full registry of system tools.
        """
        self.memory.add_log(self.role, f"ToolAgent invoked with request: '{task}'")
        
        prompt = (
            f"Please solve this task: '{task}'\n"
            "You are equipped with all system tools. Select the appropriate tool(s) "
            "sequentially to resolve this request and output the results."
        )
        
        result = self.run_task(prompt, max_iterations=10)
        
        # Save output to memory
        self.memory.set("tool_agent_result", result)
        return result
