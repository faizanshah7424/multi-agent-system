import unittest
from core.feature_engine.feature_parser import FeatureParser

class TestFeatureParser(unittest.TestCase):
    def setUp(self):
        self.parser = FeatureParser()

    def test_parse_auth_requirement(self):
        spec = self.parser.parse_requirement("Build a Login System")
        self.assertEqual(len(spec.goals), 1)
        self.assertIn("authentication", spec.goals[0].lower())
        self.assertGreater(len(spec.functional_requirements), 0)
        self.assertGreater(len(spec.apis), 0)

    def test_parse_inventory_requirement(self):
        spec = self.parser.parse_requirement("Create an Inventory Module")
        self.assertEqual(len(spec.goals), 1)
        self.assertIn("inventory", spec.goals[0].lower())
