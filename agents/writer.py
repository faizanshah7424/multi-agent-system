from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.file_reader import FileReaderTool
from tools.file_writer import FileWriterTool
from core.registry import register_agent

@register_agent(
    name="writer",
    role="Technical Content Writer",
    description="Generates documentations, markdown summaries, and project README files.",
    capabilities=["writing", "documentation"],
    tools=["file_reader", "file_writer"]
)
class WriterAgent(BaseAgent):
    """
    Writer agent responsible for generating project documentation, summaries, 
    and Markdown descriptions.
    """
    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.default_model,
            tools=[
                FileReaderTool(),
                FileWriterTool()
            ]
        )

    def run(self, task: str = "") -> str:
        """
        Executes document writing tasks.
        """
        self.memory.add_log(self.role, f"Writing documentation for subtask: '{task}'")
        
        prompt = (
            f"Objective: Generate text/markdown documentation or summaries for: '{task}'\n"
            "Use the file_writer tool to save any required document files (like README.md or API documentation) to disk. "
            "Provide a final text summary of the files created and documentation written."
        )
        
        result = self.run_task(prompt, max_iterations=5)
        
        # Save output to memory
        self.memory.set("writer_result", result)
        return result
