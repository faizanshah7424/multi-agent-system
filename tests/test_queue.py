import os
import tempfile
import unittest
import shutil
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Override PERSIST_DIR env var to avoid touching real data
if not os.environ.get("PERSIST_DIR"):
    import tempfile
    os.environ["PERSIST_DIR"] = tempfile.mkdtemp()

temp_dir = os.environ["PERSIST_DIR"]

from config import settings
settings.persist_dir = temp_dir

from core.queue import (
    TaskStatus, TaskModel, TaskQueue, TaskManager, WorkerPool,
    task_queue, task_manager, worker_pool
)
from api.app import app
from fastapi.testclient import TestClient

class TestTaskQueueAndWorkerSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Patch ManagerAgent globally during tests to prevent real Gemini/workflow execution
        cls.mock_manager_patcher = patch("agents.manager.ManagerAgent")
        cls.mock_manager_class = cls.mock_manager_patcher.start()
        
        # Define mock behavior
        cls.mock_instance = MagicMock()
        cls.mock_instance.memory.state.status = "completed"
        cls.mock_manager_class.return_value = cls.mock_instance
        
        cls.client = TestClient(app)
        cls.persist_tasks_dir = Path(temp_dir) / "tasks"
        cls.persist_tasks_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Re-ensure worker threads are stopped
        worker_pool.shutdown(timeout=1.0)
        cls.mock_manager_patcher.stop()

    def setUp(self):
        self.mock_instance.reset_mock()
        self.mock_instance.memory.state.status = "completed"
        
        # Clear database tables instead of files
        from core.database import get_db_session, Task, TaskLog, AgentMessage, WorkflowExecution, WorkerHeartbeat
        with get_db_session() as session:
            session.query(WorkflowExecution).delete()
            session.query(AgentMessage).delete()
            session.query(TaskLog).delete()
            session.query(Task).delete()
            session.query(WorkerHeartbeat).delete()
            
        # Clear queue
        task_queue.clear()

    def test_task_model_validation(self):
        task = TaskModel(
            task_id="test_1",
            payload={"task": "Write hello world in python"},
            status=TaskStatus.PENDING
        )
        self.assertEqual(task.task_id, "test_1")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.retry_count, 0)

    def test_task_queue_operations(self):
        q = TaskQueue()
        self.assertEqual(q.qsize(), 0)
        q.put("task_a")
        q.put("task_b")
        self.assertEqual(q.qsize(), 2)
        
        item = q.get(timeout=0.1)
        self.assertEqual(item, "task_a")
        q.task_done()
        
        q.clear()
        self.assertEqual(q.qsize(), 0)

    def test_task_manager_persistence(self):
        task = task_manager.create_task(
            task_id="task_persist_test",
            payload={"task": "Run tests"},
            user_id="user_123"
        )
        self.assertEqual(task.status, TaskStatus.QUEUED)
        
        # Load from disk
        loaded = task_manager.get_task("task_persist_test")
        self.assertEqual(loaded.task_id, "task_persist_test")
        self.assertEqual(loaded.user_id, "user_123")
        self.assertEqual(loaded.payload["task"], "Run tests")

    def test_task_manager_cancellation(self):
        task = task_manager.create_task(
            task_id="task_cancel_test",
            payload={"task": "Cancel me"}
        )
        self.assertEqual(task.status, TaskStatus.QUEUED)
        
        task_manager.cancel_task("task_cancel_test")
        loaded = task_manager.get_task("task_cancel_test")
        self.assertEqual(loaded.status, TaskStatus.CANCELLED)

    def test_task_manager_recovery(self):
        # Create a task and manually save it with RUNNING status on disk
        task = TaskModel(
            task_id="task_recovery_test",
            payload={"task": "Recover me"},
            status=TaskStatus.RUNNING
        )
        task_manager.save_task(task)
        
        # Run recovery
        recovered_count = task_manager.recover_tasks()
        self.assertEqual(recovered_count, 1)
        
        # Verify status is reset to QUEUED
        loaded = task_manager.get_task("task_recovery_test")
        self.assertEqual(loaded.status, TaskStatus.QUEUED)

    def test_retry_system_transient_failure(self):
        task = TaskModel(
            task_id="task_retry_test",
            payload={"task": "Trigger transient failure"},
            status=TaskStatus.RUNNING,
            retry_count=0
        )
        task_manager.save_task(task)
        
        # Handle transient failure (e.g., Gemini rate limit 429)
        task_manager.handle_task_failure(task, "Gemini API failure: ResourceExhausted 429 rate limit exceeded")
        
        loaded = task_manager.get_task("task_retry_test")
        self.assertEqual(loaded.status, TaskStatus.RETRYING)
        self.assertEqual(loaded.retry_count, 1)
        self.assertIn("429", loaded.error)

    def test_retry_system_permanent_failure(self):
        task = TaskModel(
            task_id="task_fail_test",
            payload={"task": "Trigger permanent failure"},
            status=TaskStatus.RUNNING,
            retry_count=0
        )
        task_manager.save_task(task)
        
        # Handle non-transient failure
        task_manager.handle_task_failure(task, "SyntaxError: invalid syntax")
        
        loaded = task_manager.get_task("task_fail_test")
        self.assertEqual(loaded.status, TaskStatus.FAILED)
        self.assertEqual(loaded.retry_count, 0)
        self.assertEqual(loaded.error, "SyntaxError: invalid syntax")

    def test_worker_execution_flow(self):
        # Put task in queue and run execution
        task = task_manager.create_task(
            task_id="task_exec_test",
            payload={"task": "Mocked workflow run"}
        )
        
        # Run execution directly to avoid thread race conditions in this unittest
        stop_event = MagicMock()
        task_manager.execute_task(task.task_id, stop_event)
        
        loaded = task_manager.get_task("task_exec_test")
        self.assertEqual(loaded.status, TaskStatus.COMPLETED)
        self.mock_instance.execute.assert_called_with("Mocked workflow run")

    def test_fastapi_endpoints_tasks(self):
        # 1. Create a task via API
        payload = {
            "task_id": "api_test_task",
            "task_type": "workflow",
            "payload": {"task": "Build website"}
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["task_id"], "api_test_task")
        self.assertEqual(data["status"], "QUEUED")
        
        # 2. Get task via API
        response = self.client.get("/tasks/api_test_task")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "QUEUED")
        
        # 3. Get all tasks via API
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 1)
        
        # 4. Get queue status
        response = self.client.get("/queue/status")
        self.assertEqual(response.status_code, 200)
        status_data = response.json()
        self.assertIn("queue_size", status_data)
        self.assertIn("worker_count", status_data)
        self.assertIn("tasks_by_status", status_data)
        self.assertGreaterEqual(status_data["tasks_by_status"].get("QUEUED", 0), 1)

        # 5. Delete task via API (Cancellation)
        response = self.client.delete("/tasks/api_test_task")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        
        # Check task is now cancelled
        response = self.client.get("/tasks/api_test_task")
        self.assertEqual(response.json()["status"], "CANCELLED")

    def test_fastapi_endpoints_workers(self):
        # Register workers in database to mock active worker processes
        from core.database import get_db_session
        from core.repositories import WorkerRepository
        
        with get_db_session() as session:
            repo = WorkerRepository(session)
            repo.register_worker("worker_test_1", "localhost", 1001)
            repo.register_worker("worker_test_2", "localhost", 1002)
            
        try:
            response = self.client.get("/workers")
            self.assertEqual(response.status_code, 200)
            workers = response.json()
            self.assertEqual(len(workers), 2)
            for w in workers:
                self.assertIn("worker_name", w)
                self.assertEqual(w["worker_name"], w["worker_id"])
                self.assertTrue(w["is_alive"])
                self.assertTrue(w["is_healthy"])
        finally:
            with get_db_session() as session:
                repo = WorkerRepository(session)
                repo.remove_worker("worker_test_1")
                repo.remove_worker("worker_test_2")

if __name__ == "__main__":
    unittest.main()
