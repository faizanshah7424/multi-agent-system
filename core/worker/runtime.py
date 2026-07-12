from typing import Protocol, runtime_checkable


@runtime_checkable
class IWorkerRuntime(Protocol):
    """
    Interface for the background daemon processes polling tasks from database.
    """

    def start(self) -> None:
        """Starts worker heartbeat loops and begins polling SQLite for claims."""
        ...

    def stop(self) -> None:
        """Triggers graceful shutdowns and waits for running tasks to complete."""
        ...
