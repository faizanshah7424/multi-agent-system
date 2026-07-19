from pathlib import Path

from core.di import DIContainer
from core.indexer.interface import ICodeIndexer
from core.indexer.code_indexer import CodeIndexer
from core.models.interface import IModelProvider
from core.models.providers import GeminiProvider
from core.registry.interface import IToolRegistry, ISkillRegistry, IPromptLibrary
from core.registry.tool_registry import ToolRegistry
from core.registry.skill_registry import SkillRegistry
from core.registry.prompt_library import PromptLibrary

# Sprint 4 Imports
from core.workspace.interface import IWorkspaceManager, IWorkspaceSessionManager
from core.workspace.workspace_manager import WorkspaceManager
from core.workspace.session_manager import WorkspaceSessionManager
from core.sandbox.sandbox_factory import SandboxFactory

# Sprint 5 Imports
from core.queue.scheduler import IDAGScheduler, DAGScheduler
from core.queue.planning_engine import PlanningEngine

# Sprint 5.5 Imports
from core.queue.execution_runtime import IPlanExecutor, EngineeringExecutionRuntime

# Sprint 6 Imports
from core.queue.execution_runtime import IAgentExecutor
from core.queue.agent_executor import AgentExecutor

# Sprint 7 Imports
from core.broker.interface import IEventBroker
from core.broker.events import WebSocketEventBroker
from core.queue.hitl import HITLOrchestrator

# Sprint 8 Imports
from core.queue.self_healing import SelfHealingEngine

# Sprint 8.5 Imports
from core.benchmark.interface import IBenchmarkManager
from core.benchmark.manager import BenchmarkManager

# Sprint 9 Imports
from core.memory.interface import IEngineeringMemoryEngine
from core.memory.engine import EngineeringMemoryEngine


def bootstrap_di() -> None:
    """
    Initializes DI Container mapping interfaces to concrete implementations.
    """
    # 1. Register Indexer (Sprint 2)
    DIContainer.register(ICodeIndexer, CodeIndexer())

    # 2. Register Model Provider (Sprint 3)
    DIContainer.register(IModelProvider, GeminiProvider())

    # 3. Register Tool Registry (Sprint 3)
    DIContainer.register(IToolRegistry, ToolRegistry())

    # 4. Register Skill Registry (Sprint 3)
    DIContainer.register(ISkillRegistry, SkillRegistry())

    # 5. Register Prompt Library (Sprint 3)
    prompts_dir = Path(__file__).parent / "prompts"
    DIContainer.register(IPromptLibrary, PromptLibrary(str(prompts_dir)))

    # 6. Register Workspace Manager (Sprint 4)
    DIContainer.register(IWorkspaceManager, WorkspaceManager())

    # 7. Register Workspace Session Manager (Sprint 4)
    DIContainer.register(IWorkspaceSessionManager, WorkspaceSessionManager())

    # 8. Register Sandbox Factory (Sprint 4)
    DIContainer.register("sandbox_factory", SandboxFactory.create_sandbox)

    # 9. Register DAG Scheduler (Sprint 5)
    DIContainer.register(IDAGScheduler, DAGScheduler())

    # 10. Register Planning Engine (Sprint 5)
    DIContainer.register("planning_engine", PlanningEngine())

    # 11. Register Plan Executor (Sprint 5.5)
    DIContainer.register(IPlanExecutor, EngineeringExecutionRuntime())

    # 12. Register Agent Executor (Sprint 6)
    DIContainer.register(IAgentExecutor, AgentExecutor())

    # 13. Register Event Broker (Sprint 7)
    DIContainer.register(IEventBroker, WebSocketEventBroker())

    # 14. Register HITL Orchestrator (Sprint 7)
    DIContainer.register("hitl_orchestrator", HITLOrchestrator())

    # 15. Register Self Healing Engine (Sprint 8)
    DIContainer.register("self_healing_engine", SelfHealingEngine())

    # 16. Register Benchmark Manager (Sprint 8.5)
    DIContainer.register(IBenchmarkManager, BenchmarkManager())

    # 17. Register Engineering Memory Engine (Sprint 9)
    DIContainer.register("memory_engine", EngineeringMemoryEngine())

    # 18. Register Security Subsystems (Sprint 11)
    from core.security.secret_manager import SecretManager
    from core.security.policy_manager import RuntimePolicyManager
    from core.security.audit import SecurityAuditEngine

    secret_mgr = SecretManager()
    DIContainer.register(SecretManager, secret_mgr)
    DIContainer.register(RuntimePolicyManager, RuntimePolicyManager())
    DIContainer.register(SecurityAuditEngine, SecurityAuditEngine())

    # 19. Register Diagnostics Subsystems (Sprint 13)
    from core.diagnostics.health import RepositoryHealthInspector
    from core.diagnostics.recovery import RecoveryManager
    from core.diagnostics.metrics import MetricsCollector
    from core.diagnostics.doc_audit import DocumentationAudit
    from core.diagnostics.version import VersionManager

    DIContainer.register(RepositoryHealthInspector, RepositoryHealthInspector())
    DIContainer.register(RecoveryManager, RecoveryManager())
    DIContainer.register(MetricsCollector, MetricsCollector())
    DIContainer.register(DocumentationAudit, DocumentationAudit())
    DIContainer.register(VersionManager, VersionManager())

    # 20. Register Context Optimization (Sprint 7 Batch 4)
    from config import settings
    from core.context.prompt_builder import PromptBuilder
    from core.context.indexer import TreeSitterIndexer
    from core.context.retrieval import RetrievalPipeline
    from core.context.reranker import IReranker
    from core.context.cross_encoder_reranker import CrossEncoderReranker
    from core.storage.storage_adapter import IStorageAdapter

    backend = settings.database_backend.lower()
    if backend in ("postgres", "postgresql"):
        from core.storage.postgres_adapter import PostgresStorageAdapter
        storage = PostgresStorageAdapter()
    else:
        from core.storage.sqlite_adapter import SQLiteStorageAdapter
        storage = SQLiteStorageAdapter()

    from core.planning.decomposer import ITaskDecomposer, TaskDecomposer
    from core.planning.planner import IPlanner, Planner

    decomposer = TaskDecomposer()
    planner = Planner(decomposer=decomposer)

    indexer = TreeSitterIndexer()
    reranker = CrossEncoderReranker()
    DIContainer.register(PromptBuilder, PromptBuilder())
    DIContainer.register(TreeSitterIndexer, indexer)
    DIContainer.register(IReranker, reranker)
    DIContainer.register(IStorageAdapter, storage)
    DIContainer.register(ITaskDecomposer, decomposer)
    DIContainer.register(IPlanner, planner)
    DIContainer.register(RetrievalPipeline, RetrievalPipeline(indexer=indexer, reranker=reranker, storage=storage))


