from typing import List, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class SandboxExecutionResult(BaseModel):
    """
    Schema representing the outcome of a sandboxed script or command execution.
    """

    exit_code: int = Field(..., description="Process exit code (0 for success).")
    stdout: str = Field(..., description="Captured standard output content.")
    stderr: str = Field(..., description="Captured standard error content.")
    duration_seconds: float = Field(..., description="Time taken to run the execution.")
    timeout_exceeded: bool = Field(
        ..., description="Flag indicating if the execution exceeded the limit."
    )


@runtime_checkable
class ISandbox(Protocol):
    """
    Protocol declaring lifecycle and execution operations for isolated sandboxes.
    """

    def start(self) -> None:
        """
        Provisions and starts the isolated container or virtual machine.
        """
        ...

    def execute(self, cmd: List[str], timeout: float = 30.0) -> SandboxExecutionResult:
        """
        Executes a command within the sandbox under isolated environment limits.

        Args:
            cmd: Command tokens to run.
            timeout: Limit on run time in seconds.

        Returns:
            The execution results containing output and exit code.
        """
        ...

    def copy_in(self, local_path: str, remote_path: str) -> None:
        """
        Safely copies a file or folder from the host into the sandbox mount.
        """
        ...

    def copy_out(self, remote_path: str, local_path: str) -> None:
        """
        Safely copies a file or folder from the sandbox mount onto the host.
        """
        ...

    def terminate(self) -> None:
        """
        Forcefully stops and cleans up sandbox resources.
        """
        ...
