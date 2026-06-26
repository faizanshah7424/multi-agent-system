import os
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Override PERSIST_DIR env var to avoid touching real data
if not os.environ.get("PERSIST_DIR"):
    import tempfile
    os.environ["PERSIST_DIR"] = tempfile.mkdtemp()

temp_dir = os.environ["PERSIST_DIR"]

from config import settings
settings.persist_dir = temp_dir

from core.memory import MemoryItem, VectorMemoryIndex, MemoryConsolidator, SharedMemory
from tools.memory_tool import MemoryRecallTool, MemoryStoreTool
from api.app import app
from fastapi.testclient import TestClient

def mock_get_embedding(text: str) -> list:
    """Mock embedding generation mapping inputs to static test vectors."""
    t = text.lower()
    if "fastapi" in t:
        return [1.0, 0.1, 0.0]
    elif "pasta" in t:
        return [0.0, 0.1, 1.0]
    else:
        return [0.5, 0.5, 0.5]

class TestPersistentMemorySystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.persist_memory_dir = Path(temp_dir) / "memory"
        cls.persist_memory_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        from core.database import engine
        engine.dispose()

    def setUp(self):
        # Clear SQLite database tables instead of files
        from core.database import get_db_session, Task, TaskLog, AgentMessage, MemoryEntry, WorkflowExecution
        with get_db_session() as session:
            session.query(WorkflowExecution).delete()
            session.query(AgentMessage).delete()
            session.query(TaskLog).delete()
            session.query(MemoryEntry).delete()
            session.query(Task).delete()
            
        # Clear static memory index models
        VectorMemoryIndex("global_vector_index").clear()
        VectorMemoryIndex("test_vector_index").clear()

    @patch("core.llm.get_embedding", side_effect=mock_get_embedding)
    def test_vector_memory_index_operations(self, mock_embed):
        index = VectorMemoryIndex("test_vector_index")
        self.assertEqual(len(index.items), 0)
        
        # Add memories
        index.add_memory("How to build FastAPI APIs", {"category": "coding"})
        index.add_memory("How to make delicious pasta", {"category": "cooking"})
        
        self.assertEqual(len(index.items), 2)
        
        # Search for FastAPI - should return FastAPI memory first
        results = index.search("fastapi queries", limit=1)
        self.assertEqual(len(results), 1)
        best_match, similarity = results[0]
        self.assertIn("FastAPI", best_match.text)
        self.assertEqual(best_match.metadata["category"], "coding")
        self.assertGreater(similarity, 0.8)

        # Clear index
        index.clear()
        self.assertEqual(len(index.items), 0)

    @patch("core.llm.get_embedding", side_effect=mock_get_embedding)
    def test_memory_recall_and_store_tools(self, mock_embed):
        # Store tool
        store_tool = MemoryStoreTool()
        res_store = store_tool.run(text="FastAPI route validation tips", metadata={"tag": "api"})
        self.assertIn("success", res_store.lower())

        # Recall tool
        recall_tool = MemoryRecallTool()
        res_recall = recall_tool.run(query="validation of fastapi", limit=1)
        self.assertIn("FastAPI route validation", res_recall)
        self.assertIn("api", res_recall)

    @patch("core.llm.get_embedding", side_effect=mock_get_embedding)
    @patch("core.llm.ask_llm", return_value="CONSOLIDATED ABSTRACT LEARNINGS: Use FastAPI with Pydantic for validation.")
    def test_memory_consolidation(self, mock_ask_llm, mock_embed):
        # 1. Create a dummy session with logs
        session_id = "test_consolidation_session"
        memory = SharedMemory(session_id=session_id)
        memory.update_status("completed")
        memory.add_log("researcher", "Looked at FastAPI docs.")
        memory.add_log("developer", "Created test endpoints.")
        memory.add_message("researcher", "developer", "Here are the API schemas.")
        
        # 2. Trigger consolidation
        consolidator = MemoryConsolidator()
        summary = consolidator.consolidate_session(session_id)
        self.assertIsNotNone(summary)
        self.assertIn("Use FastAPI with Pydantic", summary)

        # 3. Check it was added to vector index
        results = consolidator.vector_index.search("fastapi validation", limit=1)
        self.assertEqual(len(results), 1)
        best_match, _ = results[0]
        self.assertIn("Use FastAPI with Pydantic", best_match.text)
        self.assertEqual(best_match.metadata["session_id"], session_id)

    @patch("core.llm.get_embedding", side_effect=mock_get_embedding)
    @patch("core.llm.ask_llm", return_value="SUMMARY: fastapi details consolidated.")
    def test_api_memory_endpoints(self, mock_ask_llm, mock_embed):
        # Add memory item to the global index
        index = VectorMemoryIndex()
        index.add_memory("FastAPI deployment notes", {"env": "prod"})

        # Test search endpoint
        response = self.client.get("/memory/search", params={"query": "fastapi deploy", "limit": 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["metadata"]["env"], "prod")
        self.assertIn("FastAPI", data[0]["text"])

        # Test consolidate endpoint
        session_id = "api_consolidate_session"
        mem = SharedMemory(session_id=session_id)
        mem.add_log("system", "Workflow completed successfully.")
        mem.save()

        response = self.client.post("/memory/consolidate", params={"session_id": session_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["session_id"], session_id)
        self.assertIn("fastapi details consolidated", data["consolidated_summary"])

if __name__ == "__main__":
    unittest.main()
