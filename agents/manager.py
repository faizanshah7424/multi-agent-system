from typing import Any, Dict, Optional
from core.memory import SharedMemory
from core.workflow import WorkflowEngine
from core.registry import AgentRegistry


class ManagerAgent:
    """
    Manager Agent acts as the entry point and coordinator for the Multi-Agent system.
    Orchestrates the workflow execution plan by calling the Workflow Engine.
    """

    def __init__(self, session_id: Optional[str] = "default_session"):
        # Shared memory instance
        self.memory = SharedMemory(session_id=session_id)

        # Initialize registry connection
        self.registry = AgentRegistry()

        # Decoupled agent instantiation using registry lookups.
        # Retains original public attribute names to preserve backward compatibility.
        self.planner = self.registry.create_agent("planner", self.memory)
        self.researcher = self.registry.create_agent("researcher", self.memory)
        self.developer = self.registry.create_agent("developer", self.memory)
        self.reviewer = self.registry.create_agent("reviewer", self.memory)
        self.writer = self.registry.create_agent("writer", self.memory)

        # Initialize workflow engine and map local agent instances
        self.engine = WorkflowEngine(self.memory)
        self.engine.agents["planner"] = self.planner
        self.engine.agents["researcher"] = self.researcher
        self.engine.agents["developer"] = self.developer
        self.engine.agents["reviewer"] = self.reviewer
        self.engine.agents["writer"] = self.writer

    def execute(self, task: str) -> Dict[str, Any]:
        """
        Coordinates and runs the multi-agent workflow to solve a given task.

        Args:
            task: Task description or prompt to solve.

        Returns:
            The memory state dictionary representation.
        """
        # Execute workflow through the orchestration engine
        return self.engine.execute_workflow(task)
