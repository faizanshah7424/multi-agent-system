import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class HealthCheckItem(BaseModel):
    name: str
    status: bool
    details: str

class HealthReport(BaseModel):
    overall_status: bool
    items: List[HealthCheckItem]
    disk_free_gb: float
    git_clean: bool

class RepositoryHealthInspector:
    """
    Repository Health Inspector.
    Examines git clean status, disk limits, database reachability, Docker status,
    workspace integrity, and model availability.
    """
    def __init__(self, workspace_path: str = "worktrees") -> None:
        self.workspace_path = Path(workspace_path).resolve()

    def run_diagnostics(self) -> HealthReport:
        items = []
        overall = True

        # 1. Workspace Integrity
        try:
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            test_file = self.workspace_path / ".health_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            items.append(HealthCheckItem(name="Workspace Integrity", status=True, details="Workspace path exists and is writable."))
        except Exception as e:
            overall = False
            items.append(HealthCheckItem(name="Workspace Integrity", status=False, details=f"Workspace path is unwritable: {e}"))

        # 2. Disk Usage Check
        try:
            total, used, free = shutil.disk_usage(os.getcwd())
            free_gb = free / (1024 ** 3)
            status = free_gb > 1.0  # Require at least 1 GB free
            if not status:
                overall = False
            items.append(HealthCheckItem(
                name="Disk Usage",
                status=status,
                details=f"Free disk space: {free_gb:.2f} GB (Requirement: > 1.0 GB)"
            ))
        except Exception as e:
            free_gb = 0.0
            overall = False
            items.append(HealthCheckItem(name="Disk Usage", status=False, details=f"Disk check failed: {e}"))

        # 3. Git Status check
        git_clean = True
        try:
            res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0:
                uncommitted = res.stdout.strip()
                if uncommitted:
                    git_clean = False
                    details = f"Uncommitted local changes detected:\n{uncommitted[:200]}"
                else:
                    details = "Git repository is clean."
                items.append(HealthCheckItem(name="Git Cleanliness", status=True, details=details))
            else:
                items.append(HealthCheckItem(name="Git Cleanliness", status=False, details="Not a valid git repository or git error."))
        except Exception as e:
            items.append(HealthCheckItem(name="Git Cleanliness", status=False, details=f"Git binary not found or failed: {e}"))

        # 4. Database Connection Check
        try:
            from core.database import get_db_session
            from sqlalchemy import text
            with get_db_session() as session:
                session.execute(text("SELECT 1"))
            items.append(HealthCheckItem(name="Database Reachability", status=True, details="Successfully executed query on database session."))
        except Exception as e:
            overall = False
            items.append(HealthCheckItem(name="Database Reachability", status=False, details=f"Database connect failed: {e}"))

        # 5. Docker Daemon Check
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=2.0)
            status = (res.returncode == 0)
            details = "Docker Daemon is online and accessible." if status else "Docker Daemon returned error exit code."
            items.append(HealthCheckItem(name="Docker Status", status=status, details=details))
        except Exception as e:
            # We don't fail overall health just because docker is missing (falls back to local), but warn
            items.append(HealthCheckItem(name="Docker Status", status=False, details=f"Docker CLI not found or offline: {e}"))

        # 6. Model Credentials check
        try:
            from core.di import DIContainer
            from core.security.secret_manager import SecretManager
            secret_mgr = DIContainer.get(SecretManager)
            env_val = secret_mgr.validate_environment()
            has_primary = env_val.get("GEMINI_API_KEY", False)
            details = "Primary Gemini API Key configured." if has_primary else "Missing GEMINI_API_KEY."
            items.append(HealthCheckItem(name="Model Provider API", status=has_primary, details=details))
        except Exception as e:
            items.append(HealthCheckItem(name="Model Provider API", status=False, details=f"Secret manager not initialized: {e}"))

        return HealthReport(
            overall_status=overall,
            items=items,
            disk_free_gb=free_gb,
            git_clean=git_clean
        )
