import unittest
from core.knowledge.engine import InMemoryGraphEngine
from core.autonomous_repository.repository_planner import RepositoryTaskPlan
from core.autonomous_repository.repository_executor import RepositoryExecutor

class TestRepositoryExecutor(unittest.TestCase):
    def setUp(self):
        self.graph = InMemoryGraphEngine()
        self.executor = RepositoryExecutor(self.graph)
        self.plan = RepositoryTaskPlan(
            requirements=["req1"],
            database_changes=["core/database.py"],
            api_changes=["POST /auth/login"],
            testing_strategy=["tests/test_auth_system.py"]
        )

    def test_run_impact_analysis(self):
        impact = self.executor.run_impact_analysis(self.plan)
        self.assertIn("core/database.py", impact["affected_files"])
        self.assertIn("POST /auth/login", impact["affected_apis"])
        self.assertIn("tests/test_auth_system.py", impact["affected_tests"])

    def test_generate_code_artifacts(self):
        artifacts = self.executor.generate_code_artifacts(self.plan)
        self.assertIn("backend", artifacts)
        self.assertIn("frontend", artifacts)
        self.assertIn("database", artifacts)
        self.assertIn("tests", artifacts)
        self.assertIn("migration_scripts", artifacts)
