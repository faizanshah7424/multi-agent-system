from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.file_reader import FileReaderTool
from core.registry import register_agent


@register_agent(
    name="architect",
    role="Architect",
    description="Validates code and plans against design patterns, architectural style guides, and structural specifications.",
    capabilities=["architectural_review", "standards"],
    tools=["file_reader"],
)
class ArchitectAgent(BaseAgent):
    """
    Architect Agent responsible for reviewing plans, designs, and code structures for architectural compliance.
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
            f"Objective: Review the planned execution steps or proposed code changes for architectural fit and naming conventions: '{task}'\n\n"
            "Requirements:\n"
            "1. Inspect the planned file structure, imports, design patterns, and naming.\n"
            "2. Identify any violations of architectural integrity, circular references, or style guides.\n"
            "3. Render an approval status (Approved / Rejected) with explanation.\n"
            "4. Suggest structural refactoring or patterns if rejected."
        )
        result = self.run_task(prompt, max_iterations=4)
        self.memory.set("architect_review", result)
        return result
