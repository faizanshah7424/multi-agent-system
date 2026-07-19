import re
from typing import List, Protocol, runtime_checkable
from core.planning.planning_models import PlanningTask


@runtime_checkable
class ITaskDecomposer(Protocol):
    """
    Interface for planning task decomposition and complexity estimation.
    """

    def decompose(self, objective: str) -> List[PlanningTask]:
        """
        Decomposes a high-level goal objective into atomic planning tasks.
        """
        ...

    def estimate_complexity(self, task: PlanningTask) -> str:
        """
        Estimates the complexity classification for a task.
        """
        ...


class TaskDecomposer(ITaskDecomposer):
    """
    Heuristic-driven autonomous task decomposer.
    Parses objectives, extracts requirements, assigns specialized agents,
    and calculates task complexity metrics.
    """

    def decompose(self, objective: str) -> List[PlanningTask]:
        objective_lower = objective.lower()
        tasks: List[PlanningTask] = []

        # Heuristic 1: Database, API, and Testing stack
        if "api" in objective_lower or "endpoint" in objective_lower or "crud" in objective_lower:
            tasks.append(
                PlanningTask(
                    task_id=1,
                    name="Initialize Data Model and Database Schema",
                    description="Configure persistence layer, database connections, and model definitions.",
                    assigned_agent="developer",
                    dependencies=[],
                    priority="high",
                    files=["core/database.py", "core/models.py"],
                )
            )
            tasks.append(
                PlanningTask(
                    task_id=2,
                    name="Implement API Routes and Controller Logic",
                    description="Implement endpoints, payload schemas, and business controllers.",
                    assigned_agent="developer",
                    dependencies=[1],
                    priority="high",
                    files=["api/routes.py", "api/schemas.py"],
                )
            )
            tasks.append(
                PlanningTask(
                    task_id=3,
                    name="Write Automated Unit and Integration Tests",
                    description="Create test cases covering successful flows, edge cases, and error responses.",
                    assigned_agent="reviewer",
                    dependencies=[2],
                    priority="medium",
                    files=["tests/test_api.py"],
                )
            )
            tasks.append(
                PlanningTask(
                    task_id=4,
                    name="Verify End-to-End System and Deployment Pipeline",
                    description="Run local test suite, configure entry points, and execute post-deploy checks.",
                    assigned_agent="repository_engineer",
                    dependencies=[3],
                    priority="medium",
                    files=["main.py", "Dockerfile"],
                )
            )

        # Heuristic 2: Refactoring / Optimization
        elif "refactor" in objective_lower or "optimize" in objective_lower or "clean" in objective_lower:
            tasks.append(
                PlanningTask(
                    task_id=1,
                    name="Analyze Codebase Architecture and Profiling",
                    description="Identify bottleneck functions, architectural patterns, and code smells.",
                    assigned_agent="researcher",
                    dependencies=[],
                    priority="medium",
                    files=[],
                )
            )
            tasks.append(
                PlanningTask(
                    task_id=2,
                    name="Execute Code Refactoring and Optimization",
                    description="Restructure target modules to improve complexity, readability, and performance.",
                    assigned_agent="developer",
                    dependencies=[1],
                    priority="high",
                    files=[],
                )
            )
            tasks.append(
                PlanningTask(
                    task_id=3,
                    name="Verify Code Health and Regression Tests",
                    description="Execute existing test suites to guarantee no behavior regressions.",
                    assigned_agent="reviewer",
                    dependencies=[2],
                    priority="high",
                    files=[],
                )
            )

        # Heuristic 3: Default General Engineering Objective
        else:
            tasks.append(
                PlanningTask(
                    task_id=1,
                    name="Research Requirements and Technical Design",
                    description=f"Gather context and specify technical strategy for: {objective}",
                    assigned_agent="researcher",
                    dependencies=[],
                    priority="medium",
                    files=[],
                )
            )
            tasks.append(
                PlanningTask(
                    task_id=2,
                    name="Implement Solution Functionality",
                    description="Write the code implementation for the target engineering task.",
                    assigned_agent="developer",
                    dependencies=[1],
                    priority="high",
                    files=[],
                )
            )
            tasks.append(
                PlanningTask(
                    task_id=3,
                    name="Review Implementation and Write Tests",
                    description="Run static audits, check formatting, and verify coverage tests.",
                    assigned_agent="reviewer",
                    dependencies=[2],
                    priority="medium",
                    files=[],
                )
            )

        # Assign estimated complexity to each task
        for task in tasks:
            task.estimated_complexity = self.estimate_complexity(task)

        return tasks

    def estimate_complexity(self, task: PlanningTask) -> str:
        """
        Calculates task complexity class based on files count, descriptions, and dependencies.
        """
        file_weight = len(task.files) * 2.0
        dep_weight = len(task.dependencies) * 1.5
        desc_weight = len(task.description.split()) * 0.05
        
        score = file_weight + dep_weight + desc_weight

        if score < 2.0:
            return "Low"
        elif score < 5.0:
            return "Medium"
        elif score < 9.0:
            return "High"
        else:
            return "Very High"
