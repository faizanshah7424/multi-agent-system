import unittest
from core.feature_engine.feature_parser import FeatureParser
from core.feature_engine.feature_planner import FeaturePlanner

class TestFeaturePlanner(unittest.TestCase):
    def setUp(self):
        self.parser = FeatureParser()
        self.planner = FeaturePlanner()

    def test_create_plan(self):
        spec = self.parser.parse_requirement("Create an Inventory Module")
        plan = self.planner.create_plan(spec)
        self.assertGreater(len(plan.database_migration_steps), 0)
        self.assertGreater(len(plan.api_steps), 0)
        self.assertGreater(len(plan.frontend_steps), 0)
        self.assertGreater(len(plan.execution_order), 0)
        self.assertGreater(plan.confidence, 0)
