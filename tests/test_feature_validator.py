import unittest
from core.knowledge.engine import InMemoryGraphEngine
from core.knowledge.entities import Node, NodeType
from core.feature_engine.feature_validator import FeatureValidator

class TestFeatureValidator(unittest.TestCase):
    def setUp(self):
        self.graph = InMemoryGraphEngine()
        self.validator = FeatureValidator(self.graph)

    def test_validate_feature_success(self):
        self.graph.nodes["core/database.py"] = Node(
            id="core/database.py",
            type=NodeType.FILE,
            name="database.py"
        )
        res = self.validator.validate_feature(["core/database.py"])
        self.assertTrue(res["success"])
        self.assertTrue(res["results"]["graph_integrity"])

    def test_validate_feature_missing_graph_node(self):
        res = self.validator.validate_feature(["core/missing.py"])
        self.assertFalse(res["success"])
        self.assertFalse(res["results"]["graph_integrity"])
