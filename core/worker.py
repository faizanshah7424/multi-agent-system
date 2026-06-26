import os
import sys
import argparse
import socket
import time
import signal
import threading
import uuid
from datetime import datetime, timezone
from typing import Set, Dict, Optional

from core.database import get_db_session, init_db
from core.repositories import TaskRepository, WorkerRepository
from core.queue import task_manager
from core.logging import get_logger

logger = get_logger("WorkerProcess")

class WorkerRuntime:
    def __init__(self, worker_id: Optional[str] = None, concurrency: int = 2, poll_interval: float = 1.0):
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self.startup_time = datetime.now(timezone.utc).replace(tzinfo=None)
        self.worker_id = worker_id or f"worker_{self.hostname}_{self.pid}_{uuid.uuid4().hex[:4]}"
        self.concurrency = concurrency
        self.poll_interval = poll_interval
        
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.running_tasks_lock = threading.Lock()
        
        self.shutdown_event = threading.Event()
        self.heartbeat_thread: Optional[threading.Thread] = None
        
        init_db()

    def start(self):
        logger.info(f"Starting worker {self.worker_id} on {self.hostname} (PID: {self.pid}) with concurrency={self.concurrency}")
        
        # Register worker in DB
        with get_db_session() as session:
            worker_repo = WorkerRepository(session)
            worker_repo.register_worker(self.worker_id, self.hostname, self.pid)
            
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, name="HeartbeatThread", daemon=True)
        self.heartbeat_thread.start()
        
        # Setup signal handlers (signal only works in main thread of main interpreter)
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except ValueError:
            logger.warning("Signal handlers could not be registered (not in main thread). Skipping signal setup.")
        
        last_recovery_check = 0.0
        
        while not self.shutdown_event.is_set():
            try:
                # 1. Run stale worker recovery check every 10 seconds
                now = time.time()
                if now - last_recovery_check > 10.0:
                    with get_db_session() as session:
                        task_repo = TaskRepository(session)
                        recovered = task_repo.recover_stale_tasks(max_age_seconds=15)
                        if recovered:
                            logger.info(f"Recovered stale tasks from crashed workers: {recovered}")
                    last_recovery_check = now
                
                # 2. Check if we have capacity for more tasks
                with self.running_tasks_lock:
                    active_count = len(self.running_tasks)
                
                if active_count >= self.concurrency:
                    # At capacity, sleep briefly and check again
                    time.sleep(0.1)
                    continue
                
                # 3. Attempt to claim a task
                task_id = None
                with get_db_session() as session:
                    task_repo = TaskRepository(session)
                    task = task_repo.claim_task(self.worker_id)
                    if task:
                        task_id = task.task_id
                
                if task_id:
                    logger.info(f"Claimed task '{task_id}'. Starting execution thread...")
                    
                    t = threading.Thread(target=self._execute_task_wrapper, args=(task_id,), name=f"TaskThread-{task_id}")
                    with self.running_tasks_lock:
                        self.running_tasks[task_id] = t
                    t.start()
                else:
                    # No tasks available, poll sleep
                    time.sleep(self.poll_interval)
                    
            except Exception as e:
                logger.error(f"Error in worker main loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)
                
        # Graceful shutdown wait
        self._wait_for_shutdown()

    def _execute_task_wrapper(self, task_id: str):
        # 1. Enforce worker task validation & ownership checks
        with get_db_session() as session:
            task_repo = TaskRepository(session)
            db_task = task_repo.get_task(task_id)
            if not db_task:
                logger.error(f"Task '{task_id}' not found in SQLite database. Aborting execution.")
                return
            if db_task.claimed_by != self.worker_id:
                logger.error(f"Task '{task_id}' ownership mismatch! Expected worker_id='{self.worker_id}', found claimed_by='{db_task.claimed_by}'. Aborting execution.")
                return
            if db_task.status != "RUNNING":
                logger.error(f"Task '{task_id}' status mismatch! Expected status='RUNNING', found status='{db_task.status}'. Aborting execution.")
                return
                
            # 2. Strict payload structure validation
            payload = db_task.payload_json
            if not isinstance(payload, dict):
                logger.error(f"Task '{task_id}' payload is not a dictionary. Failing task.")
                self._mark_task_failed(task_id, "Invalid task payload structure: Must be a JSON object.")
                return
                
            task_prompt = payload.get("task")
            if not task_prompt or not isinstance(task_prompt, str) or len(task_prompt.strip()) == 0:
                logger.error(f"Task '{task_id}' payload missing 'task' prompt or has invalid format. Failing task.")
                self._mark_task_failed(task_id, "Invalid task payload structure: 'task' prompt string must be present and non-empty.")
                return
                
            # 3. Validate user_id formatting if present
            user_id = db_task.user_id
            if user_id is not None:
                import re
                if not isinstance(user_id, str) or not re.match(r"^[a-zA-Z0-9_\-]+$", user_id) or len(user_id) > 100:
                    logger.error(f"Task '{task_id}' has invalid owner user_id format. Failing task.")
                    self._mark_task_failed(task_id, "Invalid owner user ID format.")
                    return

        stop_event = threading.Event()
        try:
            task_manager.execute_task(task_id, stop_event)
        except Exception as e:
            logger.error(f"Unhandled error in task execution '{task_id}': {e}", exc_info=True)
        finally:
            with self.running_tasks_lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
            logger.info(f"Task '{task_id}' thread finished.")

    def _mark_task_failed(self, task_id: str, error_msg: str):
        try:
            with get_db_session() as session:
                task_repo = TaskRepository(session)
                db_task = task_repo.get_task(task_id)
                if db_task:
                    db_task.status = "FAILED"
                    db_task.error = error_msg
                    db_task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    task_repo.save_task(db_task)
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as failed: {e}")

    def _heartbeat_loop(self):
        while not self.shutdown_event.is_set():
            try:
                with self.running_tasks_lock:
                    active_tasks = list(self.running_tasks.keys())
                
                active_task_id = active_tasks[0] if active_tasks else None
                status = "RUNNING" if active_tasks else "IDLE"
                
                with get_db_session() as session:
                    worker_repo = WorkerRepository(session)
                    worker_repo.update_heartbeat(self.worker_id, status, active_task_id)
            except Exception as e:
                logger.error(f"Error updating heartbeat for worker {self.worker_id}: {e}")
                
            time.sleep(3.0)

    def _handle_signal(self, signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info(f"Received signal {sig_name} ({signum}). Initiating graceful shutdown...")
        self.shutdown_event.set()

    def _wait_for_shutdown(self):
        logger.info("Shutdown signaled. Waiting for active tasks to complete...")
        
        # We will wait up to 30 seconds for active threads to complete
        start_time = time.time()
        timeout = 30.0
        
        while True:
            with self.running_tasks_lock:
                active_tasks = list(self.running_tasks.keys())
            
            if not active_tasks:
                logger.info("All active tasks completed.")
                break
                
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(f"Shutdown timeout reached. Requeuing unfinished tasks: {active_tasks}")
                # For any tasks still running, we try to requeue them in SQLite
                with get_db_session() as session:
                    task_repo = TaskRepository(session)
                    for task_id in active_tasks:
                        db_task = task_repo.get_task(task_id)
                        if db_task and db_task.status not in ("COMPLETED", "FAILED", "CANCELLED"):
                            db_task.status = "QUEUED"
                            db_task.claimed_by = None
                            db_task.started_at = None
                            db_task.error = f"Worker {self.worker_id} was shut down during execution."
                            task_repo.save_task(db_task)
                break
                
            logger.info(f"Still waiting for tasks to finish: {active_tasks} ({timeout - elapsed:.1f}s remaining)...")
            time.sleep(1.0)
            
        # Update worker status to SHUTDOWN in DB
        try:
            with get_db_session() as session:
                worker_repo = WorkerRepository(session)
                worker_repo.update_heartbeat(self.worker_id, "SHUTDOWN", None)
            logger.info("Worker heartbeat set to SHUTDOWN.")
        except Exception as e:
            logger.error(f"Error marking worker as SHUTDOWN: {e}")
            
        logger.info("Shutdown complete. Exiting process.")
        if threading.current_thread() is threading.main_thread():
            sys.exit(0)
        else:
            return

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Platform Worker Process")
    parser.add_argument("--worker-id", type=str, default=None, help="Unique worker identifier")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent tasks to execute")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Interval in seconds to poll SQLite queue")
    
    args = parser.parse_args()
    
    worker = WorkerRuntime(
        worker_id=args.worker_id,
        concurrency=args.concurrency,
        poll_interval=args.poll_interval
    )
    worker.start()

if __name__ == "__main__":
    main()
