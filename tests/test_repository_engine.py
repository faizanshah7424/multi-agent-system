import unittest
from core.knowledge.engine import InMemoryGraphEngine
from core.autonomous_repository.repository_engine import AutonomousRepositoryEngine


class TestRepositoryEngine(unittest.TestCase):
    def setUp(self):
        self.graph = InMemoryGraphEngine()
        self.engine = AutonomousRepositoryEngine(self.graph)

    def test_run_repository_engineering_success(self):
        res = self.engine.run_repository_engineering("Create Login System")
        self.assertTrue(res["success"])
        self.assertIsNone(res["failures"])
        self.assertGreater(res["duration_s"], 0)
        self.assertIn("implementation_report", res["reports"])

    def test_run_repository_engineering_failure(self):
        def bad_apply(artifacts):
            raise ValueError("Applying changes raised custom error.")

        res = self.engine.run_repository_engineering(
            "Build Blog CMS", apply_changes_fn=bad_apply
        )
        self.assertFalse(res["success"])
        self.assertIn("Applying changes raised custom error.", res["failures"])
