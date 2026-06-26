from typing import Any
from agents.base_agent import BaseAgent
from config import settings
from tools.dir_scanner import DirScannerTool
from tools.file_reader import FileReaderTool
from tools.web_search import WebSearchTool
from core.registry import register_agent

@register_agent(
    name="researcher",
    role="Research Specialist",
    description="Scans directories, reads source code, and scrapes web search queries.",
    capabilities=["research", "scanning", "web_scraping"],
    tools=["dir_scanner", "file_reader", "web_search"]
)
class ResearchAgent(BaseAgent):
    """
    Agent equipped with tools to gather project requirements, scan directories, 
    read existing code files, and fetch web search results.
    """
    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.researcher_model,
            tools=[
                DirScannerTool(),
                FileReaderTool(),
                WebSearchTool()
            ]
        )

    def run(self, task: str) -> str:
        """
        Executes research on a given task, writing results back to shared memory.
        """
        prompt = (
            f"Please conduct research to solve or understand this task:\n{task}\n"
            "Use the directory scanner, file reader, and web search to collect necessary information. "
            "Examine any relevant codebase files to understand the project structure."
        )
        
        result = self.run_task(prompt, max_iterations=7)
        
        # Save research findings to memory
        self.memory.set("research", result)
        return result