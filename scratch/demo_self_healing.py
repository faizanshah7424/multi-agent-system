import os
import sys
from pathlib import Path
from typing import Any

# Add root folder to path to import core files
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.queue.scheduler import PlanStep, PlanDAG
from core.queue.execution_runtime import IPlanExecutor, IAgentExecutor
from core.queue.hitl import DBTaskPlan
from core.workspace.session_manager import DBSessionState
from core.database import get_db_session


class DemoAgentExecutor(IAgentExecutor):
    """
    Simulates the Developer Agent rewriting/fixing the bug on repair request.
    """

    def __init__(self, target_file: Path) -> None:
        self.target_file = target_file
        self.attempts = 0

    def execute_step(
        self, task_id: str, step: PlanStep, workspace_path: str, sandbox: Any
    ) -> bool:
        self.attempts += 1
        print(f"[DemoAgent] Repair call received. Attempt: {self.attempts}")

        # Correcting the python file content (evidence-driven repair)
        repaired_code = 'val = "hello" + str(5)\n'
        self.target_file.write_text(repaired_code, encoding="utf-8")
        print(f"[DemoAgent] Successfully rewrote file: {self.target_file.name}")
        return True


def run_demo() -> None:
    # 1. Initialize DI Container
    bootstrap_di()

    task_id = "demo_self_healing_task"
    workspace_dir = Path(__file__).parent.parent

    # 2. Cleanup old DB logs
    with get_db_session() as session:
        session.query(DBSessionState).filter(DBSessionState.task_id == task_id).delete()
        session.query(DBTaskPlan).filter(DBTaskPlan.task_id == task_id).delete()

    # 3. Create buggy python script
    buggy_file = workspace_dir / "sandbox_temp.py"
    buggy_code = 'val = "hello" + 5\n'  # Will raise TypeError
    buggy_file.write_text(buggy_code, encoding="utf-8")

    # Create matching test script
    test_file = workspace_dir / "test_sandbox_temp.py"
    test_code = (
        "import sandbox_temp\n"
        "def test_val():\n"
        "    assert sandbox_temp.val == 'hello5'\n"
    )
    test_file.write_text(test_code, encoding="utf-8")

    print("[Demo] Buggy python file and test script created.")

    # Register DemoAgentExecutor
    demo_agent = DemoAgentExecutor(buggy_file)
    DIContainer.register(IAgentExecutor, demo_agent)

    # 4. Build PlanDAG
    # Running Python command directly to trigger fallback & check self-healing
    s1 = PlanStep(
        step_id=1,
        dependencies=[],
        assigned_agent="developer",
        description="RUN: python sandbox_temp.py",
    )
    dag = PlanDAG(steps=[s1])

    # Unregister IAgentExecutor temporarily to force fallback path (so it fails and triggers self-healing)
    if IAgentExecutor in DIContainer._registry:
        del DIContainer._registry[IAgentExecutor]

    print("[Demo] Starting E2E Execution Runtime...")
    executor = DIContainer.get(IPlanExecutor)

    # Temporarily register demo agent executor again so that the Self-Healing engine resolves it!
    DIContainer.register(IAgentExecutor, demo_agent)

    success = executor.execute_plan(task_id, dag)

    print("\n" + "=" * 50)
    print(f"[Demo Output] Plan Execution Status: {'SUCCESS' if success else 'FAILED'}")
    print(
        f"[Demo Output] Repaired file content: {buggy_file.read_text(encoding='utf-8').strip()}"
    )
    print("=" * 50)

    # 5. Cleanup files
    if buggy_file.exists():
        os.remove(buggy_file)
    if test_file.exists():
        os.remove(test_file)


if __name__ == "__main__":
    run_demo()
