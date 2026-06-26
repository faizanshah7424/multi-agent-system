from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.file_reader import FileReaderTool
from tools.python_executor import PythonExecutorTool
from tools.dir_scanner import DirScannerTool
from core.registry import register_agent

@register_agent(
    name="reviewer",
    role="Principal Reviewer",
    description="Audits source code files, validates functionality, and runs test commands.",
    capabilities=["reviewing", "linting", "auditing"],
    tools=["file_reader", "python_executor", "dir_scanner"]
)
class ReviewerAgent(BaseAgent):
    """
    Reviewer agent responsible for analyzing developer code, verifying correctness,
    checking conventions/clean code standards, and running code syntax/lint validations.
    """
    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.reviewer_model,
            tools=[
                FileReaderTool(),
                PythonExecutorTool(),
                DirScannerTool()
            ]
        )

    def run(self, task: str = "") -> str:
        """
        Runs code review. Reads files, executes tests, formats feedback, and stores to memory.
        """
        code_summary = self.memory.get("code", "No code summary available.")
        
        prompt = (
            f"Objective: Review the code implementation for the task: '{task}'\n"
            f"Here is the developer's summary:\n{code_summary}\n\n"
            "Using the directory scanner and file reader, find and inspect the written files.\n"
            "Assess the following criteria:\n"
            "1. Functional correctness (logical errors, edge cases).\n"
            "2. Software architecture and SOLID principles.\n"
            "3. Proper exception handling and logging.\n"
            "4. Code quality (docstrings, typing, styling).\n\n"
            "If code quality is lacking, describe exactly what changes are needed. "
            "If code is excellent, give a clear approval. Return your review report as the final answer."
        )
        
        result = self.run_task(prompt, max_iterations=6)
        
        # Save review report to memory
        self.memory.set("review", result)
        return result