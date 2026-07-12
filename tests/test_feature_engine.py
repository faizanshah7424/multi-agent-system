import unittest
import tempfile
import os
from unittest.mock import MagicMock
from core.knowledge.engine import InMemoryGraphEngine
from core.knowledge.entities import Node, NodeType
from core.feature_engine.feature_engine import AutonomousFeatureEngine
from core.feature_engine.feature_memory import FeatureMemory
from core.feature_engine.migration_manager import MigrationManager


class TestFeatureEngine(unittest.TestCase):
    def setUp(self):
        self.graph = InMemoryGraphEngine()
        self.engine = AutonomousFeatureEngine(self.graph)

        # Isolate database file to avoid locking/contention issues in parallel tests
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)

        self.engine.memory = FeatureMemory(db_path=self.temp_db_path)
        self.engine.migration_mgr = MigrationManager(db_path=self.temp_db_path)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass

    def test_develop_feature_success(self):
        self.graph.nodes["core/database.py"] = Node(
            id="core/database.py", type=NodeType.FILE, name="database.py"
        )
        self.graph.nodes["core/auth/security.py"] = Node(
            id="core/auth/security.py", type=NodeType.FILE, name="security.py"
        )

        apply_mock = MagicMock()
        res = self.engine.develop_feature(
            "Build a Login System", apply_feature_fn=apply_mock
        )

        self.assertTrue(res["success"])
        self.assertIsNone(res["failures"])
        self.assertIsNotNone(res["execution_id"])
        self.assertEqual(res["requirement"], "Build a Login System")
        apply_mock.assert_called_once()

    def test_develop_feature_failure_rollback(self):
        res = self.engine.develop_feature("Build a Login System")
        self.assertFalse(res["success"])
        self.assertIsNotNone(res["failures"])
        self.assertEqual(res["requirement"], "Build a Login System")
