import time
import logging
from typing import List, Protocol, Optional, runtime_checkable

from core.planning.planning_models import PlannerExecutionPlan, PlanningTask
from core.planning.decomposer import ITaskDecomposer, TaskDecomposer
from core.planning.task_graph import TaskGraph

logger = logging.getLogger(__name__)


@runtime_checkable
class IPlanner(Protocol):
    """
    Interface for the autonomous planning engine.
    """

    def plan(self, objective: str) -> PlannerExecutionPlan:
        """
        Generates a validated hierarchical ExecutionPlan from a natural language goal.
        """
        ...

    def validate(self, plan: PlannerExecutionPlan) -> List[str]:
        """
        Validates an existing execution plan against safety and DAG rules.
        """
        ...

    def health_check(self) -> bool:
        """
        Verifies if the planning engine is operational.
        """
        ...


class Planner(IPlanner):
    """
    Autonomous planning engine coordinating task decomposition, dependency resolution,
    and topological sorting.
    """

    def __init__(self, decomposer: Optional[ITaskDecomposer] = None) -> None:
        if decomposer is None:
            decomposer = TaskDecomposer()
        self.decomposer = decomposer

    def plan(self, objective: str) -> PlannerExecutionPlan:
        start_time = time.time()
        
        # Step 1: Decomposition
        tasks = self.decomposer.decompose(objective)
        
        # Step 2: Build and validate task graph
        task_graph = TaskGraph(tasks)
        errors = task_graph.validate()
        if errors:
            raise ValueError(f"Generated an invalid plan DAG: {'; '.join(errors)}")

        # Step 3: Resolve execution stages
        stages = task_graph.get_execution_stages()
        duration = time.time() - start_time

        # Step 4: Calculate telemetry metrics
        task_count = len(tasks)
        dep_count = sum(len(t.dependencies) for t in tasks)
        parallelism_score = (task_count / len(stages)) if stages else 0.0
        
        # Compute dynamic confidence score
        confidence = 1.0 - (dep_count * 0.05) - (len(errors) * 0.2)
        confidence = max(0.1, min(1.0, confidence))

        telemetry = {
            "planning_duration": duration,
            "task_count": task_count,
            "dependency_count": dep_count,
            "parallelism_score": parallelism_score,
            "planner_confidence": confidence,
        }

        logger.info(
            f"Autonomous planning completed in {duration:.4f}s | "
            f"Tasks: {task_count}, Dependencies: {dep_count}, Stages: {len(stages)}"
        )

        return PlannerExecutionPlan(
            project_title=f"Plan: {objective[:50]}...",
            tasks=tasks,
            confidence_score=confidence,
            execution_stages=stages,
            telemetry=telemetry,
        )

    def validate(self, plan: PlannerExecutionPlan) -> List[str]:
        task_graph = TaskGraph(plan.tasks)
        return task_graph.validate()

    def health_check(self) -> bool:
        return self.decomposer is not None
