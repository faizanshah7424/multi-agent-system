from core.registry import discover_agents

# Import agents explicitly to trigger registration decorators
from agents.base_agent import BaseAgent
from agents.manager import ManagerAgent
from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.developer import DeveloperAgent
from agents.reviewer import ReviewerAgent
from agents.tool_agent import ToolAgent
from agents.writer import WriterAgent
from agents.product_builder import ProductBuilderAgent
from agents.repository_engineer import RepositoryEngineerAgent
from agents.tech_lead import TechLeadAgent
from agents.architect import ArchitectAgent

__all__ = [
    "BaseAgent",
    "ManagerAgent",
    "PlannerAgent",
    "ResearchAgent",
    "DeveloperAgent",
    "ReviewerAgent",
    "ToolAgent",
    "WriterAgent",
    "ProductBuilderAgent",
    "RepositoryEngineerAgent",
    "TechLeadAgent",
    "ArchitectAgent",
]

# Run dynamic discovery to auto-register any external/custom plugin agents placed in this folder
discover_agents()
