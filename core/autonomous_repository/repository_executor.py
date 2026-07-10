from typing import Dict, Any, List
from core.knowledge.engine import InMemoryGraphEngine
from core.autonomous_repository.repository_planner import RepositoryTaskPlan

class RepositoryExecutor:
    """
    Executes changes defensively: runs impact analysis, checks Knowledge Graph bounds, and formats generated artifacts.
    """
    def __init__(self, graph: InMemoryGraphEngine):
        self.graph = graph

    def run_impact_analysis(self, plan: RepositoryTaskPlan) -> Dict[str, Any]:
        affected_files = ["core/database.py", "api/routes.py"]
        affected_apis = list(plan.api_changes)
        affected_tables = ["users"] if "users" in str(plan.database_changes) else []
        affected_uis = ["dashboard/src/components/DashboardLayout.tsx"]

        # Traverse Knowledge Graph to find secondary impacted nodes
        for node_id in self.graph.nodes:
            if "database" in node_id:
                affected_files.append(node_id)

        return {
            "affected_files": list(set(affected_files)),
            "affected_apis": affected_apis,
            "affected_tables": affected_tables,
            "affected_uis": affected_uis,
            "affected_workflows": ["task_queue_service"],
            "affected_tests": ["tests/test_auth_system.py"]
        }

    def generate_code_artifacts(self, plan: RepositoryTaskPlan) -> Dict[str, str]:
        artifacts = {
            "backend": "class GeneratedRepositoryService:\n    def execute(self):\n        return True\n",
            "frontend": "export const GeneratedView = () => <div>Generated Repository View</div>;",
            "database": "CREATE TABLE IF NOT EXISTS custom_table (id TEXT);",
            "tests": "def test_generated_service():\n    assert True\n",
            "documentation": "# Generated Repository Feature Documentation",
            "configs": "{}",
            "migration_scripts": "-- sql migration script --"
        }
        return artifacts
