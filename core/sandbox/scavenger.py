import subprocess
import time
import threading
import re
from core.logging import get_logger
from core.database import get_db_session, Task

logger = get_logger("SandboxScavenger")


def scavenge_orphans() -> None:
    """
    Performs a single pass to find and clean up orphaned Docker container sandboxes
    whose corresponding tasks are no longer active (not PENDING or RUNNING).
    """
    try:
        # Check if Docker is available
        res = subprocess.run(["docker", "info"], capture_output=True, timeout=3.0)
        if res.returncode != 0:
            return
    except Exception:
        # Docker is not installed or daemon is offline; skip run
        return

    # List all container names that match 'task_sandbox_'
    cmd = ["docker", "ps", "-a", "--filter", "name=task_sandbox_", "--format", "{{.Names}}"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=5.0)
        if res.returncode != 0:
            logger.error(f"Failed to list Docker containers: {res.stderr.strip()}")
            return
    except Exception as e:
        logger.error(f"Error running docker ps during scavenge: {str(e)}")
        return

    container_names = [line.strip() for line in res.stdout.split("\n") if line.strip()]
    if not container_names:
        return

    logger.debug(f"Scavenger found containers: {container_names}")

    with get_db_session() as session:
        for container_name in container_names:
            # Container names are typically 'task_sandbox_{task_id}'
            match = re.search(r"task_sandbox_(.+)", container_name)
            if not match:
                continue
            task_id = match.group(1)

            # Query the task status in the database
            try:
                task = session.query(Task).filter(Task.task_id == task_id).first()
                if not task:
                    logger.warn(f"Orphaned sandbox detected (No Task record for ID {task_id}). Purging container '{container_name}'.")
                    _purge_container(container_name)
                elif task.status not in ["PENDING", "RUNNING"]:
                    logger.info(f"Task {task_id} status is '{task.status}'. Purging container '{container_name}'.")
                    _purge_container(container_name)
            except Exception as ex:
                logger.error(f"Error querying task status for {task_id}: {str(ex)}")


def _purge_container(container_name: str) -> None:
    """
    Stops and removes the specified container.
    """
    try:
        subprocess.run(["docker", "stop", container_name], capture_output=True, timeout=10.0)
        subprocess.run(["docker", "rm", container_name], capture_output=True, timeout=10.0)
        logger.info(f"Successfully purged container '{container_name}'")
    except Exception as e:
        logger.error(f"Failed to purge container '{container_name}': {str(e)}")


def scavenger_loop(interval_seconds: int = 60) -> None:
    """
    Periodic loop running in a daemon thread to trigger scavenging.
    """
    logger.info("Sandbox scavenger background thread started.")
    while True:
        try:
            scavenge_orphans()
        except Exception as e:
            logger.error(f"Unhandled error in scavenger loop: {str(e)}")
        time.sleep(interval_seconds)


def start_scavenger(interval_seconds: int = 60) -> None:
    """
    Launches the scavenger loop in a background daemon thread.
    """
    thread = threading.Thread(
        target=scavenger_loop,
        args=(interval_seconds,),
        name="SandboxScavengerThread",
        daemon=True,
    )
    thread.start()
