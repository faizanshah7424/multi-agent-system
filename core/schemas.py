from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# =====================================================================
# Planner Models
# =====================================================================


class PlanStep(BaseModel):
    """
    Structured model for a single step in a project execution workflow.
    """

    step_id: int = Field(..., description="Unique step identifier (1-indexed).")
    title: str = Field(..., description="Title describing the step.")
    assigned_agent: str = Field(
        ...,
        description="Ecosystem agent name assigned to this task (e.g., researcher, developer, reviewer).",
    )
    description: str = Field(
        ..., description="Detailed instructions of what must be executed in this step."
    )
    dependencies: List[int] = Field(
        default_factory=list,
        description="List of step_ids that must complete before this step can begin.",
    )
    priority: str = Field(
        default="medium",
        description="Priority level of the task step (low, medium, high).",
    )


class PlannerPlan(BaseModel):
    """
    Structured project execution plan containing a list of task steps.
    """

    project_title: str = Field(
        ..., description="Title of the project or target objective."
    )
    steps: List[PlanStep] = Field(
        ..., description="List of sequential steps forming the execution plan."
    )


# =====================================================================
# Agent Reasoning Models
# =====================================================================


class AgentAction(BaseModel):
    """
    Strict reasoning structure defining agent thought and selected actions.
    Ensures that either a tool call is made or a final answer is returned.
    """

    thought: str = Field(
        ..., description="Detailed inner monologue justifying this step's choice."
    )
    action: str = Field(
        ...,
        description="Action type: 'call_tool' to invoke a tool, or 'respond' to return the final answer.",
    )
    tool: Optional[str] = Field(
        default=None,
        description="The name of the tool to execute. Required if action is 'call_tool'.",
    )
    arguments: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Key-value arguments for tool execution. Required if action is 'call_tool'.",
    )
    final_answer: Optional[str] = Field(
        default=None,
        description="The final answer output text. Required if action is 'respond'.",
    )


# =====================================================================
# Tool Execution Models
# =====================================================================


class ToolRequest(BaseModel):
    """
    Represents a payload schema to execute a tool.
    """

    tool_name: str = Field(..., description="The exact registered name of the tool.")
    arguments: Dict[str, Any] = Field(
        ..., description="Parameters dictionary to execute the tool."
    )


class ToolResponse(BaseModel):
    """
    Represents the output structure of a tool execution.
    """

    tool_name: str = Field(..., description="The executed tool's name.")
    status: str = Field(..., description="Outcome status (success or error).")
    result: str = Field(
        ..., description="Stringified output or logs of tool execution."
    )
    error: Optional[str] = Field(
        default=None, description="Explicit error stack or message if status is error."
    )


# =====================================================================
# Future Compatibility Models
# =====================================================================


class VectorMemoryConfig(BaseModel):
    """
    Configuration model for semantic long-term memory.
    """

    collection_name: str = Field(
        ..., description="Name of the vector space collection."
    )
    dimension: int = Field(default=1536, description="Embedding vector size.")
    embedding_model: str = Field(
        default="text-embedding-004",
        description="Model used to generate vector embeddings.",
    )
    distance_metric: str = Field(
        default="cosine", description="Distance formula (cosine, L2, dot_product)."
    )


class DAGWorkflowPlan(BaseModel):
    """
    DAG representation schema supporting arbitrary complex, non-linear workflows.
    """

    workflow_id: str = Field(..., description="Unique workflow pipeline ID.")
    nodes: List[Dict[str, Any]] = Field(
        ..., description="Vertices representing execution agents or tasks."
    )
    edges: List[Dict[str, Any]] = Field(
        ..., description="Directed edges mapping pipeline step execution dependencies."
    )


class MultiAgentCollaborationConfig(BaseModel):
    """
    Configuration schema enabling direct multi-agent message routing and voting.
    """

    session_id: str = Field(..., description="Collaboration context ID.")
    participants: List[str] = Field(
        ..., description="Names of agents participating in the conversation."
    )
    protocol: str = Field(
        default="discussion",
        description="Protocol type (e.g. consensus, debate, discussion).",
    )


class HumanApprovalWorkflow(BaseModel):
    """
    Schema tracking human-in-the-loop validation actions for high-risk tool usage.
    """

    step_id: int = Field(
        ..., description="Target workflow step ID requiring validation."
    )
    status: str = Field(
        ..., description="Approval status (pending, approved, rejected)."
    )
    approved_by: Optional[str] = Field(
        default=None, description="Username or system agent recording approval."
    )
    comments: Optional[str] = Field(
        default=None, description="Review feedback or modification requests."
    )
