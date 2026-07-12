import uuid
from fastapi import APIRouter, HTTPException, Query, Header, Path
from typing import Optional, List, Dict, Any

from api.models import (
    TaskRequest, TaskResponse, TaskCreateRequest,
    ChatRequest, ChatResponse, 
    StatusResponse, HistoryResponse, WorkerInfo, QueueStatus
)
from agents.manager import ManagerAgent
from core.memory import SharedMemory
from config import settings
from core.logging import get_logger
from core.registry import AgentRegistry, AgentNotFoundError
from core.queue import TaskModel, TaskStatus, task_manager, worker_pool, task_queue

logger = get_logger("API_Routes")

router = APIRouter()

@router.post("/task", response_model=TaskResponse)
def post_task(request: TaskRequest):
    """
    Trigger a long-running multi-agent workflow in the background.
    Returns immediately with a session ID to track progress.
    """
    session_id = request.session_id or f"task_{uuid.uuid4().hex[:8]}"
    
    # Initialize the memory file with running state to prevent empty status lookups
    try:
        memory = SharedMemory(session_id=session_id)
        memory.update_status("running")
        memory.add_log("system", f"Queuing background task execution: '{request.task}'")
    except Exception as e:
        logger.error(f"Failed to initialize memory session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize memory session.")
        
    # Queue task to execute asynchronously via the TaskQueue
    try:
        task_manager.create_task(
            task_id=session_id,
            payload={"task": request.task},
            user_id=None
        )
    except Exception as e:
        logger.error(f"Failed to create task in queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")
    
    return TaskResponse(
        session_id=session_id,
        status="running",
        message="Multi-agent task successfully started in the background."
    )

@router.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest):
    """
    Run the multi-agent workflow synchronously. 
    Blocks the response until the agents complete their cycle.
    """
    session_id = request.session_id or f"chat_{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"Synchronous execution triggered for session {session_id}.")
        manager = ManagerAgent(session_id=session_id)
        
        # Run workflow synchronously
        manager.execute(request.message)
        
        # Look for code review summary, code output, or research findings in memory
        reply_content = None
        for key in ["review", "code", "tool_agent_result", "research", "plan"]:
            val = manager.memory.get(key)
            if val:
                reply_content = str(val)
                break
                
        if not reply_content:
            reply_content = "Task finished, but no specific response artifact was found in memory. Please inspect logs."
            
        return ChatResponse(
            session_id=session_id,
            response=reply_content
        )
        
    except Exception as e:
        logger.error(f"Synchronous chat call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.get("/status", response_model=StatusResponse)
def get_status(
    session_id: str = Query(..., pattern=r"^[a-zA-Z0-9_\-]+$", description="The session ID to check status for."),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id_query: Optional[str] = Query(None, alias="user_id", description="Optional user ID for ownership validation.")
):
    """
    Check the current status and step-by-step progress of a workflow session.
    """
    from core.database import get_db_session
    from core.repositories import TaskRepository
    
    request_user_id = user_id or user_id_query
    
    with get_db_session() as session:
        repo = TaskRepository(session)
        db_task = repo.get_task(session_id)
        if not db_task:
            raise HTTPException(status_code=404, detail=f"Session ID '{session_id}' not found.")
        
        # Ownership check
        if db_task.user_id is not None and db_task.user_id != request_user_id:
            raise HTTPException(status_code=403, detail="Access Denied: You do not own this task.")
        
    try:
        memory = SharedMemory(session_id=session_id)
        steps = memory.get("workflow_steps", [])
        return StatusResponse(
            session_id=session_id,
            status=memory.state.status,
            steps=steps
        )
    except Exception as e:
        logger.error(f"Failed to load status for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve status.")

@router.get("/history", response_model=HistoryResponse)
def get_history(
    session_id: str = Query(..., pattern=r"^[a-zA-Z0-9_\-]+$", description="The session ID to retrieve logs for."),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id_query: Optional[str] = Query(None, alias="user_id", description="Optional user ID for ownership validation.")
):
    """
    Retrieve execution logs and agent-to-agent communication history for a session.
    """
    from core.database import get_db_session
    from core.repositories import TaskRepository
    
    request_user_id = user_id or user_id_query
    
    with get_db_session() as session:
        repo = TaskRepository(session)
        db_task = repo.get_task(session_id)
        if not db_task:
            raise HTTPException(status_code=404, detail=f"Session ID '{session_id}' not found.")
            
        # Ownership check
        if db_task.user_id is not None and db_task.user_id != request_user_id:
            raise HTTPException(status_code=403, detail="Access Denied: You do not own this task.")
        
    try:
        memory = SharedMemory(session_id=session_id)
        logs = memory.get_logs()
        
        # Retrieve agent-to-agent communication logs
        messages = [m.model_dump() for m in memory.state.messages]
        
        return HistoryResponse(
            session_id=session_id,
            logs=logs,
            messages=messages
        )
    except Exception as e:
        logger.error(f"Failed to read session history {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history logs.")

@router.get("/agents")
def get_agents():
    """
    Retrieve metadata for all registered agents in the ecosystem.
    """
    registry = AgentRegistry()
    return [agent.model_dump() for agent in registry.list_agents()]

# =====================================================================
# Task Queue & Worker Observability Routes
# =====================================================================

@router.post("/tasks", response_model=TaskModel)
def create_task(request: TaskCreateRequest):
    """
    Create a new background execution task and enqueue it.
    """
    task_id = request.task_id or f"task_{uuid.uuid4().hex[:8]}"
    try:
        # Initialize SharedMemory for tracing/compatibility
        try:
            memory = SharedMemory(session_id=task_id)
            memory.update_status("queued")
            task_prompt = request.payload.get("task", f"Custom task execution: {request.task_type}")
            memory.add_log("system", f"Queuing background task execution: '{task_prompt}'")
        except Exception as e:
            logger.warning(f"Failed to initialize memory tracking for task {task_id}: {str(e)}")
            
        task = task_manager.create_task(
            task_id=task_id,
            payload=request.payload,
            user_id=request.user_id
        )
        return task
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create and queue task: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskModel)
def get_task(
    task_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id_query: Optional[str] = Query(None, alias="user_id")
):
    """
    Retrieve status and metadata of a specific task.
    """
    request_user_id = user_id or user_id_query
    try:
        task = task_manager.get_task(task_id)
        if task.user_id is not None and task.user_id != request_user_id:
            raise HTTPException(status_code=403, detail="Access Denied: You do not own this task.")
        return task
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks", response_model=List[TaskModel])
def list_tasks():
    """
    Retrieve list of all tasks.
    """
    try:
        return task_manager.list_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tasks/{task_id}")
def cancel_task(
    task_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id_query: Optional[str] = Query(None, alias="user_id")
):
    """
    Cancel an execution task if queued or running.
    """
    request_user_id = user_id or user_id_query
    try:
        task = task_manager.get_task(task_id)
        if task.user_id is not None and task.user_id != request_user_id:
            raise HTTPException(status_code=403, detail="Access Denied: You do not own this task.")
        task_manager.cancel_task(task_id)
        return {"status": "success", "message": f"Task {task_id} successfully cancelled."}
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workers", response_model=List[WorkerInfo])
def get_workers():
    """
    Retrieve health and status metadata for active worker processes in the registry.
    """
    from core.database import get_db_session
    from core.repositories import WorkerRepository
    from datetime import datetime, timezone
    try:
        with get_db_session() as session:
            repo = WorkerRepository(session)
            db_workers = repo.get_active_workers(max_age_seconds=30)
            workers_info = []
            for w in db_workers:
                uptime = (datetime.now(timezone.utc).replace(tzinfo=None) - w.startup_time).total_seconds() if w.startup_time else 0.0
                workers_info.append(WorkerInfo(
                    worker_name=w.worker_id,
                    worker_id=w.worker_id,
                    is_alive=True,
                    is_healthy=True,
                    current_task=w.active_task_id,
                    last_active=w.last_seen.isoformat() if w.last_seen else datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                    status=w.status,
                    heartbeat=w.last_seen.isoformat() if w.last_seen else datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                    uptime=uptime,
                    pid=w.pid,
                    hostname=w.hostname
                ))
            return workers_info
    except Exception as e:
        logger.error(f"Failed to retrieve workers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue/status", response_model=QueueStatus)
def get_queue_status():
    """
    Retrieve the current status metrics of the task queue and worker registry.
    """
    from core.database import get_db_session
    from core.repositories import WorkerRepository
    try:
        tasks = task_manager.list_tasks()
        tasks_by_status = {}
        queue_size = 0
        for t in tasks:
            status_str = t.status.value if hasattr(t.status, "value") else str(t.status)
            tasks_by_status[status_str] = tasks_by_status.get(status_str, 0) + 1
            if status_str == "QUEUED":
                queue_size += 1
        
        with get_db_session() as session:
            repo = WorkerRepository(session)
            active_workers = repo.get_active_workers(max_age_seconds=30)
            worker_count = len(active_workers)
            
        return QueueStatus(
            queue_size=queue_size,
            worker_count=worker_count,
            tasks_by_status=tasks_by_status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# Semantic Vector Memory Endpoints
# =====================================================================

@router.get("/memory/search")
def search_memory(
    query: str = Query(..., min_length=1, max_length=500, description="The natural language query to run similarity search on."),
    limit: int = Query(default=3, ge=1, le=50, description="Maximum number of memory items to return.")
):
    """
    Perform a semantic similarity search across the long-term vector memory index.
    """
    try:
        from core.memory import VectorMemoryIndex
        index = VectorMemoryIndex()
        results = index.search(query, limit=limit)
        return [
            {
                "text": item.text,
                "metadata": item.metadata,
                "similarity": similarity,
                "timestamp": item.timestamp
            }
            for item, similarity in results
        ]
    except Exception as e:
        logger.error(f"Failed to search semantic memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to query semantic vector memory: {str(e)}")

@router.post("/memory/consolidate")
def consolidate_memory(
    session_id: str = Query(..., pattern=r"^[a-zA-Z0-9_\-]+$", description="The memory session ID to consolidate into long-term vector index."),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id_query: Optional[str] = Query(None, alias="user_id")
):
    """
    Triggers the summary and consolidation of a completed task's execution logs and communication transcripts.
    """
    request_user_id = user_id or user_id_query
    
    from core.database import get_db_session
    from core.repositories import TaskRepository
    with get_db_session() as session:
        repo = TaskRepository(session)
        db_task = repo.get_task(session_id)
        if not db_task:
            raise HTTPException(status_code=404, detail=f"Session ID '{session_id}' not found.")
        if db_task.user_id is not None and db_task.user_id != request_user_id:
            raise HTTPException(status_code=403, detail="Access Denied: You do not own this task.")
            
    try:
        from core.memory import MemoryConsolidator
        consolidator = MemoryConsolidator()
        result = consolidator.consolidate_session(session_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Session ID '{session_id}' not found or has empty logs.")
        return {
            "status": "success",
            "session_id": session_id,
            "consolidated_summary": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to consolidate memory for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to consolidate memory session: {str(e)}")

# =====================================================================
# Observability & Cost Auditing Endpoints
# =====================================================================

@router.get("/metrics")
def get_metrics():
    """
    Retrieve all system metrics, including execution counters, queue status, performance and costs.
    """
    from core.metrics import metrics_collector
    return metrics_collector.get_all_metrics()

@router.get("/metrics/costs")
def get_metrics_costs():
    """
    Retrieve system consumption cost auditing data.
    """
    from core.metrics import metrics_collector
    return metrics_collector.get_costs()

@router.get("/metrics/tokens")
def get_metrics_tokens():
    """
    Retrieve LLM token utilization accounting details.
    """
    from core.metrics import metrics_collector
    return metrics_collector.get_tokens()

@router.get("/metrics/performance")
def get_metrics_performance():
    """
    Retrieve latency and host memory performance statistics.
    """
    from core.metrics import metrics_collector
    return metrics_collector.get_performance()

@router.get("/metrics/cache")
def get_metrics_cache():
    """
    Retrieve metrics regarding the prompt and tool cache systems.
    """
    from core.cache import llm_cache, tool_cache
    return {
        "llm_cache": llm_cache.get_metrics(),
        "tool_cache": tool_cache.get_metrics()
    }

@router.get("/autonomous/executions")
def list_autonomous_executions():
    """
    Retrieve all historical autonomous executions from learning memory.
    """
    from core.autonomous_execution.execution_engine import AutonomousExecutionEngine
    engine = AutonomousExecutionEngine()
    return [e.model_dump() for e in engine.memory.list_executions()]

@router.post("/autonomous/execute")
def trigger_autonomous_execution(
    goal: str = Query(..., description="The autonomous execution goal."),
    target_files: str = Query(..., description="Comma-separated files impacted by the goal.")
):
    """
    Run the Autonomous Code Execution Engine to fulfill a safety-checked goal.
    """
    from core.autonomous_execution.execution_engine import AutonomousExecutionEngine
    engine = AutonomousExecutionEngine()
    files_list = [f.strip() for f in target_files.split(",") if f.strip()]
    res = engine.execute_goal(goal, files_list)
    return res

@router.get("/autonomous/engineering/records")
def list_engineering_records():
    """
    Retrieve all historical engineering fixes from memory.
    """
    from core.autonomous_engineering.engineering_engine import AutonomousEngineeringEngine
    engine = AutonomousEngineeringEngine()
    return [r.model_dump() for r in engine.memory.list_records()]

@router.post("/autonomous/engineering/fix")
def trigger_autonomous_fix(
    stack_trace: str = Query(..., description="The crash stack trace to analyze and resolve."),
    failing_tests: Optional[str] = Query(None, description="Comma-separated list of failing tests.")
):
    """
    Triggers the autonomous bug fixing pipeline.
    """
    from core.autonomous_engineering.engineering_engine import AutonomousEngineeringEngine
    engine = AutonomousEngineeringEngine()
    tests_list = [t.strip() for t in failing_tests.split(",") if t.strip()] if failing_tests else None
    res = engine.run_bug_fixing_pipeline(stack_trace, tests_list)
    return res

@router.get("/autonomous/features/records")
def list_feature_records():
    """
    Retrieve all historical feature engineering records from learning memory.
    """
    from core.feature_engine.feature_engine import AutonomousFeatureEngine
    engine = AutonomousFeatureEngine()
    return [r.model_dump() for r in engine.memory.list_records()]

@router.post("/autonomous/features/develop")
def trigger_feature_development(
    requirement: str = Query(..., description="The natural language feature requirement.")
):
    """
    Triggers the autonomous feature development pipeline.
    """
    from core.feature_engine.feature_engine import AutonomousFeatureEngine
    engine = AutonomousFeatureEngine()
    res = engine.develop_feature(requirement)
    return res

@router.get("/autonomous/repository/records")
def list_repository_records():
    """
    Retrieve all historical repository engineering records.
    """
    from core.autonomous_repository.repository_engine import AutonomousRepositoryEngine
    engine = AutonomousRepositoryEngine()
    return [r.model_dump() for r in engine.memory.list_records()]

@router.post("/autonomous/repository/run")
def run_repository_engineering(
    goal: str = Query(..., description="The natural language engineering goal.")
):
    """
    Triggers the autonomous repository engineering pipeline.
    """
    from core.autonomous_repository.repository_engine import AutonomousRepositoryEngine
    engine = AutonomousRepositoryEngine()
    res = engine.run_repository_engineering(goal)
    return res

@router.get("/autonomous/products/records")
def list_product_records():
    """
    Retrieve all historical product records.
    """
    from core.product_builder.product_engine import AutonomousProductBuilder
    engine = AutonomousProductBuilder()
    return [r.model_dump() for r in engine.memory.list_records()]

@router.post("/autonomous/products/build")
def trigger_product_build(
    idea: str = Query(..., description="The natural language business idea.")
):
    """
    Triggers the autonomous product builder pipeline.
    """
    from core.product_builder.product_engine import AutonomousProductBuilder
    engine = AutonomousProductBuilder()
    res = engine.build_product(idea)
    return res

@router.get("/security/secrets")
def get_secrets_status():
    """Exposes environmental keys verification status dynamically."""
    from core.di import DIContainer
    from core.security.secret_manager import SecretManager
    try:
        secret_mgr = DIContainer.get(SecretManager)
        return secret_mgr.validate_environment()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/security/policies")
def get_runtime_policies():
    """Exposes command registry and configuration protections."""
    from core.di import DIContainer
    from core.security.policy_manager import RuntimePolicyManager
    try:
        policy_mgr = DIContainer.get(RuntimePolicyManager)
        return {
            "allowed_prefixes": list(policy_mgr.allowed_command_prefixes),
            "protected_configs": list(policy_mgr.protected_configs),
            "workspace_root": str(policy_mgr.workspace_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/security/audit")
def run_security_audit(code_content: str, file_path: str = "custom_file.py"):
    """Performs an on-demand security scan on any code content block."""
    from core.di import DIContainer
    from core.security.audit import SecurityAuditEngine
    try:
        audit_engine = DIContainer.get(SecurityAuditEngine)
        findings = audit_engine.audit_code(code_content, file_path)
        return [f.model_dump() for f in findings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/benchmark/summary")
def get_benchmark_summary():
    """Exposes active benchmark project configurations."""
    from core.di import DIContainer
    from core.benchmark.interface import IBenchmarkManager
    try:
        manager = DIContainer.get(IBenchmarkManager)
        return manager.list_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sandbox/status")
def get_sandbox_status():
    """Exposes docker status and environment isolation capabilities."""
    import subprocess
    docker_available = False
    details = "Docker daemon info call crashed."
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, timeout=2.0)
        docker_available = (res.returncode == 0)
        details = "Docker Daemon is online." if docker_available else res.stderr.decode().strip()
    except Exception as e:
        details = str(e)
    return {
        "docker_available": docker_available,
        "details": details,
        "resource_allocation": {
            "cpu_limit": "1.0 CPU Core",
            "memory_limit": "512MB RAM",
            "network_policy": "ISOLATED (none)",
            "root_mount": "READ-ONLY"
        }
    }

