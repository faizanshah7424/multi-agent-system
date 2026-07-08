import os
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, ForeignKey, Index, event, Boolean, Float, func
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from config import settings

# Base declarative class
Base = declarative_base()

from core.config.database import db_settings

DATABASE_URL = db_settings.database_url
# If using the default SQLite URL, resolve it to settings.persist_path to keep existing sqlite databases intact
if DATABASE_URL == "sqlite:///data/system.db":
    db_path = settings.persist_path / "system.db"
    settings.persist_path.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30
        },
        pool_size=db_settings.pool_size,
        max_overflow=db_settings.max_overflow,
        pool_recycle=db_settings.pool_recycle
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=db_settings.pool_size,
        max_overflow=db_settings.max_overflow,
        pool_recycle=db_settings.pool_recycle
    )

import sys
import threading
from sqlalchemy.orm import Session

def log_debug(msg):
    pid = os.getpid()
    tid = threading.get_ident()
    tname = threading.current_thread().name
    sys.stdout.write(f"[DB_TRACE] [PID:{pid}] [TID:{tid} ({tname})] {msg}\n")
    sys.stdout.flush()

@event.listens_for(engine, "checkout")
def on_checkout(dbapi_connection, connection_record, connection_proxy):
    log_debug(f"Connection CHECKOUT (Conn ID: {id(dbapi_connection)})")

@event.listens_for(engine, "checkin")
def on_checkin(dbapi_connection, connection_record):
    log_debug(f"Connection CHECKIN (Conn ID: {id(dbapi_connection)})")

# Enforce SQLite WAL (Write-Ahead Logging) for high concurrency writes without lock congestion
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    log_debug(f"Connection OPENED/CONNECTED (Conn ID: {id(dbapi_connection)})")
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

# Session Management
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(session_factory)

@event.listens_for(Session, "after_begin")
def on_after_begin(session, transaction, connection):
    log_debug(f"Session {id(session)}: BEGIN transaction (Conn ID: {id(connection.connection)})")

@event.listens_for(Session, "after_commit")
def on_after_commit(session):
    log_debug(f"Session {id(session)}: COMMIT transaction event")

@event.listens_for(Session, "after_rollback")
def on_after_rollback(session):
    log_debug(f"Session {id(session)}: ROLLBACK transaction event")

@contextmanager
def get_db_session() -> Generator[scoped_session, None, None]:
    """
    Context manager providing transactional thread-safe database session boundaries.
    """
    from core.telemetry import tracer
    with tracer.start_as_current_span("sqlalchemy.session") as span:
        span.set_attribute("db.system", engine.dialect.name)
        session = db_session()
        session_id = id(session)
        log_debug(f"get_db_session() - Session {session_id} retrieved/created")
        try:
            yield session
            log_debug(f"get_db_session() - Session {session_id} COMMIT starting")
            session.commit()
            log_debug(f"get_db_session() - Session {session_id} COMMIT successful")
        except Exception as e:
            log_debug(f"get_db_session() - Session {session_id} ROLLBACK starting due to error: {e}")
            session.rollback()
            log_debug(f"get_db_session() - Session {session_id} ROLLBACK completed")
            span.record_exception(e)
            raise
        finally:
            log_debug(f"get_db_session() - Session {session_id} CLOSE starting")
            db_session.remove()
            log_debug(f"get_db_session() - Session {session_id} CLOSE completed")

# =====================================================================
# Database Models (Original, Reconstructed & Sprints)
# =====================================================================

class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(String(50), primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:8]}")
    user_id = Column(String(50))
    org_id = Column(String(50))
    workspace_id = Column(String(50))
    task_type = Column(String(50), default="workflow")
    payload_json = Column(JSON, nullable=False)
    status = Column(String(20), default="PENDING")
    variables_json = Column(JSON)
    claimed_by = Column(String(50))
    lease_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    error = Column(Text)


class APIKeyRecord(Base):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(String(50), nullable=False)
    org_id = Column(String(50))
    workspace_id = Column(String(50))
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)


class AuthAuditLogRecord(Base):
    __tablename__ = 'auth_audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)  # LOGIN_SUCCESS, LOGIN_FAILED, TOKEN_DENIED, API_KEY_USED, API_KEY_DENIED, ROLE_DENIED
    user_id = Column(String(50))
    org_id = Column(String(50))
    workspace_id = Column(String(50))
    ip_address_hash = Column(String(64))
    details = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class UserSessionRecord(Base):
    __tablename__ = 'user_sessions'

    id = Column(String(100), primary_key=True)  # session token ID or claims ID
    user_id = Column(String(50), nullable=False, index=True)
    org_id = Column(String(50))
    workspace_id = Column(String(50))
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))



class MemoryEntry(Base):
    __tablename__ = 'memory_entries'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class WorkerHeartbeat(Base):
    __tablename__ = 'worker_heartbeats'

    worker_id = Column(String(50), primary_key=True)
    hostname = Column(String(100), nullable=False)
    pid = Column(Integer, nullable=False)
    startup_time = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    active_task_id = Column(String(50))
    status = Column(String(20), default="IDLE")


class TaskLog(Base):
    __tablename__ = 'task_logs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    source = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(10), default="INFO")


class AgentMessage(Base):
    __tablename__ = 'agent_messages'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    role = Column(String(20), nullable=False)
    agent_name = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class WorkflowExecution(Base):
    __tablename__ = 'workflow_executions'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    step_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    assigned_agent = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    result = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class CodebaseIndex(Base):
    __tablename__ = 'codebase_indices'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String(50), nullable=False)
    workspace_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AgentChangeHistory(Base):
    __tablename__ = 'agent_change_history'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    agent_name = Column(String(50), nullable=False)
    file_path = Column(Text, nullable=False)
    change_type = Column(String(20), nullable=False)
    diff = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class CodeReviewComment(Base):
    __tablename__ = 'code_review_comments'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    file_path = Column(Text, nullable=False)
    line_number = Column(Integer)
    comment = Column(Text, nullable=False)
    severity = Column(String(20), default="info")
    reviewer_agent = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class CodebaseFileIndex(Base):
    __tablename__ = 'codebase_file_indices'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    index_id = Column(String(50), ForeignKey('codebase_indices.id'), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(20))
    size = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    is_important = Column(Boolean, default=False)
    summary = Column(Text)
    last_indexed = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class GitBranchTracking(Base):
    __tablename__ = 'git_branch_tracking'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    branch_name = Column(String(100), nullable=False)
    commit_hash = Column(String(40), nullable=False)
    is_merged = Column(Boolean, default=False)
    pull_request_url = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class GitChangeTracking(Base):
    __tablename__ = 'git_change_tracking'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    file_path = Column(Text, nullable=False)
    original_hash = Column(String(64))
    modified_hash = Column(String(64))
    change_type = Column(String(20), nullable=False)
    diff = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class GitHubRepository(Base):
    __tablename__ = 'github_repositories'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repo_name = Column(String(100), nullable=False)
    owner = Column(String(100), nullable=False)
    html_url = Column(Text, nullable=False)
    description = Column(Text)
    primary_language = Column(String(50))
    stars_count = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class GitHubPullRequest(Base):
    __tablename__ = 'github_pull_requests'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    state = Column(String(20), nullable=False)
    body = Column(Text)
    user = Column(String(100))
    head_branch = Column(String(100))
    base_branch = Column(String(100))
    is_merged = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    closed_at = Column(DateTime)
    merged_at = Column(DateTime)


class GitHubIssue(Base):
    __tablename__ = 'github_issues'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    issue_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    state = Column(String(20), nullable=False)
    body = Column(Text)
    user = Column(String(100))
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    closed_at = Column(DateTime)
    milestone = Column(String(100))
    labels = Column(JSON)


class CodebaseNode(Base):
    __tablename__ = 'codebase_nodes'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    index_id = Column(String(50), ForeignKey('codebase_indices.id'), nullable=False)
    name = Column(String(100), nullable=False)
    node_type = Column(String(50), nullable=False)
    file_path = Column(Text)
    metadata_json = Column(JSON)


class CodebaseEdge(Base):
    __tablename__ = 'codebase_edges'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    index_id = Column(String(50), ForeignKey('codebase_indices.id'), nullable=False)
    source_node_id = Column(String(50), ForeignKey('codebase_nodes.id'), nullable=False)
    target_node_id = Column(String(50), ForeignKey('codebase_nodes.id'), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    metadata_json = Column(JSON)


class DecisionRecord(Base):
    __tablename__ = 'decision_records'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    proposal_title = Column(String(100), nullable=False)
    alternatives_json = Column(JSON)
    selected_plan = Column(Text, nullable=False)
    score_details = Column(JSON)
    risk_level = Column(String(20))
    approval_status = Column(String(20))
    explainability_log = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ExecutionPlanRecord(Base):
    __tablename__ = 'execution_plans'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    steps_json = Column(JSON)
    selected_strategy = Column(String(100), nullable=False)
    risk_level = Column(String(20))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class RepairHistoryRecord(Base):
    __tablename__ = 'repair_history'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    test_command = Column(String(200), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    failure_details_json = Column(JSON)
    repair_plan = Column(Text)
    repair_explanation = Column(Text)
    status = Column(String(20))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class GitHubBranch(Base):
    __tablename__ = 'github_branches'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    branch_name = Column(String(100), nullable=False)
    commit_hash = Column(String(100))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class GitHubLabel(Base):
    __tablename__ = 'github_labels'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(10))
    description = Column(Text)


class GitHubMilestone(Base):
    __tablename__ = 'github_milestones'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    state = Column(String(20))
    due_on = Column(DateTime)


class GitHubDiscussion(Base):
    __tablename__ = 'github_discussions'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    discussion_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class GitHubReview(Base):
    __tablename__ = 'github_reviews'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    pull_request_id = Column(String(50), ForeignKey('github_pull_requests.id'), nullable=False)
    review_id = Column(String(50))
    user = Column(String(100))
    body = Column(Text)
    state = Column(String(50))
    submitted_at = Column(DateTime)


class GitHubTag(Base):
    __tablename__ = 'github_tags'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    name = Column(String(100), nullable=False)
    commit_hash = Column(String(100))


class GitHubRelease(Base):
    __tablename__ = 'github_releases'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    tag_name = Column(String(100), nullable=False)
    name = Column(String(200))
    body = Column(Text)
    created_at = Column(DateTime)
    published_at = Column(DateTime)


class GitHubSyncHistory(Base):
    __tablename__ = 'github_sync_history'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    sync_started_at = Column(DateTime)
    sync_completed_at = Column(DateTime)
    status = Column(String(20))
    updated_resources = Column(JSON)
    deleted_resources = Column(JSON)
    statistics = Column(JSON)
    error = Column(Text)

# =====================================================================
# Sprint 7: GitHub Analysis Models
# =====================================================================

class RepositoryHealth(Base):
    __tablename__ = 'repository_health'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    health_score = Column(Float)
    open_issues_count = Column(Integer)
    closed_issues_count = Column(Integer)
    prs_count = Column(Integer)
    merge_rate = Column(Float)
    branch_count = Column(Integer)
    commit_frequency = Column(Float)
    contributor_count = Column(Integer)
    average_pr_size = Column(Float)
    stale_branches_count = Column(Integer)
    stale_issues_count = Column(Integer)
    detailed_metrics = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class IssueAnalysis(Base):
    __tablename__ = 'issue_analyses'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    issue_id = Column(String(50), ForeignKey('github_issues.id'), nullable=False)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    priority = Column(String(50))
    is_duplicate = Column(Boolean)
    duplicate_of_id = Column(String(50), ForeignKey('github_issues.id'))
    requirement_category = Column(String(100))
    classification = Column(String(50))
    complexity_estimation = Column(String(50))
    risk_estimation = Column(String(50))
    reasoning_details = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class PullRequestAnalysis(Base):
    __tablename__ = 'pull_request_analyses'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    pr_id = Column(String(50), ForeignKey('github_pull_requests.id'), nullable=False)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    risk_score = Column(Float)
    breaking_change_probability = Column(Float)
    estimated_review_time_minutes = Column(Integer)
    complexity_score = Column(Float)
    files_changed = Column(JSON)
    hotspots = Column(JSON)
    test_coverage_recommendation = Column(Text)
    structured_summary = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class DeveloperAnalytics(Base):
    __tablename__ = 'developer_analytics'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    developer_username = Column(String(100), nullable=False)
    commits_count = Column(Integer)
    pr_approvals_count = Column(Integer)
    average_review_time_seconds = Column(Float)
    most_modified_files = Column(JSON)
    active_branches = Column(JSON)
    code_ownership_share = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class HistoricalMetrics(Base):
    __tablename__ = 'historical_metrics'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    repository_id = Column(String(50), ForeignKey('github_repositories.id'), nullable=False)
    metric_type = Column(String(50), nullable=False)
    metric_value = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprints 8 & 9: Autonomous Loop, Timeline & Pair Programming Models
# =====================================================================

class AutonomousTask(Base):
    __tablename__ = 'autonomous_tasks'

    id = Column(String(50), primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:8]}")
    request_text = Column(Text, nullable=False)
    status = Column(String(20), default="running")
    current_phase = Column(String(50))
    report_content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class DecisionLog(Base):
    __tablename__ = 'decision_logs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    phase_name = Column(String(50), nullable=False)
    decision_reason = Column(Text, nullable=False)
    alternatives_considered = Column(JSON)
    selected_option = Column(String(100), nullable=False)
    risk_level = Column(String(20))
    confidence_score = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class TaskTimeline(Base):
    __tablename__ = 'task_timelines'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    event_name = Column(String(100), nullable=False)
    event_description = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ExecutionPhase(Base):
    __tablename__ = 'execution_phases'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    phase_name = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    completed_at = Column(DateTime)
    phase_data = Column(JSON)


class ApprovalRequest(Base):
    __tablename__ = 'approval_requests'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    requester_agent = Column(String(50), nullable=False)
    action_description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ApprovalDecision(Base):
    __tablename__ = 'approval_decisions'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    request_id = Column(String(50), ForeignKey('approval_requests.id'), nullable=False)
    approver_user = Column(String(100), nullable=False)
    decision = Column(String(20), nullable=False)
    comments = Column(Text)
    decided_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class EngineeringConversation(Base):
    __tablename__ = 'engineering_conversations'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    sender = Column(String(50), nullable=False)
    recipient = Column(String(50), nullable=False)
    message_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ExecutionTimeline(Base):
    __tablename__ = 'execution_timelines'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    event_name = Column(String(100), nullable=False)
    event_description = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class RollbackRecord(Base):
    __tablename__ = 'rollback_records'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    backup_content_hash = Column(String(100), nullable=False)
    status = Column(String(20), default="success")
    restored_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class PairProgrammingSession(Base):
    __tablename__ = 'pair_programming_sessions'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('autonomous_tasks.id'), nullable=False)
    developer_role = Column(String(50), nullable=False)
    navigator_role = Column(String(50), nullable=False)
    active_file = Column(String(255))
    conversation_history = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 10: Context & Prompt Caching Models
# =====================================================================

class ContextCache(Base):
    __tablename__ = 'context_caches'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    index_id = Column(String(50), nullable=False)
    target_file = Column(String(255), nullable=False)
    repo_hash = Column(String(100), nullable=False)
    depth = Column(Integer, default=0)
    context_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class PromptCacheRecord(Base):
    __tablename__ = 'prompt_cache_records'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    prompt_key = Column(String(255), nullable=False, unique=True)
    prompt_mode = Column(String(50), nullable=False)
    rendered_prompt = Column(Text, nullable=False)
    hit_count = Column(Integer, default=0)
    miss_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 11: Multi-LLM Orchestration Models
# =====================================================================

class LLMModelConfig(Base):
    __tablename__ = 'llm_model_configs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    api_key = Column(String(255))
    api_base = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class LLMProviderHealth(Base):
    __tablename__ = 'llm_provider_health'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    provider = Column(String(50), nullable=False, unique=True)
    is_healthy = Column(Boolean, default=True)
    error_count = Column(Integer, default=0)
    latency_avg_ms = Column(Float, default=0.0)
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class LLMBenchmark(Base):
    __tablename__ = 'llm_benchmarks'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    benchmark_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    latency_ms = Column(Float)
    success_rate = Column(Float)
    quality_score = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class LLMRequestLog(Base):
    __tablename__ = 'llm_request_logs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    outcome = Column(String(20), nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 12: IDE Integration & Local Agent Models
# =====================================================================

class TerminalSession(Base):
    __tablename__ = 'terminal_sessions'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_name = Column(String(100), nullable=False)
    cwd = Column(Text)
    env_vars = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class WorkspaceScan(Base):
    __tablename__ = 'workspace_scans'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    workspace_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ExecutionAuditLog(Base):
    __tablename__ = 'execution_audit_logs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    action_name = Column(String(100), nullable=False)
    parameters = Column(JSON)
    exit_code = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ProcessLog(Base):
    __tablename__ = 'process_logs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    pid = Column(Integer, nullable=False)
    process_name = Column(String(100))
    port = Column(Integer)
    status = Column(String(20), default="running")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 14: SaaS Foundation & Multi-Tenant Models
# =====================================================================

class User(Base):
    __tablename__ = 'users'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    email = Column(String(150), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class OrganizationMembership(Base):
    __tablename__ = 'organization_memberships'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(50), ForeignKey('users.id'), nullable=False)
    org_id = Column(String(50), ForeignKey('organizations.id'), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class Project(Base):
    __tablename__ = 'projects'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    org_id = Column(String(50), ForeignKey('organizations.id'), nullable=False)
    name = Column(String(100), nullable=False)
    repository_url = Column(String(255))
    agent_config = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class UserApiKey(Base):
    __tablename__ = 'user_api_keys'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(50), ForeignKey('users.id'), nullable=False)
    key_hash = Column(String(255), nullable=False)
    scopes = Column(JSON)
    environment = Column(String(50), default="development")
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class UsageQuota(Base):
    __tablename__ = 'usage_quotas'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    org_id = Column(String(50), ForeignKey('organizations.id'), nullable=False)
    requests_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    storage_bytes = Column(Integer, default=0)
    execution_seconds = Column(Float, default=0.0)
    limit_usd = Column(Float, default=100.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class SaaSAuditLog(Base):
    __tablename__ = 'saas_audit_logs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    actor_id = Column(String(50))
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 15: DevOps, Deployment & Secret Manager Models
# =====================================================================

class DeploymentTarget(Base):
    __tablename__ = 'deployment_targets'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    project_id = Column(String(50), ForeignKey('projects.id'), nullable=False)
    provider = Column(String(50), nullable=False)
    target_config = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class Deployment(Base):
    __tablename__ = 'deployments'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    project_id = Column(String(50), ForeignKey('projects.id'), nullable=False)
    target_id = Column(String(50), ForeignKey('deployment_targets.id'), nullable=False)
    provider = Column(String(50), nullable=False)
    branch = Column(String(100), default="main")
    commit_hash = Column(String(100))
    status = Column(String(20), default="pending")
    rollback_status = Column(String(20))
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class DeploymentLog(Base):
    __tablename__ = 'deployment_logs'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    deployment_id = Column(String(50), ForeignKey('deployments.id'), nullable=False)
    log_level = Column(String(10), default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class DeploymentMetric(Base):
    __tablename__ = 'deployment_metrics'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    deployment_id = Column(String(50), ForeignKey('deployments.id'), nullable=False)
    cpu_usage_pct = Column(Float)
    memory_usage_mb = Column(Float)
    response_time_ms = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class DeploymentSecret(Base):
    __tablename__ = 'deployment_secrets'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    project_id = Column(String(50), ForeignKey('projects.id'), nullable=False)
    secret_name = Column(String(100), nullable=False)
    secret_value_encrypted = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 16: Code Review & Quality Score Models
# =====================================================================

class CodeReview(Base):
    __tablename__ = 'code_reviews'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    project_id = Column(String(50), ForeignKey('projects.id'), nullable=False)
    target_commit = Column(String(100))
    target_branch = Column(String(100))
    summary = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class SecurityFinding(Base):
    __tablename__ = 'security_findings'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    review_id = Column(String(50), ForeignKey('code_reviews.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    line_number = Column(Integer)
    rule_id = Column(String(100))
    severity = Column(String(20))
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    evidence = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class PerformanceFinding(Base):
    __tablename__ = 'performance_findings'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    review_id = Column(String(50), ForeignKey('code_reviews.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    line_number = Column(Integer)
    rule_id = Column(String(100))
    severity = Column(String(20))
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    evidence = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ArchitectureFinding(Base):
    __tablename__ = 'architecture_findings'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    review_id = Column(String(50), ForeignKey('code_reviews.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    line_number = Column(Integer)
    rule_id = Column(String(100))
    severity = Column(String(20))
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    evidence = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class QualityScore(Base):
    __tablename__ = 'quality_scores'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    review_id = Column(String(50), ForeignKey('code_reviews.id'), nullable=False)
    overall_score = Column(Float)
    maintainability = Column(Float)
    readability = Column(Float)
    security = Column(Float)
    performance = Column(Float)
    testing = Column(Float)
    documentation = Column(Float)
    architecture = Column(Float)
    technical_debt_hours = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 17: Self-Healing & Learning Engine Models
# =====================================================================

class RepairSession(Base):
    __tablename__ = 'repair_sessions'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    status = Column(String(20), default="running")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    completed_at = Column(DateTime)


class RepairAttempt(Base):
    __tablename__ = 'repair_attempts'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    task_id = Column(String(50), ForeignKey('tasks.task_id'), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    test_results = Column(JSON)
    error_classification = Column(String(100))
    repair_plan = Column(Text)
    code_diff = Column(Text)
    status = Column(String(20))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ConfidenceScoreModel(Base):
    __tablename__ = 'confidence_scores'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String(50), ForeignKey('repair_sessions.id'), nullable=False)
    repair_confidence = Column(Float)
    risk_score = Column(Float)
    regression_probability = Column(Float)
    architecture_impact = Column(Float)
    deployment_risk = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class RegressionReportModel(Base):
    __tablename__ = 'regression_reports'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String(50), ForeignKey('repair_sessions.id'), nullable=False)
    has_regression = Column(Boolean)
    details = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class LearningRecord(Base):
    __tablename__ = 'learning_records'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    failure_pattern = Column(Text, nullable=False)
    repair_strategy = Column(Text, nullable=False)
    success_rate = Column(Float)
    failure_rate = Column(Float)
    affected_technologies = Column(JSON)
    repair_history = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class RepairStrategy(Base):
    __tablename__ = 'repair_strategies'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    pattern = Column(Text, nullable=False)
    strategy_description = Column(Text, nullable=False)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    technologies = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Sprint 10: Commercial Readiness & Billing
# =====================================================================

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    org_id = Column(String(50), nullable=False, unique=True)
    customer_id = Column(String(50), nullable=False)
    plan = Column(String(50), default="free")
    status = Column(String(50), default="active")
    seats = Column(Integer, default=1)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class AnalyticsEvent(Base):
    __tablename__ = 'analytics_events'

    id = Column(String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(50), nullable=True)
    org_id = Column(String(50), nullable=True)
    event_name = Column(String(100), nullable=False)
    properties = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# =====================================================================
# Database Initialization
# =====================================================================

def init_db():
    log_debug("init_db() - STARTING")
    Base.metadata.create_all(bind=engine)
    
    # Dynamic column addition for tasks table migration
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("tasks")]
        with engine.begin() as conn:
            if "org_id" not in columns:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN org_id VARCHAR(50)"))
                log_debug("init_db() - Migration: Added org_id to tasks")
            if "workspace_id" not in columns:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN workspace_id VARCHAR(50)"))
                log_debug("init_db() - Migration: Added workspace_id to tasks")
            if "lease_expires_at" not in columns:
                col_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
                conn.execute(text(f"ALTER TABLE tasks ADD COLUMN lease_expires_at {col_type}"))
                log_debug("init_db() - Migration: Added lease_expires_at to tasks")
    except Exception as e:
        log_debug(f"init_db() - Schema migration error (non-fatal): {e}")
        
    log_debug("init_db() - COMPLETED")
