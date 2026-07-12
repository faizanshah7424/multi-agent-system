import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator, List, Type, TypeVar
from pydantic import BaseModel

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.models.interface import IModelProvider, ModelParameters
from core.queue.scheduler import PlanStep
from core.queue.agent_executor import AgentDecision, AgentExecutor
from core.queue.execution_runtime import IAgentExecutor, IPlanExecutor
from core.sandbox.interface import ISandbox
from core.sandbox.local_sandbox import LocalProcessSandbox
from core.workspace.session_manager import DBSessionState
from core.database import get_db_session

T = TypeVar("T", bound=BaseModel)

class MockAgentModelProvider(IModelProvider):
    """
    Mock model provider that returns a sequence of AgentDecisions to simulate ReAct.
    """
    def __init__(self, decisions: List[AgentDecision]) -> None:
        self.decisions = decisions
        self.current_idx = 0
        self.last_system_instruction = None

    def generate(self, prompt: str, system_instruction: str, params: ModelParameters) -> str:
        return ""

    def generate_structured(self, prompt: str, schema: Type[T], system_instruction: str, params: ModelParameters) -> T:
        self.last_system_instruction = system_instruction
        if self.current_idx < len(self.decisions):
            decision = self.decisions[self.current_idx]
            self.current_idx += 1
            return decision
        return AgentDecision(
            thought="No more actions, respond success.",
            action="respond",
            final_answer="Done"
        )

    def generate_stream(self, prompt: str, system_instruction: str, params: ModelParameters) -> Iterator[str]:
        yield ""

class TestAgentExecutorFramework(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.agent_executor = DIContainer.get(IAgentExecutor)
        self.task_id = "test_sprint6_task"

        # Clean DB session states to prevent leaks
        with get_db_session() as session:
            session.query(DBSessionState).filter(DBSessionState.task_id == self.task_id).delete()

    def tearDown(self) -> None:
        # Clean workspace session
        try:
            from core.workspace.interface import IWorkspaceSessionManager
            session_mgr = DIContainer.get(IWorkspaceSessionManager)
            session_mgr.end_session(self.task_id)
        except Exception:
            pass

    def test_di_registration(self) -> None:
        self.assertTrue(isinstance(self.agent_executor, AgentExecutor))

    def test_react_loop_routing(self) -> None:
        # Define a sequence of 3 ReAct actions:
        # 1. Write a file
        # 2. Read the file to verify
        # 3. Final answer (respond)
        decisions = [
            AgentDecision(
                thought="I will write a test file first.",
                action="write_file",
                file_path="react_test_file.txt",
                content="hello react world"
            ),
            AgentDecision(
                thought="Now I will read the file to confirm it was written.",
                action="read_file",
                file_path="react_test_file.txt"
            ),
            AgentDecision(
                thought="Success, I am ready to complete the task.",
                action="respond",
                final_answer="File verified successfully."
            )
        ]

        # Register MockAgentModelProvider
        mock_provider = MockAgentModelProvider(decisions)
        DIContainer.register(IModelProvider, mock_provider)

        with TemporaryDirectory() as temp_dir:
            sandbox = LocalProcessSandbox(temp_dir)
            sandbox.start()

            step = PlanStep(
                step_id=1,
                dependencies=[],
                assigned_agent="developer",
                description="Write and verify react_test_file.txt"
            )

            # Trigger execution
            success = self.agent_executor.execute_step(self.task_id, step, temp_dir, sandbox)
            self.assertTrue(success)

            # Assert target file was physically created in the workspace path
            target_path = Path(temp_dir) / "react_test_file.txt"
            self.assertTrue(target_path.exists())
            self.assertEqual(target_path.read_text(encoding="utf-8"), "hello react world")

            # Assert system instructions loaded correct profile variables
            self.assertIn("Developer Agent", mock_provider.last_system_instruction)
            self.assertIn("Write and verify react_test_file.txt", mock_provider.last_system_instruction)

            sandbox.terminate()

    def test_local_sandbox_command_sanitization(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sandbox = LocalProcessSandbox(temp_dir)
            sandbox.start()

            # Test safe command
            res_safe = sandbox.execute(["python", "-c", "print('safe')"])
            self.assertEqual(res_safe.exit_code, 0)

            # Test command chain using semicolon
            res_semicolon = sandbox.execute(["python", "-c", "print('unsafe')", ";", "echo", "injected"])
            self.assertEqual(res_semicolon.exit_code, -1)
            self.assertIn("Access Denied", res_semicolon.stderr)

            # Test command chain using &&
            res_and = sandbox.execute(["python", "-c", "print('unsafe')", "&&", "echo"])
            self.assertEqual(res_and.exit_code, -1)
            self.assertIn("Access Denied", res_and.stderr)

            # Test redirect operator
            res_redirect = sandbox.execute(["echo", "injected", ">", "out.txt"])
            self.assertEqual(res_redirect.exit_code, -1)
            self.assertIn("Access Denied", res_redirect.stderr)

            sandbox.terminate()
