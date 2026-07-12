import os
import sys
import json
import traceback
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


class RecoveryManager:
    """
    Automatic Recovery Manager.
    Tries to repair transient runtime crashes (Docker hang-ups, workspace locking, database disconnections).
    """

    def __init__(self, workspace_path: str = "worktrees") -> None:
        self.workspace_path = Path(workspace_path).resolve()

    def recover_sandbox(self, container_name: str) -> bool:
        """Tries to clean up and force remove a crashed or hanging sandbox container."""
        try:
            # Stop and force remove the container
            subprocess.run(
                ["docker", "stop", container_name], capture_output=True, timeout=5.0
            )
            subprocess.run(
                ["docker", "rm", "-f", container_name], capture_output=True, timeout=5.0
            )
            return True
        except Exception:
            return False

    def recover_workspace(self, task_id: str) -> bool:
        """Removes lock files or temporary session directories left behind by a crash."""
        try:
            session_dir = self.workspace_path / f"session_{task_id}"
            if session_dir.exists():
                import shutil

                shutil.rmtree(session_dir, ignore_errors=True)
            return True
        except Exception:
            return False

    def check_and_recover_db(self) -> bool:
        """Tries to ping the database and re-initializes tables if disconnected."""
        try:
            from core.database import init_db, get_db_session
            from sqlalchemy import text

            init_db()
            with get_db_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


class CrashReportGenerator:
    """
    System Crash Reporter.
    Compiles detailed runtime diagnostic files under the crash_reports/ directory.
    """

    @staticmethod
    def generate_report(
        error: Exception,
        active_agent: Optional[str] = None,
        current_task: Optional[str] = None,
        sandbox_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        report_dir = Path("crash_reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        # Build structured findings
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_text = "".join(tb_lines)

        report_data = {
            "timestamp": timestamp,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "stack_trace": tb_text,
            "active_agent": active_agent or "unknown",
            "current_task": current_task or "none",
            "sandbox": sandbox_id or "none",
            "model": model_name or "none",
            "environment": {
                "os": sys.platform,
                "python_version": sys.version,
                "pid": os.getpid(),
                "cwd": os.getcwd(),
            },
        }

        safe_time = timestamp.replace(":", "-").replace(".", "-")
        report_file = report_dir / f"crash_{safe_time}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        return str(report_file.resolve())
