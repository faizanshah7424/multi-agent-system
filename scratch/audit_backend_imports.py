import sys
import os

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("=== Starting Backend Module Import Audit ===")

try:
    print("1. Loading config...")
    from config import settings
    print(f"   Settings loaded. Persist dir: {settings.persist_path}")

    print("2. Loading core.logging...")
    from core.logging import get_logger, set_correlation_context, get_correlation_context
    logger = get_logger("Audit")
    print("   Logging initialized.")

    print("3. Loading core.metrics...")
    from core.metrics import metrics_collector, calculate_cost
    print("   Metrics initialized.")

    print("4. Loading core.cache...")
    from core.cache import llm_cache, tool_cache
    print("   Cache initialized.")

    print("5. Loading core.registry...")
    from core.registry import AgentRegistry, AgentMetadata, register_agent
    registry = AgentRegistry()
    print(f"   Registry initialized. Found {len(registry.list_agents())} registered agents.")

    print("6. Loading core.memory...")
    from core.memory import SharedMemory, VectorMemoryIndex, MemoryConsolidator
    print("   Memory system initialized.")

    print("7. Loading core.llm...")
    from core.llm import ask_llm, ask_llm_structured, GeminiWrapper
    print("   LLM system initialized.")

    print("8. Loading core.queue...")
    from core.queue import task_queue, task_manager, worker_pool, TaskStatus, TaskModel
    print("   Queue and workers initialized.")

    print("9. Loading core.workflow...")
    from core.workflow import WorkflowEngine, TaskStep, WorkflowPlan
    print("   Workflow Engine initialized.")

    print("10. Loading tools...")
    from tools.base import BaseTool
    print("    Tools base class initialized.")

    print("11. Loading agents...")
    from agents.manager import ManagerAgent
    print("    Manager agent initialized.")

    print("12. Loading api router & routes...")
    from api.routes import router
    from api.app import create_app
    print("    FastAPI app factory initialized.")

    print("\nSUCCESS: All platform modules imported cleanly! No circular dependencies detected.")
    sys.exit(0)

except Exception as e:
    import traceback
    print(f"\nFAILURE: Import audit failed with error: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
