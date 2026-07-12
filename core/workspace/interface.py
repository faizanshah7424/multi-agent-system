from datetime import datetime
from typing import List, Literal, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class FileChange(BaseModel):
    """
    Schema describing a single filesystem modification.
    """

    file_path: str = Field(
        ..., description="Target file path relative to workspace root."
    )
    action: Literal["add", "modify", "delete"] = Field(
        ..., description="Nature of the filesystem change."
    )
    content: str = Field(
        ..., description="Full content (for additions/modifications) or unified diff."
    )


class SessionState(BaseModel):
    """
    Schema representing active session allocations for execution tracking.
    """

    task_id: str = Field(..., description="Unique ID of the active task.")
    workspace_path: str = Field(
        ..., description="Absolute path to the isolated host worktree directory."
    )
    container_id: Optional[str] = Field(
        None, description="Docker container identifier if active."
    )
    git_branch: str = Field(..., description="Isolated workspace git branch name.")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Time of session creation."
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow, description="Time of last heartbeat/action."
    )


@runtime_checkable
class IWorkspaceManager(Protocol):
    """
    Protocol for transactional workspace operations utilizing Git worktrees.
    """

    def create_workspace(self, task_id: str) -> str:
        """
        Creates an isolated git worktree branch for a task and returns its local host path.
        """
        ...

    def stage_changes(self, task_id: str, changes: List[FileChange]) -> None:
        """
        Applies changes safely within the isolated branch.
        """
        ...

    def generate_diff(self, task_id: str) -> str:
        """
        Retrieves the unified diff of the worktree against its parent branch.
        """
        ...

    def commit_and_merge(self, task_id: str) -> bool:
        """
        Applies task modifications back to origin branch and commits.
        """
        ...

    def destroy_workspace(self, task_id: str) -> None:
        """
        Tears down worktree mappings and cleans transient branches.
        """
        ...


@runtime_checkable
class IWorkspaceSessionManager(Protocol):
    """
    Protocol tracking active workspaces, containers, and sessions to prevent leaks.
    """

    def start_session(self, task_id: str) -> SessionState:
        """
        Initializes and registers a tracking session structure.
        """
        ...

    def end_session(self, task_id: str) -> None:
        """
        Cleans up and terminates sandbox and workspace allocations.
        """
        ...
