import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional
from core.workspace.interface import IWorkspaceManager, FileChange


class WorkspaceManager(IWorkspaceManager):
    """
    Concrete Workspace Manager providing transactional isolation via Git worktrees.
    Dispatches CLI subprocesses to manage branch and worktree allocations outside the platform repository.
    """

    def __init__(self, main_repo_path: Optional[str] = None) -> None:
        if main_repo_path:
            self.main_repo_path = Path(main_repo_path).resolve()
        else:
            self.main_repo_path = Path(__file__).parent.parent.parent.resolve()

        # Place all worktree runs outside the platform repository in the temp directory
        self.worktrees_root = Path(tempfile.gettempdir()) / "codeorbit_runs"
        self.worktrees_root.mkdir(parents=True, exist_ok=True)

    def _get_worktree_path(self, task_id: str) -> Path:
        """
        Resolves the platform-specific isolated workspace path for a given task.
        Target structure: /tmp/codeorbit_runs/{task_id}/workspace
        """
        return self.worktrees_root / task_id / "workspace"

    def _run_git(self, args: List[str], cwd: Optional[Path] = None) -> str:
        target_cwd = cwd or self.main_repo_path
        res = subprocess.run(
            ["git"] + args,
            cwd=str(target_cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode != 0:
            raise RuntimeError(
                f"Git {' '.join(args)} failed in {target_cwd}: {res.stderr.strip()}"
            )
        return res.stdout.strip()

    def create_workspace(self, task_id: str) -> str:
        """
        Creates an isolated git worktree branch for a task and returns its local host path.
        """
        branch_name = f"task_{task_id}"
        worktree_path = self._get_worktree_path(task_id)

        # Resolve base branch to branch off of
        try:
            base_branch = self._run_git(["branch", "--show-current"])
        except Exception:
            base_branch = "main"

        # Check if the branch already exists, delete if stagnant
        try:
            self._run_git(["branch", "-D", branch_name])
        except Exception:
            pass

        # Check if directory already exists, clean up if stagnant
        if worktree_path.exists():
            try:
                self._run_git(["worktree", "remove", str(worktree_path), "--force"])
            except Exception:
                pass
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

        # Ensure parent runs folder exists
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Git worktree
        self._run_git(
            ["worktree", "add", "-b", branch_name, str(worktree_path), base_branch]
        )

        # Register workspace destruction in CleanupCoordinator
        from core.cleanup import CleanupCoordinator
        CleanupCoordinator.register_resource(
            task_id=task_id,
            resource_type="workspace",
            resource_identifier=str(worktree_path),
            cleanup_callable=lambda: self.destroy_workspace(task_id)
        )

        return str(worktree_path).replace("\\", "/")


    def stage_changes(self, task_id: str, changes: List[FileChange]) -> None:
        """
        Applies changes safely within the isolated branch.
        """
        worktree_path = self._get_worktree_path(task_id)
        if not worktree_path.exists():
            raise FileNotFoundError(
                f"Isolated worktree path does not exist: {worktree_path}"
            )

        for change in changes:
            file_path = worktree_path / change.file_path

            # Ensure parent directories exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if change.action in ("add", "modify"):
                file_path.write_text(change.content, encoding="utf-8")
            elif change.action == "delete":
                if file_path.exists():
                    if file_path.is_dir():
                        shutil.rmtree(file_path, ignore_errors=True)
                    else:
                        file_path.unlink()

        # Run Git add to stage changes in the worktree
        self._run_git(["add", "-A"], cwd=worktree_path)

    def generate_diff(self, task_id: str) -> str:
        """
        Retrieves the unified diff of the worktree against its parent branch.
        """
        worktree_path = self._get_worktree_path(task_id)
        if not worktree_path.exists():
            raise FileNotFoundError(
                f"Isolated worktree path does not exist: {worktree_path}"
            )

        # Git diff against current HEAD of the worktree branch
        try:
            return self._run_git(["diff", "HEAD"], cwd=worktree_path)
        except Exception as e:
            return f"Error generating diff: {str(e)}"

    def commit_and_merge(self, task_id: str) -> bool:
        """
        Applies task modifications back to origin branch and commits.
        """
        branch_name = f"task_{task_id}"
        worktree_path = self._get_worktree_path(task_id)
        if not worktree_path.exists():
            raise FileNotFoundError(
                f"Isolated worktree path does not exist: {worktree_path}"
            )

        try:
            # 1. Commit changes inside the isolated worktree
            status = self._run_git(["status", "--porcelain"], cwd=worktree_path)
            if status:
                self._run_git(
                    ["commit", "-m", f"Task completion commit: {task_id}"],
                    cwd=worktree_path,
                )

            # 2. Get active branch in main repository
            try:
                main_branch = self._run_git(["branch", "--show-current"])
            except Exception:
                main_branch = "main"

            # 3. Merge the task branch into the active main repository branch
            self._run_git(["merge", branch_name])
            return True
        except Exception as e:
            raise RuntimeError(f"Commit and merge transaction failed: {str(e)}")

    def destroy_workspace(self, task_id: str) -> None:
        """
        Tears down worktree mappings and cleans transient branches.
        """
        branch_name = f"task_{task_id}"
        worktree_path = self._get_worktree_path(task_id)

        # 1. Remove the Git worktree allocation
        if worktree_path.exists():
            try:
                self._run_git(["worktree", "remove", str(worktree_path), "--force"])
            except Exception:
                pass

            # Clean up directory leftovers if force remove didn't purge it
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

        # Clean up task-specific temp parent directory
        task_runs_dir = self.worktrees_root / task_id
        if task_runs_dir.exists():
            try:
                shutil.rmtree(task_runs_dir, ignore_errors=True)
            except Exception:
                pass

        # 2. Delete the transient branch
        try:
            self._run_git(["branch", "-D", branch_name])
        except Exception:
            pass

