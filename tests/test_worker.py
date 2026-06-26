import os
import time
import unittest
import threading
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from core.database import get_db_session, Task, TaskLog, WorkerHeartbeat, init_db
from core.repositories import TaskRepository, WorkerRepository
from core.worker import WorkerRuntime
from core.queue import task_manager

class TestWorkerSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override PERSIST_DIR env var to avoid touching real data
        if not os.environ.get("PERSIST_DIR"):
            import tempfile
            os.environ["PERSIST_DIR"] = tempfile.mkdtemp()
        init_db()

    def setUp(self):
        # Clear database tables before each test
        with get_db_session() as session:
            session.query(TaskLog).delete()
            session.query(Task).delete()
            session.query(WorkerHeartbeat).delete()

    def test_worker_registration_and_heartbeat(self):
        worker = WorkerRuntime(worker_id="test_worker_1", poll_interval=0.1)
        
        # Verify initial registration
        with get_db_session() as session:
            w_repo = WorkerRepository(session)
            worker_db = session.query(WorkerHeartbeat).filter_by(worker_id="test_worker_1").first()
            self.assertIsNone(worker_db)
            
            # Manually register
            w_repo.register_worker(worker.worker_id, worker.hostname, worker.pid)
            worker_db = session.query(WorkerHeartbeat).filter_by(worker_id="test_worker_1").first()
            self.assertIsNotNone(worker_db)
            self.assertEqual(worker_db.status, "IDLE")
            self.assertEqual(worker_db.pid, worker.pid)

            # Update heartbeat
            w_repo.update_heartbeat(worker.worker_id, "RUNNING", "task_abc")
            worker_db = session.query(WorkerHeartbeat).filter_by(worker_id="test_worker_1").first()
            self.assertEqual(worker_db.status, "RUNNING")
            self.assertEqual(worker_db.active_task_id, "task_abc")

    def test_stale_worker_recovery(self):
        # 1. Create a stale worker and a task claimed by it
        with get_db_session() as session:
            # Register worker
            w_repo = WorkerRepository(session)
            w_repo.register_worker("stale_worker", "localhost", 9999)
            
            # Manually backdate heartbeat
            worker_db = session.query(WorkerHeartbeat).filter_by(worker_id="stale_worker").first()
            worker_db.last_seen = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=30)
            worker_db.status = "RUNNING"
            session.add(worker_db)
            
            # Create running task claimed by this worker
            t_repo = TaskRepository(session)
            task = t_repo.create_task("stale_task", {"task": "Do work"})
            task.status = "RUNNING"
            task.claimed_by = "stale_worker"
            task.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            t_repo.save_task(task)
            
        # 2. Run recovery check
        with get_db_session() as session:
            t_repo = TaskRepository(session)
            recovered = t_repo.recover_stale_tasks(max_age_seconds=15)
            
        # 3. Assertions
        self.assertEqual(recovered, ["stale_task"])
        
        with get_db_session() as session:
            # Task must be requeued
            task_db = session.query(Task).filter_by(task_id="stale_task").first()
            self.assertEqual(task_db.status, "QUEUED")
            self.assertIsNone(task_db.claimed_by)
            self.assertEqual(task_db.retry_count, 1)
            self.assertIn("heartbeat timeout", task_db.error)
            
            # Worker must be marked shutdown
            worker_db = session.query(WorkerHeartbeat).filter_by(worker_id="stale_worker").first()
            self.assertEqual(worker_db.status, "SHUTDOWN")

    @patch("agents.manager.ManagerAgent")
    def test_graceful_shutdown(self, mock_manager):
        # Set up mock agent behavior
        mock_instance = MagicMock()
        mock_instance.memory.state.status = "completed"
        mock_manager.return_value = mock_instance
        
        worker = WorkerRuntime(worker_id="graceful_worker", poll_interval=0.1)
        
        # Create a task in SQLite
        with get_db_session() as session:
            t_repo = TaskRepository(session)
            t_repo.create_task("graceful_task", {"task": "Graceful shutdown test"})
            
        # Start worker in a separate thread
        worker_thread = threading.Thread(target=worker.start)
        worker_thread.start()
        
        # Wait a short moment to ensure the task is claimed and executing
        time.sleep(0.3)
        
        # Trigger shutdown
        worker.shutdown_event.set()
        
        # Wait for thread to exit
        worker_thread.join(timeout=5)
        
        # Check task completion and worker status
        with get_db_session() as session:
            task_db = session.query(Task).filter_by(task_id="graceful_task").first()
            self.assertEqual(task_db.status, "COMPLETED")
            
            worker_db = session.query(WorkerHeartbeat).filter_by(worker_id="graceful_worker").first()
            self.assertEqual(worker_db.status, "SHUTDOWN")

    @patch("agents.manager.ManagerAgent")
    def test_multi_worker_concurrency_1_worker(self, mock_manager):
        self._run_multi_worker_load_test(mock_manager, num_workers=1, num_tasks=5)

    @patch("agents.manager.ManagerAgent")
    def test_multi_worker_concurrency_2_workers(self, mock_manager):
        self._run_multi_worker_load_test(mock_manager, num_workers=2, num_tasks=10)

    @patch("agents.manager.ManagerAgent")
    def test_multi_worker_concurrency_5_workers(self, mock_manager):
        self._run_multi_worker_load_test(mock_manager, num_workers=5, num_tasks=15)

    def _run_multi_worker_load_test(self, mock_manager, num_workers: int, num_tasks: int):
        # Configure mock ManagerAgent to sleep slightly to simulate work and allow actual thread contention
        def mock_execute(prompt):
            time.sleep(0.02)
        
        mock_instance = MagicMock()
        mock_instance.execute.side_effect = mock_execute
        mock_instance.memory.state.status = "completed"
        mock_manager.return_value = mock_instance
        
        # 1. Enqueue tasks
        task_ids = []
        with get_db_session() as session:
            t_repo = TaskRepository(session)
            for i in range(num_tasks):
                task_id = f"concurrency_task_{i}"
                t_repo.create_task(task_id, {"task": f"Test task {i}"})
                task_ids.append(task_id)

        # 2. Spin up concurrent worker threads
        workers = []
        threads = []
        for i in range(num_workers):
            w = WorkerRuntime(worker_id=f"concurrent_worker_{i}", concurrency=2, poll_interval=0.05)
            workers.append(w)
            t = threading.Thread(target=w.start)
            threads.append(t)
            t.start()

        # 3. Wait for all tasks to be completed
        start_time = time.time()
        timeout = 10.0
        all_completed = False
        
        while time.time() - start_time < timeout:
            with get_db_session() as session:
                incomplete = session.query(Task).filter(Task.status.in_(["QUEUED", "RUNNING"])).count()
                if incomplete == 0:
                    all_completed = True
                    break
            time.sleep(0.1)

        # 4. Shutdown workers and join threads
        for w in workers:
            w.shutdown_event.set()
        for t in threads:
            t.join(timeout=2)

        # 5. Assertions
        self.assertTrue(all_completed, f"Timed out waiting for tasks to complete. {incomplete} tasks remaining.")
        
        with get_db_session() as session:
            tasks = session.query(Task).filter(Task.task_id.in_(task_ids)).all()
            self.assertEqual(len(tasks), num_tasks)
            for task in tasks:
                self.assertEqual(task.status, "COMPLETED", f"Task {task.task_id} status is {task.status}")
                self.assertIsNotNone(task.claimed_by)
                
                # Check task logs to verify it was claimed only once
                logs = session.query(TaskLog).filter_by(task_id=task.task_id).all()
                claim_logs = [log for log in logs if "claimed by worker" in log.message]
                self.assertEqual(len(claim_logs), 1, f"Task {task.task_id} was claimed {len(claim_logs)} times!")

if __name__ == "__main__":
    unittest.main()
