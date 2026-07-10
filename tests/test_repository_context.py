import unittest
from core.autonomous_repository.repository_context import RepositoryContextDetector

class TestRepositoryContext(unittest.TestCase):
    def setUp(self):
        self.detector = RepositoryContextDetector()

    def test_build_context(self):
        ctx = self.detector.build_context()
        self.assertGreater(len(ctx.frameworks), 0)
        self.assertIn("FastAPI", ctx.frameworks)
        self.assertGreater(len(ctx.tests), 0)
        self.assertGreater(len(ctx.reusable_components), 0)
