import os
import unittest
from core.autonomous_repository.repository_memory import (
    RepositoryMemory,
    RepositoryRecord,
)


class TestRepositoryMemory(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_repo_memory.db"
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass
        self.memory = RepositoryMemory(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_add_and_list_records(self):
        record = RepositoryRecord(
            id="rec_1",
            goal="Create Login System",
            repo_snapshot={"tests": 12},
            generated_files=["core/auth.py"],
            confidence=0.90,
            validation_results={"success": True},
            rollback_snapshot="snap_1",
            execution_duration_seconds=1.23,
        )
        self.memory.add_record(record)

        recs = self.memory.list_records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].goal, "Create Login System")
        self.assertEqual(recs[0].confidence, 0.90)
        self.assertTrue(recs[0].validation_results.get("success"))
