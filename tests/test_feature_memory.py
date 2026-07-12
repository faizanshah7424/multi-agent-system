import unittest
import tempfile
import os
from core.feature_engine.feature_memory import FeatureMemory, FeatureRecord


class TestFeatureMemory(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.memory = FeatureMemory(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_list_records(self):
        record = FeatureRecord(
            id="feat_test_rec",
            feature_name="Build a Login System",
            execution_duration_seconds=3.24,
            files_modified=["core/database.py"],
            success_rate=1.0,
            confidence=0.98,
            lessons_learned=["JWT is clean"],
        )
        self.memory.add_record(record)

        records = self.memory.list_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, "feat_test_rec")
        self.assertEqual(records[0].success_rate, 1.0)
        self.assertIn("JWT is clean", records[0].lessons_learned)
