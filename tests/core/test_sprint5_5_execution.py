import unittest
from typing import Dict, List

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.queue.scheduler import PlanStep, PlanDAG
from core.queue.execution_runtime import (
    IPlanExecutor,
    IAgentExecutor,
    EngineeringExecutionRuntime,
)
from core.sandbox.interface import ISandbox
from core.workspace.session_manager import DBSessionState
from core.database import get_db_session


class MockAgentExecutor(IAgentExecutor):
    """
    Mock agent executor that fails on specific step IDs to test halting and cancellation.
    """

    def __init__(self, fail_on_step_ids: List[int]) -> None:
        self.fail_on_step_ids = fail_on_step_ids
        self.executed_steps: List[int] = []

    def execute_step(
        self, task_id: str, step: PlanStep, workspace_path: str, sandbox: ISandbox
    ) -> bool:
        self.executed_steps.append(step.step_id)
        if step.step_id in self.fail_on_step_ids:
            return False
        return True


class TestExecutionRuntime(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.executor = DIContainer.get(IPlanExecutor)
        self.task_id = "test_sprint5_5_task"

        # Clean DB session states to prevent leaks
        with get_db_session() as session:
            session.query(DBSessionState).filter(
                DBSessionState.task_id == self.task_id
            ).delete()
            try:
                from core.queue.hitl import DBTaskPlan

                session.query(DBTaskPlan).filter(
                    DBTaskPlan.task_id == self.task_id
                ).delete()
            except Exception:
                pass

    def tearDown(self) -> None:
        # Clean workspace session
        try:
            from core.workspace.interface import IWorkspaceSessionManager

            session_mgr = DIContainer.get(IWorkspaceSessionManager)
            session_mgr.end_session(self.task_id)
        except Exception:
            pass

    def test_di_registration(self) -> None:
        self.assertTrue(isinstance(self.executor, EngineeringExecutionRuntime))

    def test_execution_all_success(self) -> None:
        # Step 1 -> Step 2 -> Step 3
        s1 = PlanStep(
            step_id=1, dependencies=[], assigned_agent="developer", description="Step 1"
        )
        s2 = PlanStep(
            step_id=2, dependencies=[1], assigned_agent="reviewer", description="Step 2"
        )
        s3 = PlanStep(
            step_id=3,
            dependencies=[2],
            assigned_agent="developer",
            description="Step 3",
        )
        dag = PlanDAG(steps=[s1, s2, s3])

        # Mock agent executor to prevent real LLM network queries
        mock_agent = MockAgentExecutor(fail_on_step_ids=[])
        DIContainer.register(IAgentExecutor, mock_agent)

        # Run E2E plan execution
        success = self.executor.execute_plan(self.task_id, dag)
        self.assertTrue(success)

        # Assert status updates
        self.assertEqual(s1.status, "completed")
        self.assertEqual(s2.status, "completed")
        self.assertEqual(s3.status, "completed")

    def test_execution_failure_and_halt(self) -> None:
        # Step 1 -> Step 2 -> Step 3 (Step 2 will fail)
        s1 = PlanStep(
            step_id=1, dependencies=[], assigned_agent="developer", description="Step 1"
        )
        s2 = PlanStep(
            step_id=2, dependencies=[1], assigned_agent="reviewer", description="Step 2"
        )
        s3 = PlanStep(
            step_id=3,
            dependencies=[2],
            assigned_agent="developer",
            description="Step 3",
        )
        dag = PlanDAG(steps=[s1, s2, s3])

        # Register MockAgentExecutor failing on Step 2
        mock_agent = MockAgentExecutor(fail_on_step_ids=[2])
        DIContainer.register(IAgentExecutor, mock_agent)

        success = self.executor.execute_plan(self.task_id, dag)
        self.assertFalse(success)

        # Assert execution halting statuses
        self.assertEqual(s1.status, "completed")
        self.assertEqual(s2.status, "failed")
        self.assertEqual(
            s3.status, "cancelled"
        )  # Downstream cancelled because parent failed

        # Verify only step 1 and 2 were actually executed (step 3 was cancelled)
        self.assertIn(1, mock_agent.executed_steps)
        self.assertIn(2, mock_agent.executed_steps)
        self.assertNotIn(3, mock_agent.executed_steps)

    def test_execution_sandbox_fallback_command(self) -> None:
        # Executes an actual command inside the sandbox fallback
        s1 = PlanStep(
            step_id=1,
            dependencies=[],
            assigned_agent="developer",
            description="RUN: python -c \"print('Hello from test')\"",
        )
        dag = PlanDAG(steps=[s1])

        # Remove IAgentExecutor registration to force fallback command runner path
        if IAgentExecutor in DIContainer._registry:
            del DIContainer._registry[IAgentExecutor]

        success = self.executor.execute_plan(self.task_id, dag)
        self.assertTrue(success)
        self.assertEqual(s1.status, "completed")
