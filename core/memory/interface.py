from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class IEngineeringMemoryEngine(Protocol):
    """
    Interface for the persistent Engineering Memory Engine (EME).
    Stores and retrieves software engineering conventions, past fixes,
    and episodic debug sessions.
    """

    def record_fix(
        self,
        task_id: str,
        step_id: int,
        file_path: str,
        error_msg: str,
        applied_fix: str,
    ) -> None:
        """
        Records a successful debug/repair session in the persistent episodic ledger.
        """
        ...

    def retrieve_similar_fixes(
        self, error_msg: str, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Queries EME to retrieve relevant past fixes based on semantic traceback overlaps.
        """
        ...

    def compact_memories(self) -> None:
        """
        Triggers memory compaction to summarize verbose trace logs and optimize context bounds.
        """
        ...

    def record_convention(
        self,
        task_id: str,
        file_path: str,
        convention_name: str,
        description: str,
        category: str = "general",
    ) -> None:
        """
        Records a software engineering convention or styling policy.
        """
        ...

    def retrieve_similar_conventions(
        self, query: str, file_path: Optional[str] = None, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Queries EME to retrieve relevant conventions based on a file path or semantic query.
        """
        ...
