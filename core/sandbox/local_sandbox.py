import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional
from core.sandbox.interface import ISandbox, SandboxExecutionResult


class LocalProcessSandbox(ISandbox):
    """
    Fallback Process Sandbox providing virtualenv-scoped execution boundaries on the local host.
    Utilized when Docker daemon is not available.
    """

    def __init__(self, workspace_path: str) -> None:
        self.workspace_path = Path(workspace_path).resolve()
        self._active_processes: List[subprocess.Popen] = []

    def start(self) -> None:
        """
        Ensures the workspace directory exists.
        """
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    def execute(self, cmd: List[str], timeout: float = 30.0) -> SandboxExecutionResult:
        """
        Executes a command inside the directory scope under standard timeouts.
        """
        if not self.workspace_path.exists():
            raise FileNotFoundError(
                f"Sandbox directory does not exist: {self.workspace_path}"
            )

        # Try to resolve virtual environment path if present inside workspace or main repo
        # On Windows, standard venv python is at venv/Scripts/python.exe
        venv_path = self.workspace_path / "venv" / "Scripts" / "python.exe"
        if not venv_path.exists():
            # Fall back to parent main repo venv if available
            parent_venv = (
                self.workspace_path.parent.parent / "venv" / "Scripts" / "python.exe"
            )
            if parent_venv.exists():
                venv_path = parent_venv

        executable_cmd = list(cmd)

        # Security Sanitization check
        for token in executable_cmd:
            # Block standalone shell operator tokens
            if token in [";", "&", "&&", "|", "||", ">", "<", ">>"]:
                return SandboxExecutionResult(
                    exit_code=-1,
                    stdout="",
                    stderr="Access Denied: Unsafe command token detected. Chaining and redirection operators are forbidden.",
                    duration_seconds=0.0,
                    timeout_exceeded=False,
                )
            # Block subexpression evals anywhere in the token
            if "`" in token or "$(" in token:
                return SandboxExecutionResult(
                    exit_code=-1,
                    stdout="",
                    stderr="Access Denied: Unsafe command token detected. Subexpression evaluations are forbidden.",
                    duration_seconds=0.0,
                    timeout_exceeded=False,
                )

        if executable_cmd[0] == "python" and venv_path.exists():
            executable_cmd[0] = str(venv_path)

        start_time = time.time()
        timeout_exceeded = False

        try:
            # Execute command inside the worktree path directory
            proc = subprocess.Popen(  # nosec
                executable_cmd,
                cwd=str(self.workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=True,  # Required on Windows to parse shell commands/scripts properly
            )
            self._active_processes.append(proc)

            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                timeout_exceeded = True

            exit_code = proc.returncode

        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = f"Sandbox execution crashed: {str(e)}"

        duration = time.time() - start_time

        return SandboxExecutionResult(
            exit_code=exit_code,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_seconds=duration,
            timeout_exceeded=timeout_exceeded,
        )

    def copy_in(self, local_path: str, remote_path: str) -> None:
        """
        Copies a file/folder from host into workspace directory.
        """
        src = Path(local_path).resolve()
        # remote_path is relative to workspace root
        dest = (self.workspace_path / remote_path).resolve()

        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        dest.parent.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dest)

    def copy_out(self, remote_path: str, local_path: str) -> None:
        """
        Copies a file/folder from workspace directory onto host path.
        """
        # remote_path is relative to workspace root
        src = (self.workspace_path / remote_path).resolve()
        dest = Path(local_path).resolve()

        if not src.exists():
            raise FileNotFoundError(f"Source file not found inside sandbox: {src}")

        dest.parent.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dest)

    def terminate(self) -> None:
        """
        Purges active transient subprocesses.
        """
        for proc in self._active_processes:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass
        self._active_processes.clear()
