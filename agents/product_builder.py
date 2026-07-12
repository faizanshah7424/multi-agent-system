from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.file_reader import FileReaderTool
from core.registry import register_agent


@register_agent(
    name="product_builder",
    role="Product Builder",
    description="Formulates product requirements, vision, and specifications from user ideas.",
    capabilities=["product_design", "requirements"],
    tools=["file_reader"],
)
class ProductBuilderAgent(BaseAgent):
    """
    Product Builder Agent responsible for translating ideas into formal software requirements and visions.
    """

    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.default_model,
            tools=[FileReaderTool()],
        )

    def run(self, task: str = "") -> str:
        prompt = (
            f"Objective: Translate the user idea or task into clear product requirements, specs, and a project vision.\n"
            f"User input / task: '{task}'\n\n"
            "Requirements:\n"
            "1. Output a clear product vision statement.\n"
            "2. List functional requirements as a structured list.\n"
            "3. Enumerate design and architectural constraints.\n"
            "4. Provide a structured summary of the product scope."
        )
        result = self.run_task(prompt, max_iterations=4)
        self.memory.set("product_specs", result)
        return result
