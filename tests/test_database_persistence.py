import os
import json
import tempfile
import shutil
import unittest
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Force the environment variable to a temporary location before importing settings
if not os.environ.get("PERSIST_DIR"):
    import tempfile

    os.environ["PERSIST_DIR"] = tempfile.mkdtemp()

temp_dir = os.environ["PERSIST_DIR"]

from config import settings

settings.persist_dir = temp_dir

from core.database import (
    Base,
    engine,
    get_db_session,
    init_db,
    Task as DBTask,
    TaskLog as DBTaskLog,
    AgentMessage as DBAgentMessage,
    MemoryEntry as DBMemoryEntry,
    WorkflowExecution as DBWorkflowExecution,
)
from core.repositories import TaskRepository, MemoryRepository, WorkflowRepository
from scripts.migrate_json_to_sqlite import migrate


class TestDatabasePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    @classmethod
    def tearDownClass(cls):
        # Dispose the engine connection pool so Windows releases lock on system.db
        engine.dispose()

    def setUp(self):
        # Clear database tables before every test
        with get_db_session() as session:
            session.query(DBWorkflowExecution).delete()
            session.query(DBAgentMessage).delete()
            session.query(DBTaskLog).delete()
            session.query(DBMemoryEntry).delete()
            session.query(DBTask).delete()

    def test_database_transaction_rollback(self):
        # Test transaction rollback on failure
        task_id = "test_rollback_id"

        try:
            with get_db_session() as session:
                repo = TaskRepository(session)
                repo.create_task(
                    task_id=task_id,
                    payload={"command": "test rollback"},
                    task_type="workflow",
                )
                # Intentionally raise an exception to trigger rollback
                raise RuntimeError("Simulated Database Transaction Failure")
        except RuntimeError:
            pass

        # Query outside the failed transaction context to confirm task is not persisted
        with get_db_session() as session:
            repo = TaskRepository(session)
            db_task = repo.get_task(task_id)
            self.assertIsNone(
                db_task, "Task should have been rolled back and not exist in DB."
            )

    def test_task_repository_operations(self):
        with get_db_session() as session:
            repo = TaskRepository(session)

            # Create
            task = repo.create_task(
                "task_repo_1", {"command": "hello"}, user_id="user_123"
            )
            self.assertEqual(task.task_id, "task_repo_1")
            self.assertEqual(task.status, "QUEUED")

            # Get
            fetched = repo.get_task("task_repo_1")
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.user_id, "user_123")

            # Update status
            fetched.status = "RUNNING"
            repo.save_task(fetched)

            # Verify update
            verified = repo.get_task("task_repo_1")
            self.assertEqual(verified.status, "RUNNING")

            # Add logs
            repo.add_log("task_repo_1", "researcher", "searching web")
            repo.add_log("task_repo_1", "developer", "writing code", "INFO")

            logs = repo.get_logs("task_repo_1")
            self.assertEqual(len(logs), 2)
            self.assertEqual(logs[0].source, "researcher")
            self.assertEqual(logs[1].message, "writing code")

            # Add agent chatter messages
            repo.add_message(
                "task_repo_1", "developer", "researcher", "Here are findings"
            )
            msgs = repo.get_messages("task_repo_1")
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0].role, "developer")
            self.assertEqual(msgs[0].agent_name, "researcher")
            self.assertEqual(msgs[0].content, "Here are findings")

            # Cancel task
            repo.cancel_task("task_repo_1")
            cancelled = repo.get_task("task_repo_1")
            self.assertEqual(cancelled.status, "CANCELLED")

    def test_memory_repository_operations(self):
        with get_db_session() as session:
            repo = MemoryRepository(session)

            # Add entries
            repo.add_entry(
                "test_index", "Memory text 1", {"tag": "a", "vector": [0.1, 0.2]}
            )
            repo.add_entry(
                "test_index", "Memory text 2", {"tag": "b", "vector": [0.3, 0.4]}
            )

            entries = repo.get_entries("test_index")
            self.assertEqual(len(entries), 2)
            self.assertEqual(
                entries[0].text, "Memory text 2"
            )  # sorted by desc timestamp

            # Clear entries
            repo.clear_entries("test_index")
            cleared_entries = repo.get_entries("test_index")
            self.assertEqual(len(cleared_entries), 0)

    def test_workflow_repository_operations(self):
        # Create parent task first
        with get_db_session() as session:
            task_repo = TaskRepository(session)
            task_repo.create_task("wf_task_1", {"command": "run workflow"})

            wf_repo = WorkflowRepository(session)
            wf_repo.create_step("wf_task_1", 1, "Plan", "Make a plan", "planner")
            wf_repo.create_step("wf_task_1", 2, "Code", "Develop code", "developer")

            steps = wf_repo.get_steps("wf_task_1")
            self.assertEqual(len(steps), 2)
            self.assertEqual(steps[0].name, "Plan")
            self.assertEqual(steps[1].assigned_agent, "developer")

            # Update step status
            wf_repo.update_step(
                "wf_task_1",
                1,
                "completed",
                result="Plan created successfully",
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            steps_updated = wf_repo.get_steps("wf_task_1")
            self.assertEqual(steps_updated[0].status, "completed")
            self.assertEqual(steps_updated[0].result, "Plan created successfully")

    def test_migration_layer(self):
        # Create temp folder structure for JSON mock files
        path = Path(temp_dir)
        tasks_dir = path / "tasks"
        memory_dir = path / "memory"

        tasks_dir.mkdir(parents=True, exist_ok=True)
        memory_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create a mock task JSON file
        task_data = {
            "task_id": "migrated_task_1",
            "user_id": "migrated_user",
            "task_type": "workflow",
            "payload": {"prompt": "Run migration test"},
            "status": "COMPLETED",
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "started_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "completed_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "retry_count": 1,
            "error": "None",
        }
        with open(tasks_dir / "migrated_task_1.json", "w", encoding="utf-8") as f:
            json.dump(task_data, f)

        # 2. Create a mock memory session state JSON file
        session_data = {
            "status": "completed",
            "task_id": "migrated_task_1",
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "logs": [
                {
                    "agent": "planner",
                    "message": "Planning steps",
                    "level": "INFO",
                    "timestamp": datetime.now(timezone.utc)
                    .replace(tzinfo=None)
                    .isoformat(),
                }
            ],
            "messages": [
                {
                    "sender": "planner",
                    "receiver": "developer",
                    "content": "Here is the plan",
                    "timestamp": datetime.now(timezone.utc)
                    .replace(tzinfo=None)
                    .isoformat(),
                }
            ],
            "data": {
                "workflow_steps": [
                    {
                        "step_id": 1,
                        "name": "Step 1",
                        "description": "First step description",
                        "assigned_agent": "planner",
                        "status": "completed",
                        "result": "Step 1 complete",
                        "started_at": datetime.now(timezone.utc)
                        .replace(tzinfo=None)
                        .isoformat(),
                        "completed_at": datetime.now(timezone.utc)
                        .replace(tzinfo=None)
                        .isoformat(),
                    }
                ]
            },
        }
        with open(path / "migrated_task_1.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f)

        # 3. Create a mock vector index JSON file
        vector_data = [
            {
                "text": "Migrated memory text",
                "metadata": {"category": "test"},
                "vector": [0.5, 0.5, 0.5],
                "timestamp": datetime.now(timezone.utc)
                .replace(tzinfo=None)
                .isoformat(),
            }
        ]
        with open(
            memory_dir / "migrated_vector_index.json", "w", encoding="utf-8"
        ) as f:
            json.dump(vector_data, f)

        # Run migration programmatically
        migrate()

        # Verify database imports
        with get_db_session() as session:
            task_repo = TaskRepository(session)
            migrated_task = task_repo.get_task("migrated_task_1")
            self.assertIsNotNone(migrated_task)
            self.assertEqual(migrated_task.user_id, "migrated_user")
            self.assertEqual(migrated_task.status, "COMPLETED")
            self.assertEqual(
                migrated_task.payload_json, {"prompt": "Run migration test"}
            )

            logs = task_repo.get_logs("migrated_task_1")
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].source, "planner")
            self.assertEqual(logs[0].message, "Planning steps")

            msgs = task_repo.get_messages("migrated_task_1")
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0].role, "developer")
            self.assertEqual(msgs[0].agent_name, "planner")
            self.assertEqual(msgs[0].content, "Here is the plan")

            wf_repo = WorkflowRepository(session)
            steps = wf_repo.get_steps("migrated_task_1")
            self.assertEqual(len(steps), 1)
            self.assertEqual(steps[0].name, "Step 1")
            self.assertEqual(steps[0].result, "Step 1 complete")

            mem_repo = MemoryRepository(session)
            memories = mem_repo.get_entries("migrated_vector_index")
            self.assertEqual(len(memories), 1)
            self.assertEqual(memories[0].text, "Migrated memory text")
            self.assertEqual(memories[0].metadata_json.get("category"), "test")
            self.assertEqual(memories[0].metadata_json.get("vector"), [0.5, 0.5, 0.5])

    def test_sqlite_concurrency_wal(self):
        # Verify that multi-threaded writes/reads do not throw lock errors
        errors = []
        task_id = "concurrent_task"

        # Precreate the task row to let threads write logs/messages safely
        with get_db_session() as session:
            repo = TaskRepository(session)
            repo.create_task(task_id, {"command": "concurrency testing"})

        def worker_thread(thread_idx):
            for i in range(20):
                try:
                    with get_db_session() as session:
                        repo = TaskRepository(session)
                        repo.add_log(
                            task_id, f"thread_{thread_idx}", f"log message {i}"
                        )
                        # Perform query to simulate mix workload
                        repo.get_task(task_id)
                        time.sleep(0.01)
                except Exception as e:
                    errors.append(e)

        threads = []
        for j in range(10):
            t = threading.Thread(target=worker_thread, args=(j,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(
            len(errors), 0, f"Concurrent threads raised SQLite errors: {errors}"
        )

        with get_db_session() as session:
            repo = TaskRepository(session)
            logs = repo.get_logs(task_id)
            # Expecting 10 threads * 20 entries = 200 logs
            self.assertEqual(len(logs), 200)


if __name__ == "__main__":
    unittest.main()
