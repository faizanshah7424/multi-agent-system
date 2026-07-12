from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class InjectableBug(BaseModel):
    """
    Schema defining a deterministic code bug injection.
    """

    bug_id: str = Field(..., description="Unique ID for the bug.")
    file_path: str = Field(..., description="Relative path of target file to modify.")
    target_content: str = Field(..., description="Original code string to locate.")
    bug_content: str = Field(..., description="Buggy code string to replace with.")
    category: str = Field(
        ...,
        description="Failure category (e.g. SYNTAX_ERROR, IMPORT_ERROR, TYPE_ERROR, LINT_ERROR, UNIT_TEST_FAILURE)",
    )


class BenchmarkProject(BaseModel):
    """
    Representation of a template project inside the benchmark library.
    """

    name: str = Field(..., description="Name of the benchmark project.")
    category: str = Field(
        ...,
        description="Platform/Technology category (Python, FastAPI, TypeScript, React, Next.js, etc.)",
    )
    files: Dict[str, str] = Field(
        ..., description="Mapping of relative paths to file contents."
    )
    injectable_bugs: List[InjectableBug] = Field(
        default_factory=list, description="List of supportable bugs."
    )


class BenchmarkMetric(BaseModel):
    """
    Metrics collected during a benchmark run execution.
    """

    detection_accuracy: float = Field(default=0.0)
    root_cause_accuracy: float = Field(default=0.0)
    repair_success_rate: float = Field(default=0.0)
    validation_success_rate: float = Field(default=0.0)
    average_repair_time: float = Field(default=0.0)
    repair_attempts: int = Field(default=0)
    files_modified: int = Field(default=0)
    false_repairs: int = Field(default=0)

    # Sprint 11 Performance Telemetry Latency breakdown
    startup_time: float = Field(default=0.0)
    planning_latency: float = Field(default=0.0)
    execution_latency: float = Field(default=0.0)
    sandbox_startup: float = Field(default=0.0)
    repository_indexing: float = Field(default=0.0)
    memory_retrieval: float = Field(default=0.0)
    consensus_duration: float = Field(default=0.0)
    self_healing_duration: float = Field(default=0.0)


class BenchmarkReport(BaseModel):
    """
    Final benchmark run scorecard trace.
    """

    project_name: str
    category: str
    bug_id: str
    status: str = Field(..., description="Execution status: SUCCESS or FAILED")
    duration_seconds: float
    metrics: BenchmarkMetric
    scores: Dict[str, float] = Field(
        default_factory=dict, description="Maturity scores per capability."
    )
