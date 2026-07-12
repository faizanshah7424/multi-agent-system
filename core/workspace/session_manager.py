from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from core.database import Base, engine, get_db_session
from core.workspace.interface import IWorkspaceSessionManager, SessionState
from core.di import DIContainer
from core.workspace.interface import IWorkspaceManager

# SQLAlchemy database schema representing session tracking records
class DBSessionState(Base):
    __tablename__ = 'workspace_sessions'
    
    task_id = Column(String(50), primary_key=True)
    workspace_path = Column(String(512), nullable=False)
    container_id = Column(String(100), nullable=True)
    git_branch = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_active = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Dynamically initialize tables
Base.metadata.create_all(bind=engine)

class WorkspaceSessionManager(IWorkspaceSessionManager):
    """
    Concrete Session Manager implementing session persistence in SQLite database
    to prevent resource leaks.
    """
    def start_session(self, task_id: str) -> SessionState:
        """
        Initializes and registers a tracking session structure.
        """
        # 1. Check if session already exists
        with get_db_session() as session:
            record = session.query(DBSessionState).filter(DBSessionState.task_id == task_id).first()
            if record:
                return SessionState(
                    task_id=record.task_id,
                    workspace_path=record.workspace_path,
                    container_id=record.container_id,
                    git_branch=record.git_branch,
                    created_at=record.created_at,
                    last_active=record.last_active
                )

        # 2. Retrieve WorkspaceManager from DIContainer to allocate worktree
        workspace_mgr = DIContainer.get(IWorkspaceManager)
        workspace_path = workspace_mgr.create_workspace(task_id)
        git_branch = f"task_{task_id}"

        # 3. Create tracking record in DB
        state = SessionState(
            task_id=task_id,
            workspace_path=workspace_path,
            container_id=None,
            git_branch=git_branch,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            last_active=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        with get_db_session() as session:
            db_record = DBSessionState(
                task_id=state.task_id,
                workspace_path=state.workspace_path,
                container_id=state.container_id,
                git_branch=state.git_branch,
                created_at=state.created_at,
                last_active=state.last_active
            )
            session.add(db_record)

        return state

    def end_session(self, task_id: str) -> None:
        """
        Cleans up and terminates sandbox and workspace allocations.
        """
        workspace_path = None
        container_id = None

        with get_db_session() as session:
            record = session.query(DBSessionState).filter(DBSessionState.task_id == task_id).first()
            if record:
                workspace_path = record.workspace_path
                container_id = record.container_id
                session.delete(record)

        # 1. Clean container sandbox if it exists
        if container_id:
            try:
                from core.sandbox.interface import ISandbox
                sandbox = DIContainer.get(ISandbox)
                # Assign active container id to terminate it
                if hasattr(sandbox, "container_id"):
                    setattr(sandbox, "container_id", container_id)
                sandbox.terminate()
            except Exception:
                pass

        # 2. Destroy transient Git worktree and branch
        workspace_mgr = DIContainer.get(IWorkspaceManager)
        try:
            workspace_mgr.destroy_workspace(task_id)
        except Exception:
            pass
