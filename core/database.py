import os
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, ForeignKey, Index, event
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from config import settings

# Base declarative class
Base = declarative_base()

# SQLite connection and path resolution
db_path = settings.persist_path / "system.db"
settings.persist_path.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{db_path}"

# Engine creation with connection pool rules
# QueuePool is used by default for non-memory DBs in SQLAlchemy.
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }, # Required for multi-threaded SQLite and preventing locked databases
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

# Enforce SQLite WAL (Write-Ahead Logging) for high concurrency writes without lock congestion
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session Management
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(session_factory)

@contextmanager
def get_db_session() -> Generator[scoped_session, None, None]:
    """
    Context manager providing transactional thread-safe database session boundaries.
    """
    session = db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# =====================================================================
# Database Models
# =====================================================================

class Task(Base):
    __tablename__ = "tasks"
    
    task_id = Column(String(50), primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:8]}")
    user_id = Column(String(50), nullable=True)
    task_type = Column(String(50), default="workflow")
    payload_json = Column(JSON, nullable=False)
    status = Column(String(20), default="PENDING")
    variables_json = Column(JSON, nullable=True)
    claimed_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_task_type", "task_type"),
        Index("ix_tasks_claimed_by", "claimed_by"),
    )

class TaskLog(Base):
    __tablename__ = "task_logs"
    
    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    source = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(10), default="INFO")

    __table_args__ = (
        Index("ix_task_logs_task_id", "task_id"),
        Index("ix_task_logs_level", "level"),
        Index("ix_task_logs_timestamp", "timestamp"),
    )

class AgentMessage(Base):
    __tablename__ = "agent_messages"
    
    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    agent_name = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    __table_args__ = (
        Index("ix_agent_messages_task_id", "task_id"),
        Index("ix_agent_messages_agent_name", "agent_name"),
    )

class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    
    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    __table_args__ = (
        Index("ix_memory_entries_session_id", "session_id"),
    )

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    step_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    assigned_agent = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    result = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_workflow_executions_task_id", "task_id"),
        Index("ix_workflow_executions_step_id", "step_id"),
        Index("ix_workflow_executions_status", "status"),
    )

class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    
    worker_id = Column(String(50), primary_key=True)
    hostname = Column(String(100), nullable=False)
    pid = Column(Integer, nullable=False)
    startup_time = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    active_task_id = Column(String(50), nullable=True)
    status = Column(String(20), default="IDLE") # IDLE, RUNNING, SHUTDOWN

    __table_args__ = (
        Index("ix_worker_heartbeats_last_seen", "last_seen"),
    )

# Initialization function
def init_db():
    Base.metadata.create_all(bind=engine)
