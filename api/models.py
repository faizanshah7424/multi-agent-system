from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import re

def validate_alphanumeric_id(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    if not isinstance(v, str):
        raise ValueError("Must be a string.")
    if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
        raise ValueError("Must be alphanumeric with dashes or underscores.")
    return v

class TaskRequest(BaseModel):
    """Schema representing a request to start a background agentic workflow."""
    task: str = Field(
        ..., 
        min_length=1, 
        max_length=50000, 
        description="The high-level prompt or project goal to execute."
    )
    session_id: Optional[str] = Field(
        default=None, 
        max_length=100,
        description="Optional session identifier. Must be alphanumeric with dashes or underscores."
    )

    @field_validator("session_id")
    @classmethod
    def check_session_id(cls, v):
        return validate_alphanumeric_id(v)

class TaskResponse(BaseModel):
    """Schema representing the initial response after queuing a task."""
    session_id: str = Field(..., description="The unique session ID associated with the task.")
    status: str = Field(..., description="The current status of the task workflow.")
    message: str = Field(..., description="Informational message about the workflow initialization.")

class TaskCreateRequest(BaseModel):
    """Schema representing a request to create and enqueue a background task."""
    task_id: Optional[str] = Field(
        default=None, 
        max_length=100,
        description="Optional custom task identifier."
    )
    user_id: Optional[str] = Field(
        default=None, 
        max_length=100,
        description="Optional user ID owner."
    )
    task_type: Optional[str] = Field(
        default="workflow", 
        max_length=50,
        description="Type classification of the task."
    )
    payload: Dict[str, Any] = Field(..., description="Prompt and variables payload required for agent execution.")

    @field_validator("task_id", "user_id", "task_type")
    @classmethod
    def check_ids(cls, v):
        return validate_alphanumeric_id(v)

class ChatRequest(BaseModel):
    """Schema representing a direct interactive chat question/prompt."""
    message: str = Field(..., min_length=1, max_length=50000, description="The text query to send to the agent.")
    session_id: Optional[str] = Field(
        default=None, 
        max_length=100,
        description="Optional session ID to track ongoing conversation context."
    )

    @field_validator("session_id")
    @classmethod
    def check_session_id(cls, v):
        return validate_alphanumeric_id(v)

class ChatResponse(BaseModel):
    """Schema representing the response to a chat prompt."""
    session_id: str = Field(..., description="The active session ID.")
    response: str = Field(..., description="The agent's reply content.")

class StatusResponse(BaseModel):
    """Schema representing the execution status of a task workflow."""
    session_id: str = Field(..., description="The requested session ID.")
    status: str = Field(..., description="Overall workflow status (idle, running, completed, failed).")
    steps: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Detailed execution status for each planned subtask step."
    )

class HistoryResponse(BaseModel):
    """Schema representing the persistent history of a session."""
    session_id: str = Field(..., description="The requested session ID.")
    logs: List[str] = Field(
        default_factory=list, 
        description="The detailed chronological execution logs of agents and systems."
    )
    messages: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="The record of agent-to-agent communication transcripts."
    )

class WorkerInfo(BaseModel):
    """Observability: model representing status details of a background worker thread."""
    worker_name: str
    worker_id: str
    is_alive: bool
    is_healthy: bool
    current_task: Optional[str] = None
    last_active: str
    status: Optional[str] = None
    heartbeat: Optional[str] = None
    uptime: Optional[float] = None
    pid: Optional[int] = None
    hostname: Optional[str] = None

class QueueStatus(BaseModel):
    """Observability: model representing the queue system's state metrics."""
    queue_size: int
    worker_count: int
    tasks_by_status: Dict[str, int]

