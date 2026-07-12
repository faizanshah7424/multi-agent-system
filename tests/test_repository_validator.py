import unittest
from core.knowledge.engine import InMemoryGraphEngine
from core.autonomous_repository.repository_validator import RepositoryValidator


class TestRepositoryValidator(unittest.TestCase):
    def setUp(self):
        self.graph = InMemoryGraphEngine()
        self.validator = RepositoryValidator(self.graph)

    def test_validate_repository(self):
        res = self.validator.validate_repository(["core/database.py"])
        self.assertTrue(res["success"])
        self.assertTrue(res["results"]["kg_validation"])
        self.assertTrue(res["results"]["formatting"])
