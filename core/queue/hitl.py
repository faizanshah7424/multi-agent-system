import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, JSON
from core.database import Base, engine, get_db_session
from core.queue.scheduler import PlanDAG, PlanStep
from core.di import DIContainer
from core.broker.interface import IEventBroker

class DBTaskPlan(Base):
    """
    SQLAlchemy table persisting the execution PlanDAG and status state
    for human-in-the-loop (HITL) resumption and recovery.
    """
    __tablename__ = 'task_plans'
    
    task_id = Column(String(50), primary_key=True)
    plan_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Initialize database schema dynamically
Base.metadata.create_all(bind=engine)

class HITLOrchestrator:
    """
    Orchestration manager handling Human-in-the-Loop approval gates,
    task pause/resume states, and real-time streaming notifications.
    """
    def __init__(self) -> None:
        pass

    def register_plan(self, task_id: str, plan: PlanDAG) -> None:
        """
        Persists the initial task PlanDAG in SQLite.
        """
        with get_db_session() as session:
            record = session.query(DBTaskPlan).filter(DBTaskPlan.task_id == task_id).first()
            if not record:
                record = DBTaskPlan(task_id=task_id, plan_json=plan.model_dump())
                session.add(record)
            else:
                record.plan_json = plan.model_dump()
                record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def get_plan(self, task_id: str) -> Optional[PlanDAG]:
        """
        Loads the persisted PlanDAG from SQLite.
        """
        with get_db_session() as session:
            record = session.query(DBTaskPlan).filter(DBTaskPlan.task_id == task_id).first()
            if record:
                # Handle dict or string parsed JSON representation
                data = record.plan_json
                if isinstance(data, str):
                    data = json.loads(data)
                return PlanDAG(**data)
        return None

    def check_step_needs_approval(self, step: PlanStep) -> Optional[str]:
        """
        Checks if the step requires explicit human approval before running.
        Returns the type of approval needed, or None.
        """
        desc_lower = step.description.lower()
        
        # Security boundaries checks on dangerous actions
        if "commit" in desc_lower:
            return "Git Commit Approval"
        if "merge" in desc_lower:
            return "Git Merge Approval"
        if "delete" in desc_lower or "remove" in desc_lower:
            return "File Deletion Approval"
        if "migration" in desc_lower or "db_migrate" in desc_lower:
            return "Database Migration Approval"
        if "install" in desc_lower or "pip" in desc_lower:
            return "Dependency Installation Approval"
        if "refactor" in desc_lower:
            return "Large Code Refactor Approval"
            
        return None

    def request_approval(self, task_id: str, step: PlanStep, approval_type: str) -> None:
        """
        Pauses plan execution, persists WAITING_FOR_APPROVAL status, and streams WebSocket alerts.
        """
        # 1. Update task status in DB
        from core.queue import task_manager, TaskStatus
        try:
            task = task_manager.get_task(task_id)
            task.status = TaskStatus.PENDING  # Set back to queue pending so it can be resumed
            # Or use a dedicated status or variables_json field
            task.error = f"PAUSED: Waiting for {approval_type} on Step {step.step_id}"
            task_manager.save_task(task)
        except Exception:
            pass

        # 2. Update step status in DAG to waiting
        plan = self.get_plan(task_id)
        if plan:
            for s in plan.steps:
                if s.step_id == step.step_id:
                    s.status = "waiting_for_approval"
            self.register_plan(task_id, plan)

        # 3. Publish alert to WebSocket Event Broker
        try:
            broker = DIContainer.get(IEventBroker)
            broker.publish("hitl_alerts", {
                "task_id": task_id,
                "step_id": step.step_id,
                "event": "waiting_for_approval",
                "type": approval_type,
                "description": step.description
            })
        except Exception:
            pass

    def approve_step(self, task_id: str, step_id: int) -> bool:
        """
        Approves a paused step and marks it ready to resume.
        """
        plan = self.get_plan(task_id)
        if not plan:
            return False

        for step in plan.steps:
            if step.step_id == step_id:
                step.status = "approved"
                
        self.register_plan(task_id, plan)

        # Re-queue task in TaskManager to resume execution
        from core.queue import task_manager, task_queue
        try:
            task = task_manager.get_task(task_id)
            # Remove pause error log
            task.error = None
            task_manager.save_task(task)
            task_queue.put(task_id)
        except Exception:
            pass

        # Stream resume notification
        try:
            broker = DIContainer.get(IEventBroker)
            broker.publish("hitl_alerts", {
                "task_id": task_id,
                "step_id": step_id,
                "event": "approved"
            })
        except Exception:
            pass

        return True

    def reject_step(self, task_id: str, step_id: int, reason: str = "") -> None:
        """
        Rejects a paused step, marks the plan failed, and aborts downstream.
        """
        plan = self.get_plan(task_id)
        if not plan:
            return

        for step in plan.steps:
            if step.step_id == step_id:
                step.status = "failed"
            elif step.status == "pending":
                step.status = "cancelled"

        self.register_plan(task_id, plan)

        from core.queue import task_manager, TaskStatus
        try:
            task = task_manager.get_task(task_id)
            task.status = TaskStatus.FAILED
            task.error = f"Step {step_id} rejected by user: {reason}"
            task_manager.save_task(task)
        except Exception:
            pass

        # Stream rejection notification
        try:
            broker = DIContainer.get(IEventBroker)
            broker.publish("hitl_alerts", {
                "task_id": task_id,
                "step_id": step_id,
                "event": "rejected",
                "reason": reason
            })
        except Exception:
            pass
