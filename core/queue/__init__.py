import json
import os
import queue
import sys
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from config import settings
from core.logging import get_logger
from core.registry import RegistryError, AgentNotFoundError

logger = get_logger("TaskQueueSystem")

# =====================================================================
# Enums and Models
# =====================================================================

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"

class TaskModel(BaseModel):
    """
    Data model representing an execution task state inside the system.
    """
    task_id: str = Field(..., description="Unique task identifier, also used as memory session ID.")
    user_id: Optional[str] = Field(default=None, description="Optional user ID owner.")
    task_type: str = Field(default="workflow", description="Type classification of the task.")
    payload: Dict[str, Any] = Field(..., description="Prompt and variables payload required for agent execution.")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task execution status.")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    error: Optional[str] = None

# =====================================================================
# Task Queue persistence layer & Thread Safe Queue Manager
# =====================================================================

class TaskQueue:
    """
    Thread-safe task ID queue wrapping Python's built-in queue.Queue.
    Supports basic push, pull, and inspection.
    """
    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()

    def put(self, task_id: str) -> None:
        with self._lock:
            self._queue.put(task_id)

    def get(self, timeout: float = 1.0) -> str:
        # Note: get is blocking, so we do not wrap it inside lock to prevent freezing,
        # but the underlying queue.Queue is already thread-safe.
        return self._queue.get(block=True, timeout=timeout)

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        with self._lock:
            return self._queue.qsize()

    def clear(self) -> None:
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break

# =====================================================================
# Worker Threads
# =====================================================================

class Worker(threading.Thread):
    """
    Background worker thread that pops tasks from the TaskQueue and delegates
    their execution to the TaskManager.
    """
    def __init__(self, worker_id: int, task_queue: TaskQueue, manager: "TaskManager") -> None:
        super().__init__(name=f"WorkerThread-{worker_id}")
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.manager = manager
        self.stop_event = threading.Event()
        self.current_task_id: Optional[str] = None
        self.last_active = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        self.is_healthy = True

    def run(self) -> None:
        logger.info(f"Worker {self.worker_id} started and waiting for tasks.")
        while not self.stop_event.is_set():
            try:
                self.last_active = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                # Fetch task with a timeout to inspect stop_event periodically
                task_id = self.task_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            self.current_task_id = task_id
            self.last_active = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            
            logger.info(f"Worker {self.worker_id} pulled Task '{task_id}' for execution.")
            try:
                self.manager.execute_task(task_id, self.stop_event)
            except Exception as e:
                logger.error(f"Worker {self.worker_id} crashed executing task {task_id}: {str(e)}", exc_info=True)
                self.is_healthy = False
            finally:
                self.current_task_id = None
                self.task_queue.task_done()

        logger.info(f"Worker {self.worker_id} shut down gracefully.")

    def stop(self) -> None:
        self.stop_event.set()

class WorkerPool:
    """
    Manages a pool of active background Worker threads.
    Protects the system from concurrent overload by controlling the pool size.
    """
    def __init__(self, size: int, task_queue: TaskQueue, manager: "TaskManager") -> None:
        self.size = size
        self.task_queue = task_queue
        self.manager = manager
        self.workers: List[Worker] = []
        self._lock = threading.Lock()

    def start(self) -> None:
        """Spawns and starts worker threads."""
        with self._lock:
            if self.workers:
                logger.warning("Worker pool is already running.")
                return
            for i in range(self.size):
                w = Worker(worker_id=i + 1, task_queue=self.task_queue, manager=self.manager)
                w.daemon = True
                w.start()
                self.workers.append(w)
            logger.info(f"WorkerPool started with {self.size} workers.")

    def shutdown(self, timeout: float = 5.0) -> None:
        """Gracefully triggers stop signals on workers and waits for termination."""
        with self._lock:
            logger.info("Signaling WorkerPool to shutdown...")
            for w in self.workers:
                w.stop()
                
            # Wait for all workers to join/exit
            start_time = time.time()
            for w in self.workers:
                elapsed = time.time() - start_time
                wait_time = max(0.1, timeout - elapsed)
                w.join(timeout=wait_time)
                
            self.workers.clear()
            logger.info("WorkerPool shut down successfully.")

    def get_status(self) -> List[Dict[str, Any]]:
        """Returns health and execution logs for active worker threads."""
        with self._lock:
            status_list = []
            for w in self.workers:
                status_list.append({
                    "worker_name": w.name,
                    "worker_id": w.worker_id,
                    "is_alive": w.is_alive(),
                    "is_healthy": w.is_healthy,
                    "current_task": w.current_task_id,
                    "last_active": w.last_active
                })
            return status_list

# =====================================================================
# Task Manager & Persistor Coordinator
# =====================================================================

class TaskManager:
    """
    Central controller orchestrating task creation, database persistence, 
    recovery, retries, and thread execution routing.
    """
    def __init__(self, task_queue: TaskQueue) -> None:
        self.task_queue = task_queue
        self._lock = threading.Lock()
        
        # Ensure database is initialized on startup
        from core.database import init_db
        init_db()

    def _to_model(self, db_task) -> TaskModel:
        """Helper to convert database Task model to Pydantic TaskModel."""
        return TaskModel(
            task_id=db_task.task_id,
            user_id=db_task.user_id,
            task_type=db_task.task_type,
            payload=db_task.payload_json,
            status=db_task.status,
            created_at=db_task.created_at.isoformat() if db_task.created_at else datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            started_at=db_task.started_at.isoformat() if db_task.started_at else None,
            completed_at=db_task.completed_at.isoformat() if db_task.completed_at else None,
            retry_count=db_task.retry_count,
            error=db_task.error
        )

    def create_task(self, task_id: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> TaskModel:
        """
        Creates, persists in DB, and queues a new task.
        """
        from core.database import get_db_session
        from core.repositories import TaskRepository
        
        with get_db_session() as session:
            repo = TaskRepository(session)
            db_task = repo.create_task(task_id, payload, user_id)
            task_model = self._to_model(db_task)
            
        self.task_queue.put(task_model.task_id)
        logger.info(f"Task '{task_id}' created and pushed to the queue.")
        return task_model

    def get_task(self, task_id: str) -> TaskModel:
        """
        Loads a task model state directly from SQLite.
        """
        from core.database import get_db_session
        from core.repositories import TaskRepository
        
        with get_db_session() as session:
            repo = TaskRepository(session)
            db_task = repo.get_task(task_id)
            if not db_task:
                raise AgentNotFoundError(f"Task ID '{task_id}' was not found in the database.")
            return self._to_model(db_task)

    def save_task(self, task: TaskModel) -> None:
        """
        Saves a task state to the database transactionally.
        """
        from core.database import get_db_session
        from core.repositories import TaskRepository
        
        with get_db_session() as session:
            repo = TaskRepository(session)
            db_task = repo.get_task(task.task_id)
            if not db_task:
                db_task = repo.create_task(
                    task_id=task.task_id,
                    payload=task.payload,
                    task_type=task.task_type
                )
            
            db_task.status = task.status.value if hasattr(task.status, "value") else str(task.status)
            db_task.started_at = datetime.fromisoformat(task.started_at) if task.started_at else None
            db_task.completed_at = datetime.fromisoformat(task.completed_at) if task.completed_at else None
            db_task.retry_count = task.retry_count
            db_task.error = task.error
            repo.save_task(db_task)

    def list_tasks(self) -> List[TaskModel]:
        """
        Lists all persisted tasks from SQLite.
        """
        from core.database import get_db_session
        from core.repositories import TaskRepository
        
        with get_db_session() as session:
            repo = TaskRepository(session)
            db_tasks = repo.list_tasks()
            return [self._to_model(t) for t in db_tasks]

    def cancel_task(self, task_id: str) -> None:
        """
        Cancels a task if it is not already completed or failed.
        """
        from core.database import get_db_session
        from core.repositories import TaskRepository
        
        with get_db_session() as session:
            repo = TaskRepository(session)
            db_task = repo.cancel_task(task_id)
            if not db_task:
                raise AgentNotFoundError(f"Task ID '{task_id}' was not found in the database.")
        logger.info(f"Task '{task_id}' was marked as CANCELLED.")

    def recover_tasks(self) -> int:
        """
        Scans SQLite database on startup to recover incomplete tasks.
        Resets and re-queues any tasks left in running or queued states.
        """
        from core.database import get_db_session
        from core.repositories import TaskRepository
        
        recovered_count = 0
        with get_db_session() as session:
            repo = TaskRepository(session)
            db_tasks = repo.list_tasks()
            
            for task in db_tasks:
                if task.status in ("PENDING", "QUEUED", "RUNNING", "RETRYING"):
                    logger.info(f"Recovering unfinished task '{task.task_id}' (Status was '{task.status}'). Re-queuing...")
                    task.status = "QUEUED"
                    task.error = "Task recovered and re-queued after server restart."
                    repo.save_task(task)
                    self.task_queue.put(task.task_id)
                    recovered_count += 1
                    
        if recovered_count > 0:
            logger.info(f"Task recovery cycle complete. Re-queued {recovered_count} tasks.")
        return recovered_count

    def execute_task(self, task_id: str, stop_event: threading.Event) -> None:
        """
        Core task execution thread logic. Instantiates the Manager agent,
        tracks workflow steps, and routes errors/retries.
        """
        from core.logging import set_correlation_context
        from core.metrics import metrics_collector
        
        set_correlation_context(task_id=task_id, workflow_id=task_id, agent_name="worker", session_id=task_id)
        
        task = self.get_task(task_id)
        if task.status == TaskStatus.CANCELLED:
            logger.info(f"Task {task_id} was cancelled before starting.")
            return

        created_dt = datetime.fromisoformat(task.created_at)
        wait_time = (datetime.now(timezone.utc).replace(tzinfo=None) - created_dt).total_seconds()
        metrics_collector.record_queue_wait(wait_time)

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        self.save_task(task)
        logger.info(f"Executing task '{task_id}'...")

        try:
            prompt = task.payload.get("task")
            if not prompt:
                raise ValueError("Payload missing required 'task' prompt key.")

            from agents.manager import ManagerAgent
            manager = ManagerAgent(session_id=task_id)
            manager.execute(prompt)
            
            final_memory_status = manager.memory.state.status
            task = self.get_task(task_id)
            if task.status == TaskStatus.CANCELLED:
                logger.info(f"Task {task_id} completed run, but was marked CANCELLED in memory.")
                return

            if final_memory_status == "completed":
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                self.save_task(task)
                logger.info(f"Task '{task_id}' executed successfully.")
            elif final_memory_status == "failed":
                error_msg = "Workflow step failure detected in memory status logs."
                for log in reversed(manager.memory.state.logs):
                    if log.level == "ERROR":
                        error_msg = log.message
                        break
                raise Exception(error_msg)
            else:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                self.save_task(task)

        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            self.handle_task_failure(task, str(e))

    def handle_task_failure(self, task: TaskModel, error_message: str) -> None:
        """
        Routes failures to the retry loop or marks the task as failed.
        """
        max_retries = 3
        is_retryable = any(kw in error_message.lower() for kw in ["429", "quota", "demand", "timeout", "exhausted", "503"])
        
        task = self.get_task(task.task_id)
        if task.status == TaskStatus.CANCELLED:
            return

        from core.metrics import metrics_collector

        if is_retryable and task.retry_count < max_retries:
            task.status = TaskStatus.RETRYING
            task.retry_count += 1
            task.error = f"Transient error: {error_message}"
            self.save_task(task)

            metrics_collector.record_retry()
            backoff_delay = 5 * (2 ** (task.retry_count - 1))
            logger.warning(f"Task '{task.task_id}' failed (Attempt {task.retry_count}). Retrying in {backoff_delay}s...")

            def schedule_retry():
                time.sleep(backoff_delay)
                try:
                    from core.database import get_db_session
                    from core.repositories import TaskRepository
                    with get_db_session() as session:
                        repo = TaskRepository(session)
                        db_task = repo.get_task(task.task_id)
                        if db_task and db_task.status not in ("COMPLETED", "FAILED", "CANCELLED"):
                            db_task.status = "QUEUED"
                            db_task.claimed_by = None
                            repo.save_task(db_task)
                            logger.info(f"Re-queued retried task '{task.task_id}' in SQLite.")
                    self.task_queue.put(task.task_id)
                except Exception as e:
                    logger.error(f"Failed to re-queue retried task '{task.task_id}': {e}")

            t = threading.Thread(target=schedule_retry, name=f"RetryTimer-{task.task_id}")
            t.daemon = True
            t.start()
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            task.error = error_message
            self.save_task(task)
            metrics_collector.record_failure()
            logger.error(f"Task '{task.task_id}' permanently failed: {error_message}")

# =====================================================================
# Globals/Singleton helper initialization
# =====================================================================

task_queue = TaskQueue()
task_manager = TaskManager(task_queue)
worker_pool = WorkerPool(size=2, task_queue=task_queue, manager=task_manager)
