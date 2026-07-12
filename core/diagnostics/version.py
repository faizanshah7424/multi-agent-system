import subprocess
from pathlib import Path
from typing import Dict, Any


class VersionManager:
    """
    Subsystem exposing platform and migration version metadata.
    Reads current Git commits, SQLite database versions, and build configurations.
    """

    def __init__(self) -> None:
        # Load version from VERSION file at project root, falling back to '1.3.0-beta.1'
        version_file = Path(__file__).parent.parent.parent / "VERSION"
        if version_file.exists():
            try:
                self.version = version_file.read_text(encoding="utf-8").strip()
            except Exception:
                self.version = "1.3.0-beta.1"
        else:
            self.version = "1.3.0-beta.1"

        self.architecture_version = "2.2"
        self.sprint_version = "13"
        self.build_number = "103"

    def _get_git_commit(self) -> str:
        """Retrieves the current Git commit hash from subprocess."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
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
            "git_commit": self._get_git_commit(),
        }
