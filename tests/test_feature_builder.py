import unittest
from core.feature_engine.feature_parser import FeatureParser
from core.feature_engine.feature_planner import FeaturePlanner
from core.feature_engine.feature_builder import FeatureBuilder


class TestFeatureBuilder(unittest.TestCase):
    def setUp(self):
        self.parser = FeatureParser()
        self.planner = FeaturePlanner()
        self.builder = FeatureBuilder()

    def test_build_feature_inventory(self):
        spec = self.parser.parse_requirement("Create an Inventory Module")
        plan = self.planner.create_plan(spec)
        artifacts = self.builder.build_feature(spec, plan)
        self.assertIn("InventoryManager", artifacts["backend"])
        self.assertIn("inventory_items", artifacts["database"])
        self.assertIn("InventoryView", artifacts["frontend"])
        self.assertIn("test_inventory_manager", artifacts["tests"])
