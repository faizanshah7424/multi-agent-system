from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.file_reader import FileReaderTool
from tools.file_writer import FileWriterTool
from tools.python_executor import PythonExecutorTool
from tools.dir_scanner import DirScannerTool
from core.registry import register_agent


@register_agent(
    name="developer",
    role="Senior Software Engineer",
    description="Writes source files, runs scripts, debugs errors, and walks structures.",
    capabilities=["coding", "development", "debugging"],
    tools=["file_reader", "file_writer", "python_executor", "dir_scanner"],
)
class DeveloperAgent(BaseAgent):
    """
    Developer agent equipped with code reading, writing, structure scanning, and python execution tools.
    Can write complete script files, execute test suites, and fix runtime errors interactively.
    """

    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.developer_model,
            tools=[
                FileReaderTool(),
                FileWriterTool(),
                PythonExecutorTool(),
                DirScannerTool(),
            ],
        )

    def run(self, task: str = "") -> str:
        """
        Executes code development. Reads research context from memory, builds implementation,
        validates via script execution, and saves implementation summary.
        """
        # Pull latest research information from memory
        research = self.memory.get("research", "No research context available.")
        plan = self.memory.get("plan", "No plan available.")

        prompt = (
            f"Objective: Write production-ready code files to complete the task: '{task}'\n"
            f"Refer to the project plan:\n{plan}\n\n"
            f"Here is the research summary gathered:\n{research}\n\n"
            "Your tasks:\n"
            "1. Write the source code files to the filesystem using the 'file_writer' tool.\n"
            "2. Verify and test the written scripts using 'python_executor' to ensure they run successfully.\n"
            "3. If any runtime or import error occurs, read the files, fix the issues, and write them back.\n"
            "4. Provide a detailed summary of the implemented modules and code structure as your final answer."
        )

        result = self.run_task(prompt, max_iterations=8)

        # Save development summary to memory
        self.memory.set("code", result)
        return result
