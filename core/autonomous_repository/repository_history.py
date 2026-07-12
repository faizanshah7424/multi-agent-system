from typing import List, Dict, Any
from core.autonomous_repository.repository_memory import (
    RepositoryMemory,
    RepositoryRecord,
)


class RepositoryHistory:
    """
    Provides formatted summary views of previous repository engineering jobs.
    """

    def __init__(self, memory: RepositoryMemory):
        self.memory = memory

    def get_summary_history(self) -> List[Dict[str, Any]]:
        records = self.memory.list_records()
        history_list = []
        for r in records:
            # Safely get outcome
            is_success = r.validation_results.get("success", True)
            if isinstance(r.validation_results.get("success"), dict):
                is_success = all(r.validation_results["success"].values())
            history_list.append(
                {
                    "id": r.id,
                    "goal": r.goal,
                    "duration_seconds": r.execution_duration_seconds,
                    "success": is_success,
                    "timestamp": r.timestamp,
                }
            )
        return history_list
