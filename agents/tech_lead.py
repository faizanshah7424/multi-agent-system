from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.file_reader import FileReaderTool
from core.registry import register_agent


@register_agent(
    name="tech_lead",
    role="Tech Lead",
    description="Moderates technical disputes, votes on approvals, coordinates consensus, and ensures engineering quality.",
    capabilities=["moderation", "consensus", "dispute_resolution"],
    tools=["file_reader"],
)
class TechLeadAgent(BaseAgent):
    """
    Tech Lead Agent responsible for moderating debates, resolving conflicts, and signing off on code modifications.
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
            f"Objective: Arbitrate and resolve any pending technical disputes or code review conflicts for: '{task}'\n\n"
            "Requirements:\n"
            "1. Read the developer's proposed code modifications and the reviewer's critiques/objections.\n"
            "2. Decide if the reviewer's concerns are valid and identify appropriate compromises.\n"
            "3. Render a final decision: Approve, Reject, or request Revisions.\n"
            "4. Provide the exact technical rationale and path forward."
        )
        result = self.run_task(prompt, max_iterations=4)
        self.memory.set("tech_lead_decision", result)
        return result
