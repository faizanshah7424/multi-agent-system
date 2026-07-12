from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class IBenchmarkManager(Protocol):
    """
    Interface orchestrating benchmark workspace creation, deterministic
    bug injection, execution runs, metrics collection, and scorecard reports.
    """

    def run_benchmark(self, project_name: str, bug_id: str) -> Dict[str, Any]:
        """
        Runs the benchmark E2E: prepares environment, injects bug, executes plan runtime,
        measures self-healing repairs, and calculates scores.
        """
        ...

    def list_projects(self) -> Dict[str, Any]:
        """
        Returns a list of all discovered benchmark projects in the library.
        """
        ...
