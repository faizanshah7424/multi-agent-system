import unittest
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import patch

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.memory.interface import IEngineeringMemoryEngine
from core.memory.engine import (
    EngineeringMemoryEngine,
    DBEngineeringMemory,
    DBEngineeringConvention,
)
from core.memory.compaction import MemoryCompactionManager
from core.database import get_db_session
from core.memory import VectorMemoryIndex


def mock_get_embedding(text: str) -> list:
    """Mock embedding generation mapping inputs to static test vectors."""
    t = text.lower()
    if "vanilla css" in t or "css" in t:
        return [1.0, 0.1, 0.0]
    elif "valueerror" in t:
        return [0.0, 1.0, 0.0]
    else:
        return [0.5, 0.5, 0.5]


class TestEngineeringMemoryEngine(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.engine = DIContainer.get("memory_engine")
        self.compactor = MemoryCompactionManager()
        self.task_id = "test_sprint9_task"

        # Cleanup memory records from SQLite
        with get_db_session() as session:
            session.query(DBEngineeringMemory).filter(
                DBEngineeringMemory.task_id == self.task_id
            ).delete()
            session.query(DBEngineeringConvention).filter(
                DBEngineeringConvention.task_id == self.task_id
            ).delete()

        # Clear vector indexes
        VectorMemoryIndex("eme_fixes_index").clear()
        VectorMemoryIndex("eme_conventions_index").clear()

    def test_di_registration(self) -> None:
        self.assertTrue(isinstance(self.engine, EngineeringMemoryEngine))

    def test_verbose_log_compaction(self) -> None:
        verbose_trace = (
            "Traceback (most recent call last):\n"
            '  File "core/di.py", line 15, in get\n'
            '    raise ValueError("Not found")\n'
            "E   ValueError: Not found\n"
            "\n"
            "tests/test_di.py:10: ValueError"
        )
        compacted = self.compactor.compact_log(verbose_trace)
        self.assertIsNotNone(compacted)
        self.assertNotIn("Traceback", compacted)
        self.assertIn('File "core/di.py"', compacted)
        self.assertIn("E   ValueError: Not found", compacted)

    @patch("core.llm.get_embedding", side_effect=mock_get_embedding)
    def test_record_fix_and_jaccard_overlap_retrieval(self, mock_embed) -> None:
        # 1. Record two separate fixes
        self.engine.record_fix(
            task_id=self.task_id,
            step_id=1,
            file_path="core/di.py",
            error_msg="ValueError: Dependency interface not registered inside container.",
            applied_fix="Add DIContainer.register(Interface, Concrete) inside di_setup.py",
        )

        self.engine.record_fix(
            task_id=self.task_id,
            step_id=2,
            file_path="main.py",
            error_msg="ImportError: No module named fastapi in global scope.",
            applied_fix="Run pip install fastapi to download package dependencies.",
        )

        # 2. Query with a similar ValueError traceback
        query_log = "ValueError: Dependency interface IAgentExecutor not registered"
        similar = self.engine.retrieve_similar_fixes(query_log, limit=1)

        self.assertEqual(len(similar), 1)
        # Check that it matched the ValueError record rather than the ImportError one
        self.assertEqual(similar[0]["file_path"], "core/di.py")
        self.assertIn("di_setup.py", similar[0]["applied_fix"])
        self.assertGreater(similar[0]["score"], 0.1)

        # 3. Query with unrelated string (should return empty or low overlap)
        unrelated_query = "ZeroDivisionError: division by zero"
        similar_unrelated = self.engine.retrieve_similar_fixes(unrelated_query, limit=1)
        self.assertEqual(len(similar_unrelated), 0)

    def test_memory_database_compaction_utility(self) -> None:
        # Record a verbose traceback directly
        with get_db_session() as session:
            record = DBEngineeringMemory(
                task_id=self.task_id,
                step_id=1,
                file_path="app.py",
                error_msg='File "app.py", line 10\nSyntaxError: invalid syntax\n',
                applied_fix="Fixed syntax",
            )
            session.add(record)

        # Run compaction
        self.engine.compact_memories()

        # Assert log was converted to single compacted line
        with get_db_session() as session:
            db_record = (
                session.query(DBEngineeringMemory)
                .filter(DBEngineeringMemory.task_id == self.task_id)
                .first()
            )
            self.assertIsNotNone(db_record)
            self.assertNotIn("\n", db_record.error_msg)
            self.assertIn('File "app.py"', db_record.error_msg)

    @patch("core.llm.get_embedding", side_effect=mock_get_embedding)
    def test_record_and_retrieve_convention(self, mock_embed) -> None:
        # 1. Record styling conventions
        self.engine.record_convention(
            task_id=self.task_id,
            file_path="dashboard/src/components/HospitalView.tsx",
            convention_name="Vanilla CSS Requirement",
            description="Use only custom Vanilla CSS for styling. Avoid TailwindCSS unless explicitly asked.",
            category="style",
        )

        self.engine.record_convention(
            task_id=self.task_id,
            file_path="core/di_setup.py",
            convention_name="Dependency Injection Container",
            description="Always register interface and concrete pairs in the di_setup registry.",
            category="architecture",
        )

        # 2. Retrieve styling convention
        styling_matches = self.engine.retrieve_similar_conventions(
            query="custom styling with css",
            file_path="dashboard/src/components/HospitalView.tsx",
            limit=1,
        )
        self.assertEqual(len(styling_matches), 1)
        self.assertEqual(
            styling_matches[0]["convention_name"], "Vanilla CSS Requirement"
        )
        self.assertEqual(styling_matches[0]["category"], "style")
        self.assertGreater(styling_matches[0]["score"], 0.2)

        # 3. Retrieve DI convention
        di_matches = self.engine.retrieve_similar_conventions(
            query="dependency injection registry", file_path="core/di_setup.py", limit=1
        )
        self.assertEqual(len(di_matches), 1)
        self.assertEqual(
            di_matches[0]["convention_name"], "Dependency Injection Container"
        )

    @patch("core.llm.get_embedding", side_effect=mock_get_embedding)
    def test_hybrid_fixes_retrieval(self, mock_embed) -> None:
        # 1. Record fix
        self.engine.record_fix(
            task_id=self.task_id,
            step_id=1,
            file_path="core/di.py",
            error_msg="ValueError: Dependency interface not registered inside container.",
            applied_fix="Add DIContainer.register(Interface, Concrete) inside di_setup.py",
        )

        # 2. Query using ValueError (should match and retrieve using hybrid search)
        similar = self.engine.retrieve_similar_fixes(
            "ValueError in dependency setup", limit=1
        )
        self.assertEqual(len(similar), 1)
        self.assertEqual(similar[0]["file_path"], "core/di.py")
        self.assertGreater(similar[0]["score"], 0.1)
