import unittest
import time
from typing import Dict, Any, List

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.broker.interface import IEventBroker
from core.broker.events import WebSocketEventBroker
from core.queue.scheduler import PlanStep, PlanDAG
from core.queue.execution_runtime import IPlanExecutor, IAgentExecutor
from core.queue.hitl import HITLOrchestrator, DBTaskPlan
from core.workspace.session_manager import DBSessionState
from core.database import get_db_session


class MockAgentExecutor(IAgentExecutor):
    def __init__(self) -> None:
        self.executed_steps = []

    def execute_step(
        self, task_id: str, step: PlanStep, workspace_path: str, sandbox: Any
    ) -> bool:
        self.executed_steps.append(step.step_id)
        return True


class TestHITLAndBroker(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.broker = DIContainer.get(IEventBroker)
        self.hitl_orchestrator = DIContainer.get("hitl_orchestrator")
        self.plan_executor = DIContainer.get(IPlanExecutor)
        self.task_id = "test_sprint7_task"

        # Mock agent executor to prevent real LLM network queries
        self.mock_agent = MockAgentExecutor()
        DIContainer.register(IAgentExecutor, self.mock_agent)

        # Cleanup DB records
        with get_db_session() as session:
            session.query(DBSessionState).filter(
                DBSessionState.task_id == self.task_id
            ).delete()
            session.query(DBTaskPlan).filter(
                DBTaskPlan.task_id == self.task_id
            ).delete()

    def tearDown(self) -> None:
        try:
            from core.workspace.interface import IWorkspaceSessionManager

            session_mgr = DIContainer.get(IWorkspaceSessionManager)
            session_mgr.end_session(self.task_id)
        except Exception:
            pass

    def test_di_registrations(self) -> None:
        self.assertTrue(isinstance(self.broker, WebSocketEventBroker))
        self.assertTrue(isinstance(self.hitl_orchestrator, HITLOrchestrator))

    def test_websocket_pub_sub(self) -> None:
        received_messages: List[Dict[str, Any]] = []

        def callback(msg: Dict[str, Any]) -> None:
            received_messages.append(msg)

        # Subscribe
        self.broker.subscribe("agent_reasoning", callback)

        # Publish
        test_msg = {"thought": "I will scan files.", "action": "dir_scanner"}
        self.broker.publish("agent_reasoning", test_msg)

        # Wait for async thread callback delivery
        time.sleep(0.1)
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0]["thought"], "I will scan files.")

        # Unsubscribe
        self.broker.unsubscribe("agent_reasoning", callback)
        self.broker.publish("agent_reasoning", {"thought": "Another thinking."})

        time.sleep(0.1)
        self.assertEqual(len(received_messages), 1)  # Stays 1, callback unsubscribed

    def test_hitl_orchestration_pause_and_resume(self) -> None:
        # Step 1: No approval needed
        # Step 2: Requires Git Merge Approval (triggers keyword "merge")
        # Step 3: No approval needed
        s1 = PlanStep(
            step_id=1,
            dependencies=[],
            assigned_agent="developer",
            description="Step 1 description",
        )
        s2 = PlanStep(
            step_id=2,
            dependencies=[1],
            assigned_agent="reviewer",
            description="Merge task branch back to main",
        )
        s3 = PlanStep(
            step_id=3,
            dependencies=[2],
            assigned_agent="developer",
            description="Step 3 description",
        )
        dag = PlanDAG(steps=[s1, s2, s3])

        # 1. Execute plan (should pause on Step 2)
        success = self.plan_executor.execute_plan(self.task_id, dag)
        self.assertFalse(success)  # Suspend/pause returns False

        # 2. Assert step statuses after pause
        updated_plan = self.hitl_orchestrator.get_plan(self.task_id)
        self.assertIsNotNone(updated_plan)
        self.assertEqual(updated_plan.steps[0].status, "completed")
        self.assertEqual(updated_plan.steps[1].status, "waiting_for_approval")
        self.assertEqual(updated_plan.steps[2].status, "pending")

        # 3. Approve Step 2
        approved = self.hitl_orchestrator.approve_step(self.task_id, 2)
        self.assertTrue(approved)

        # 4. Resume plan execution (loads state and continues)
        resume_success = self.plan_executor.execute_plan(self.task_id, dag)
        self.assertTrue(resume_success)

        # 5. Assert all steps completed
        final_plan = self.hitl_orchestrator.get_plan(self.task_id)
        self.assertEqual(final_plan.steps[0].status, "completed")
        self.assertEqual(final_plan.steps[1].status, "completed")
        self.assertEqual(final_plan.steps[2].status, "completed")

    def test_hitl_rejection(self) -> None:
        s1 = PlanStep(
            step_id=1,
            dependencies=[],
            assigned_agent="developer",
            description="Step 1 description",
        )
        s2 = PlanStep(
            step_id=2,
            dependencies=[1],
            assigned_agent="reviewer",
            description="Merge task branch back to main",
        )
        s3 = PlanStep(
            step_id=3,
            dependencies=[2],
            assigned_agent="developer",
            description="Step 3 description",
        )
        dag = PlanDAG(steps=[s1, s2, s3])

        # Execute plan to trigger pause
        self.plan_executor.execute_plan(self.task_id, dag)

        # Reject Step 2
        self.hitl_orchestrator.reject_step(
            self.task_id, 2, "Dangerous command check failed."
        )

        # Assert status propagation
        rejected_plan = self.hitl_orchestrator.get_plan(self.task_id)
        self.assertEqual(rejected_plan.steps[0].status, "completed")
        self.assertEqual(rejected_plan.steps[1].status, "failed")
        self.assertEqual(rejected_plan.steps[2].status, "cancelled")
