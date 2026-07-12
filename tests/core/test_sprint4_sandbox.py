import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.workspace.interface import (
    IWorkspaceManager,
    IWorkspaceSessionManager,
    FileChange,
)
from core.workspace.workspace_manager import WorkspaceManager
from core.workspace.session_manager import WorkspaceSessionManager, DBSessionState
from core.sandbox.interface import ISandbox
from core.sandbox.local_sandbox import LocalProcessSandbox
from core.database import get_db_session


class TestWorkspaceAndSandbox(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.workspace_mgr = DIContainer.get(IWorkspaceManager)
        self.session_mgr = DIContainer.get(IWorkspaceSessionManager)
        self.sandbox_factory = DIContainer.get("sandbox_factory")
        self.task_id = "test_sprint4_task"

        # Cleanup any stagnant session
        with get_db_session() as session:
            session.query(DBSessionState).filter(
                DBSessionState.task_id == self.task_id
            ).delete()

    def tearDown(self) -> None:
        # Tear down session and worktree
        try:
            self.session_mgr.end_session(self.task_id)
        except Exception:
            pass

    def test_di_registrations(self) -> None:
        self.assertTrue(isinstance(self.workspace_mgr, WorkspaceManager))
        self.assertTrue(isinstance(self.session_mgr, WorkspaceSessionManager))
        self.assertTrue(callable(self.sandbox_factory))

    def test_workspace_transactional_lifecycle(self) -> None:
        import uuid

        unique_file = f"sprint4_test_{uuid.uuid4().hex[:8]}.txt"

        # 1. Create Workspace
        path = self.workspace_mgr.create_workspace(self.task_id)
        self.assertTrue(Path(path).exists())
        self.assertTrue(Path(path).is_dir())

        # 2. Stage Changes
        change_add = FileChange(
            file_path=unique_file, action="add", content="Hello from Sprint 4!"
        )
        self.workspace_mgr.stage_changes(self.task_id, [change_add])

        target_file = Path(path) / unique_file
        self.assertTrue(target_file.exists())
        self.assertEqual(
            target_file.read_text(encoding="utf-8"), "Hello from Sprint 4!"
        )

        # 3. Generate Diff
        diff = self.workspace_mgr.generate_diff(self.task_id)
        self.assertIn("Hello from Sprint 4!", diff)

        # 4. Commit and Merge
        success = self.workspace_mgr.commit_and_merge(self.task_id)
        self.assertTrue(success)

        # 5. Destroy Workspace
        self.workspace_mgr.destroy_workspace(self.task_id)
        self.assertFalse(Path(path).exists())

    def test_workspace_session_manager(self) -> None:
        # Start session
        state = self.session_mgr.start_session(self.task_id)
        self.assertEqual(state.task_id, self.task_id)
        self.assertEqual(state.git_branch, f"task_{self.task_id}")
        self.assertTrue(Path(state.workspace_path).exists())

        # Verify database record exists
        with get_db_session() as session:
            record = (
                session.query(DBSessionState)
                .filter(DBSessionState.task_id == self.task_id)
                .first()
            )
            self.assertIsNotNone(record)
            self.assertEqual(record.workspace_path, state.workspace_path)

        # End session
        self.session_mgr.end_session(self.task_id)

        # Verify DB record is removed and folder cleaned up
        with get_db_session() as session:
            record = (
                session.query(DBSessionState)
                .filter(DBSessionState.task_id == self.task_id)
                .first()
            )
            self.assertIsNone(record)
        self.assertFalse(Path(state.workspace_path).exists())

    def test_local_process_sandbox_execution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sandbox = self.sandbox_factory(temp_dir, self.task_id)
            sandbox.start()

            # Execute simple command
            res = sandbox.execute(["python", "-c", "print('hello sandbox')"])
            self.assertEqual(res.exit_code, 0)
            self.assertIn("hello sandbox", res.stdout)
            self.assertFalse(res.timeout_exceeded)

            # Test timeout exceeded
            res_timeout = sandbox.execute(
                ["python", "-c", "import time; time.sleep(10)"], timeout=1.0
            )
            self.assertTrue(res_timeout.timeout_exceeded)

            # Test Copy In and Copy Out
            local_src = Path(temp_dir) / "local_test_file.txt"
            local_src.write_text("content to sandbox", encoding="utf-8")

            # Copy file in
            sandbox.copy_in(str(local_src), "sandbox_test_file.txt")
            sandbox_file = Path(temp_dir) / "sandbox_test_file.txt"
            self.assertTrue(sandbox_file.exists())
            self.assertEqual(
                sandbox_file.read_text(encoding="utf-8"), "content to sandbox"
            )

            # Copy file out
            local_dest = Path(temp_dir) / "local_dest_file.txt"
            sandbox.copy_out("sandbox_test_file.txt", str(local_dest))
            self.assertTrue(local_dest.exists())
            self.assertEqual(
                local_dest.read_text(encoding="utf-8"), "content to sandbox"
            )

            sandbox.terminate()
