from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.dir_scanner import DirScannerTool
from tools.file_reader import FileReaderTool
from core.registry import register_agent


@register_agent(
    name="repository_engineer",
    role="Repository Engineer",
    description="Analyzes the codebase structure, scans dependencies, tracks imports, and outlines repository impact.",
    capabilities=["repository_analysis", "dependencies"],
    tools=["dir_scanner", "file_reader"],
)
class RepositoryEngineerAgent(BaseAgent):
    """
    Repository Engineer Agent responsible for analyzing code structure and dependencies.
    """

    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.default_model,
            tools=[DirScannerTool(), FileReaderTool()],
        )

    def run(self, task: str = "") -> str:
        prompt = (
            f"Objective: Analyze the repository structure and dependencies relevant to the task: '{task}'\n\n"
            "Requirements:\n"
            "1. List all source directories, files, and modules.\n"
            "2. Identify key package imports and internal project dependencies.\n"
            "3. Assess the structural impact of the proposed changes.\n"
            "4. Search for potential naming collisions, dependency cycles, or file conflicts."
        )
        result = self.run_task(prompt, max_iterations=4)
        self.memory.set("repository_analysis", result)
        return result
