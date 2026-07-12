from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session
from core.database import (
    Task,
    TaskLog,
    AgentMessage,
    MemoryEntry,
    WorkflowExecution,
    WorkerHeartbeat,
)


class TaskRepository:
    """
    Repository encapsulating all transactional operations on Tasks, TaskLogs, and Agent Chatter Messages.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_task(
        self,
        task_id: str,
        payload: dict,
        user_id: Optional[str] = None,
        task_type: str = "workflow",
    ) -> Task:
        task = self.session.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            task = Task(
                task_id=task_id,
                user_id=user_id,
                task_type=task_type,
                payload_json=payload,
                status="QUEUED",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            self.session.add(task)
        else:
            if user_id is not None:
                task.user_id = user_id
            task.task_type = task_type
            task.payload_json = payload
            # Only set to QUEUED if not in a terminal state
            if task.status not in ("COMPLETED", "FAILED", "CANCELLED"):
                task.status = "QUEUED"
        self.session.flush()  # Flushes changes to get populated default values
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.session.query(Task).filter(Task.task_id == task_id).first()

    def save_task(self, task: Task) -> None:
        self.session.add(task)
        self.session.flush()

    def list_tasks(self) -> List[Task]:
        # Return sorted by created_at descending
        return self.session.query(Task).order_by(Task.created_at.desc()).all()

    def cancel_task(self, task_id: str) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None

        # Don't overwrite terminal states
        if task.status not in ("COMPLETED", "FAILED", "CANCELLED"):
            task.status = "CANCELLED"
            task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            task.error = "Task cancelled by user request."
            self.session.add(task)
            self.session.flush()
        return task

    def add_log(
        self, task_id: str, source: str, message: str, level: str = "INFO"
    ) -> TaskLog:
        log = TaskLog(
            task_id=task_id,
            source=source,
            message=message,
            level=level,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.session.add(log)
        self.session.flush()
        return log

    def get_logs(self, task_id: str) -> List[TaskLog]:
        return (
            self.session.query(TaskLog)
            .filter(TaskLog.task_id == task_id)
            .order_by(TaskLog.timestamp.asc())
            .all()
        )

    def add_message(
        self, task_id: str, role: str, agent_name: str, content: str
    ) -> AgentMessage:
        msg = AgentMessage(
            task_id=task_id,
            role=role,
            agent_name=agent_name,
            content=content,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.session.add(msg)
        self.session.flush()
        return msg

    def get_messages(self, task_id: str) -> List[AgentMessage]:
        return (
            self.session.query(AgentMessage)
            .filter(AgentMessage.task_id == task_id)
            .order_by(AgentMessage.timestamp.asc())
            .all()
        )

    def claim_task(self, worker_id: str) -> Optional[Task]:
        """
        Atomically claims a queued task using SQLite BEGIN IMMEDIATE.
        """
        # Force rollback of any implicitly started transaction to ensure we can BEGIN IMMEDIATE
        self.session.rollback()
        self.session.execute(text("BEGIN IMMEDIATE"))
        try:
            # Query for the next QUEUED task
            task = (
                self.session.query(Task)
                .filter(Task.status == "QUEUED")
                .order_by(Task.created_at.asc())
                .first()
            )

            if task:
                task.status = "RUNNING"
                task.claimed_by = worker_id
                task.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
                self.session.add(task)

                # Log the claim
                log = TaskLog(
                    task_id=task.task_id,
                    source="worker",
                    message=f"Task claimed by worker {worker_id}",
                    level="INFO",
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                self.session.add(log)
                self.session.flush()
                return task
            else:
                return None
        except Exception:
            self.session.rollback()
            raise

    def recover_stale_tasks(self, max_age_seconds: int = 15) -> List[str]:
        """
        Detects tasks claimed by workers that are now stale (crashed),
        releases them, and requeues them.
        """
        # Find stale workers
        from datetime import timedelta

        cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            seconds=max_age_seconds
        )

        stale_workers = (
            self.session.query(WorkerHeartbeat)
            .filter(
                WorkerHeartbeat.last_seen < cutoff_time,
                WorkerHeartbeat.status != "SHUTDOWN",
            )
            .all()
        )

        requeued_tasks = []
        for worker in stale_workers:
            # Find running tasks claimed by this worker
            tasks_to_recover = (
                self.session.query(Task)
                .filter(Task.claimed_by == worker.worker_id, Task.status == "RUNNING")
                .all()
            )

            for task in tasks_to_recover:
                task.status = "QUEUED"
                task.claimed_by = None
                task.started_at = None
                task.retry_count = (task.retry_count or 0) + 1
                task.error = f"Worker {worker.worker_id} heartbeat timeout. Requeued."
                self.session.add(task)

                # Log recovery
                log = TaskLog(
                    task_id=task.task_id,
                    source="recovery",
                    message=f"Task recovered from stale worker {worker.worker_id} and requeued (retry count: {task.retry_count})",
                    level="WARNING",
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                self.session.add(log)
                requeued_tasks.append(task.task_id)

            # Set worker status to SHUTDOWN so we don't process it again
            worker.status = "SHUTDOWN"
            self.session.add(worker)

        self.session.flush()
        return requeued_tasks


class MemoryRepository:
    """
    Repository encapsulating operations on semantic memory entries.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_entry(self, session_id: str, text: str, metadata_json: dict) -> MemoryEntry:
        entry = MemoryEntry(
            session_id=session_id,
            text=text,
            metadata_json=metadata_json,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def get_entries(self, session_id: str) -> List[MemoryEntry]:
        return (
            self.session.query(MemoryEntry)
            .filter(MemoryEntry.session_id == session_id)
            .order_by(MemoryEntry.timestamp.desc())
            .all()
        )

    def clear_entries(self, session_id: str) -> None:
        self.session.query(MemoryEntry).filter(
            MemoryEntry.session_id == session_id
        ).delete()
        self.session.flush()


class WorkflowRepository:
    """
    Repository encapsulating step-by-step workflow executions.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_step(
        self,
        task_id: str,
        step_id: int,
        name: str,
        description: str,
        assigned_agent: str,
        status: str = "pending",
    ) -> WorkflowExecution:
        step = WorkflowExecution(
            task_id=task_id,
            step_id=step_id,
            name=name,
            description=description,
            assigned_agent=assigned_agent,
            status=status,
        )
        self.session.add(step)
        self.session.flush()
        return step

    def update_step(
        self,
        task_id: str,
        step_id: int,
        status: str,
        result: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[WorkflowExecution]:
        step = (
            self.session.query(WorkflowExecution)
            .filter(
                WorkflowExecution.task_id == task_id,
                WorkflowExecution.step_id == step_id,
            )
            .first()
        )

        if not step:
            return None

        step.status = status
        if result is not None:
            step.result = result
        if started_at is not None:
            step.started_at = started_at
        if completed_at is not None:
            step.completed_at = completed_at

        self.session.add(step)
        self.session.flush()
        return step

    def get_steps(self, task_id: str) -> List[WorkflowExecution]:
        return (
            self.session.query(WorkflowExecution)
            .filter(WorkflowExecution.task_id == task_id)
            .order_by(WorkflowExecution.step_id.asc())
            .all()
        )


class WorkerRepository:
    """
    Repository encapsulating operations on worker registration and heartbeat tracking.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def register_worker(
        self, worker_id: str, hostname: str, pid: int
    ) -> WorkerHeartbeat:
        worker = (
            self.session.query(WorkerHeartbeat)
            .filter(WorkerHeartbeat.worker_id == worker_id)
            .first()
        )
        if not worker:
            worker = WorkerHeartbeat(
                worker_id=worker_id,
                hostname=hostname,
                pid=pid,
                startup_time=datetime.now(timezone.utc).replace(tzinfo=None),
                last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
                status="IDLE",
            )
            self.session.add(worker)
        else:
            worker.hostname = hostname
            worker.pid = pid
            worker.startup_time = datetime.now(timezone.utc).replace(tzinfo=None)
            worker.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
            worker.status = "IDLE"
            worker.active_task_id = None
            self.session.add(worker)
        self.session.flush()
        return worker

    def update_heartbeat(
        self, worker_id: str, status: str, active_task_id: Optional[str] = None
    ) -> Optional[WorkerHeartbeat]:
        worker = (
            self.session.query(WorkerHeartbeat)
            .filter(WorkerHeartbeat.worker_id == worker_id)
            .first()
        )
        if worker:
            worker.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
            worker.status = status
            worker.active_task_id = active_task_id
            self.session.add(worker)
            self.session.flush()
        return worker

    def get_active_workers(self, max_age_seconds: int = 15) -> List[WorkerHeartbeat]:
        from datetime import timedelta

        cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            seconds=max_age_seconds
        )
        return (
            self.session.query(WorkerHeartbeat)
            .filter(
                WorkerHeartbeat.last_seen >= cutoff_time,
                WorkerHeartbeat.status != "SHUTDOWN",
            )
            .all()
        )

    def get_stale_workers(self, max_age_seconds: int = 15) -> List[WorkerHeartbeat]:
        from datetime import timedelta

        cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            seconds=max_age_seconds
        )
        return (
            self.session.query(WorkerHeartbeat)
            .filter(
                WorkerHeartbeat.last_seen < cutoff_time,
                WorkerHeartbeat.status != "SHUTDOWN",
            )
            .all()
        )

    def remove_worker(self, worker_id: str) -> None:
        self.session.query(WorkerHeartbeat).filter(
            WorkerHeartbeat.worker_id == worker_id
        ).delete()
        self.session.flush()
