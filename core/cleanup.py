import time
import logging
from typing import Callable, Dict, List, NamedTuple

logger = logging.getLogger("CleanupCoordinator")


class RegisteredResource(NamedTuple):
    resource_type: str
    resource_identifier: str
    cleanup_callable: Callable[[], None]


class CleanupCoordinator:
    """
    Coordinator responsible for registering active resources, tracking task-session ownership,
    and executing cleanup in reverse order on failure or session end.
    """
    _registry: Dict[str, List[RegisteredResource]] = {}

    @classmethod
    def register_resource(
        cls,
        task_id: str,
        resource_type: str,
        resource_identifier: str,
        cleanup_callable: Callable[[], None]
    ) -> None:
        """
        Registers a resource under a task session for later cleanup.
        """
        # Ensure task_id is clean and present
        t_id = task_id or "global"
        cls._registry.setdefault(t_id, []).append(
            RegisteredResource(
                resource_type=resource_type,
                resource_identifier=resource_identifier,
                cleanup_callable=cleanup_callable
            )
        )
        logger.info(
            f"Registered resource for task '{t_id}': Type='{resource_type}', ID='{resource_identifier}'"
        )

    @classmethod
    def execute_cleanup(cls, task_id: str) -> None:
        """
        Executes cleanup for all registered resources for a task in reverse order (LIFO).
        Guarantees no exceptions are propagated back to the caller.
        """
        t_id = task_id or "global"
        resources = cls._registry.pop(t_id, [])
        if not resources:
            return

        logger.info(f"Initiating cleanup sequence for task '{t_id}' (Total resources: {len(resources)})...")

        # Cleanup in reverse order of registration (LIFO)
        for res in reversed(resources):
            start_time = time.time()
            success = False
            error_reason = ""
            try:
                res.cleanup_callable()
                success = True
            except Exception as e:
                error_reason = str(e)
                logger.error(
                    f"Cleanup failed for resource '{res.resource_identifier}' of type '{res.resource_type}' (Task: '{t_id}'): {error_reason}"
                )
            finally:
                duration = time.time() - start_time
                status = "SUCCESS" if success else "FAILED"
                # Structured cleanup log record
                logger.info(
                    f"[CLEANUP_LOG] ResourceType: {res.resource_type} | TaskID: {t_id} | "
                    f"Identifier: {res.resource_identifier} | Status: {status} | "
                    f"Duration: {duration:.4f}s | Reason: {error_reason}"
                )

    @classmethod
    def detect_orphans(cls) -> Dict[str, List[str]]:
        """
        Scans and reports orphan containers, workspaces, and stale temporary directories.
        Does not delete them automatically; only reports.
        """
        orphans = {
            "orphan_containers": [],
            "orphan_workspaces": [],
            "stale_temp_dirs": []
        }

        # 1. Detect orphan Docker containers
        # Look for containers starting with "task_sandbox_"
        import subprocess
        try:
            res = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=task_sandbox_", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5.0
            )
            # Cross-reference with DB session state (active tasks)
            from core.database import get_db_session
            from core.workspace.session_manager import DBSessionState
            
            active_container_ids = set()
            try:
                with get_db_session() as session:
                    records = session.query(DBSessionState).all()
                    for r in records:
                        if r.container_id:
                            active_container_ids.add(r.container_id)
            except Exception:
                pass

            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    name = line.strip()
                    if name and name not in active_container_ids:
                        orphans["orphan_containers"].append(name)
        except Exception as e:
            logger.debug(f"Docker orphan check skipped or failed: {e}")

        # 2. Detect orphan workspaces
        # Look for workspace directories in temp or system temp dir
        import tempfile
        from pathlib import Path
        temp_runs_dir = Path(tempfile.gettempdir()) / "codeorbit_runs"
        
        active_workspace_paths = set()
        try:
            from core.database import get_db_session
            from core.workspace.session_manager import DBSessionState
            with get_db_session() as db_session:
                records = db_session.query(DBSessionState).all()
                for r in records:
                    if r.workspace_path:
                        active_workspace_paths.add(Path(r.workspace_path).resolve())
        except Exception:
            pass

        if temp_runs_dir.exists():
            for task_dir in temp_runs_dir.iterdir():
                if task_dir.is_dir():
                    workspace_dir = task_dir / "workspace"
                    if workspace_dir.exists():
                        resolved_ws = workspace_dir.resolve()
                        if resolved_ws not in active_workspace_paths:
                            orphans["orphan_workspaces"].append(str(resolved_ws))
                    else:
                        orphans["stale_temp_dirs"].append(str(task_dir.resolve()))

        # Report outcomes
        logger.info("[ORPHAN_DETECTION] Scan completed.")
        for key, items in orphans.items():
            logger.info(f"[ORPHAN_DETECTION] {key}: Count={len(items)} | Items={items}")

        return orphans
