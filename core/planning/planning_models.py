from typing import Any, Dict, List
from pydantic import BaseModel, Field
from core.queue.scheduler import ExecutionStage


class PlanningTask(BaseModel):
    """
    Data model representing an atomic, independent, and serializable planning task.
    """

    task_id: int = Field(..., description="Unique task step identifier (1-indexed).")
    name: str = Field(..., description="Title of the planning task step.")
    description: str = Field(..., description="Detailed instructions of the task execution.")
    assigned_agent: str = Field(..., description="Ecosystem agent assigned to this task (e.g. researcher, developer).")
    dependencies: List[int] = Field(default_factory=list, description="List of task_ids this task depends on.")
    priority: str = Field(default="medium", description="Priority level (low, medium, high).")
    estimated_complexity: str = Field(default="Medium", description="Complexity (Low, Medium, High, Very High).")
    files: List[str] = Field(default_factory=list, description="Files affected by this task.")


class PlannerExecutionPlan(BaseModel):
    """
    Execution plan output by the autonomous planning engine.
    """

    project_title: str = Field(..., description="Title of the project or objective.")
    tasks: List[PlanningTask] = Field(..., description="List of decomposed tasks.")
    confidence_score: float = Field(default=1.0, description="Confidence score of the generated plan (0.0 to 1.0).")
    execution_stages: List[ExecutionStage] = Field(default_factory=list, description="Sequenced stages for parallel execution.")
    telemetry: Dict[str, Any] = Field(default_factory=dict, description="Planning metrics and telemetry.")
