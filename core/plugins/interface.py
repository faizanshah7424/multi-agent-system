from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class IPlugin(Protocol):
    """
    Interface for third-party extensions utilizing platform lifecycle hooks.
    """

    def on_startup(self, config: Dict[str, Any]) -> None:
        """Executed during API/Worker startup bootstrap sequences."""
        ...

    def on_task_claim(self, task_id: str, worker_id: str) -> None:
        """Executed when a worker runtime claims a task."""
        ...

    def on_step_complete(
        self, task_id: str, step_id: int, result_payload: Dict[str, Any]
    ) -> None:
        """Executed on successful workflow step completion."""
        ...

    def on_shutdown(self) -> None:
        """Executed on system shutdown."""
        ...


@runtime_checkable
class IPluginManager(Protocol):
    """
    Interface managing and dispatching events to active plugins.
    """

    def register_plugin(self, name: str, plugin: IPlugin) -> None:
        """Registers a plugin instance."""
        ...

    def trigger_startup(self, config: Dict[str, Any]) -> None:
        """Broadcasts startup hooks."""
        ...

    def trigger_task_claim(self, task_id: str, worker_id: str) -> None:
        """Broadcasts task claim hooks."""
        ...

    def trigger_step_complete(
        self, task_id: str, step_id: int, result_payload: Dict[str, Any]
    ) -> None:
        """Broadcasts step completion hooks."""
        ...

    def trigger_shutdown(self) -> None:
        """Broadcasts shutdown hooks."""
        ...
