import subprocess
from typing import Dict, Any

class VersionManager:
    """
    Subsystem exposing platform and migration version metadata.
    Reads current Git commits, SQLite database versions, and build configurations.
    """
    def __init__(self) -> None:
        self.version = "1.0.0"
        self.architecture_version = "2.2"
        self.sprint_version = "13"
        self.build_number = "103"

    def _get_git_commit(self) -> str:
        """Retrieves the current Git commit hash from subprocess."""
        try:
            res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return "unknown_commit"

    def get_version_info(self) -> Dict[str, Any]:
        """Returns the unified version mapping metadata."""
        return {
            "version": self.version,
            "architecture_version": self.architecture_version,
            "sprint_version": self.sprint_version,
            "build_number": self.build_number,
            "database_version": "SQLite Schema v1.2",
            "migration_version": "alembic_rev_039d2c",
            "git_commit": self._get_git_commit()
        }
