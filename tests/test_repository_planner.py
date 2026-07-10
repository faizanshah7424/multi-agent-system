import unittest
from core.autonomous_repository.repository_context import RepositoryContext
from core.autonomous_repository.repository_planner import RepositoryPlanner

class TestRepositoryPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = RepositoryPlanner()
        self.context = RepositoryContext(
            frameworks=["FastAPI"],
            tests=["tests/test_auth_system.py"]
        )

    def test_create_plan_auth(self):
        plan = self.planner.create_plan("Create Login System", self.context)
        self.assertGreater(len(plan.requirements), 0)
        self.assertGreater(len(plan.database_changes), 0)
        self.assertGreater(len(plan.api_changes), 0)
        self.assertEqual(plan.estimated_effort, "4 hours")

    def test_create_plan_custom(self):
        plan = self.planner.create_plan("Build an Inventory Module", self.context)
        self.assertIn("Fulfill custom goal", plan.requirements[0])
        self.assertEqual(plan.estimated_effort, "6 hours")
