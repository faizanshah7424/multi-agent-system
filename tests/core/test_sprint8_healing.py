import unittest
from typing import Dict, Any, List

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.queue.scheduler import PlanStep
from core.queue.self_healing import SelfHealingEngine, ISelfHealingEngine
from core.queue.execution_runtime import IAgentExecutor
from core.sandbox.interface import ISandbox, SandboxExecutionResult


class MockAgentExecutor(IAgentExecutor):
    def __init__(self) -> None:
        self.call_count = 0

    def execute_step(
        self, task_id: str, step: PlanStep, workspace_path: str, sandbox: Any
    ) -> bool:
        self.call_count += 1
        return True


class MockSandbox(ISandbox):
    def __init__(self, fail_attempts: int) -> None:
        self.fail_attempts = fail_attempts
        self.call_count = 0

    def start(self) -> None:
        pass

    def terminate(self) -> None:
        pass

    def execute(self, cmd: List[str]) -> SandboxExecutionResult:
        if cmd[0] == "ruff":
            self.call_count += 1

        if self.call_count <= self.fail_attempts:
            return SandboxExecutionResult(
                exit_code=1,
                stdout="",
                stderr="Validation failure simulated.",
                duration_seconds=0.01,
                timeout_exceeded=False,
            )
        return SandboxExecutionResult(
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=0.01,
            timeout_exceeded=False,
        )


class TestSelfHealingEngine(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.engine = DIContainer.get("self_healing_engine")
        self.mock_agent = MockAgentExecutor()
        DIContainer.register(IAgentExecutor, self.mock_agent)

    def test_di_registration(self) -> None:
        self.assertTrue(isinstance(self.engine, SelfHealingEngine))

    def test_python_traceback_parsing(self) -> None:
        log = (
            'File "core/utils.py", line 45, in format_text\n'
            "    res = val + 10\n"
            'TypeError: can only concatenate str (not "int") to str'
        )
        res = self.engine.classify_failure(log)
        self.assertIsNotNone(res)
        self.assertEqual(res.category, "TYPE_ERROR")
        self.assertEqual(res.file_path, "core/utils.py")
        self.assertEqual(res.line_number, 45)
        self.assertIn("TypeError", res.message)

    def test_ruff_lint_parsing(self) -> None:
        log = "core/utils.py:12:8: F821 Undefined name 'undefined_var'"
        res = self.engine.classify_failure(log)
        self.assertIsNotNone(res)
        self.assertEqual(res.category, "LINT_ERROR")
        self.assertEqual(res.file_path, "core/utils.py")
        self.assertEqual(res.line_number, 12)
        self.assertEqual(res.column_number, 8)
        self.assertIn("F821", res.message)

    def test_pytest_failure_parsing(self) -> None:
        log = (
            ">       assert math_op(5) == 25\n"
            "E       AssertionError: assert 10 == 25\n"
            "\n"
            "tests/test_math.py:15: AssertionError"
        )
        res = self.engine.classify_failure(log)
        self.assertIsNotNone(res)
        self.assertEqual(res.category, "UNIT_TEST_FAILURE")
        self.assertEqual(res.file_path, "tests/test_math.py")
        self.assertEqual(res.line_number, 15)

    def test_tsc_parsing(self) -> None:
        log = "src/app.ts(30,12): error TS2304: Cannot find name 'Config'."
        res = self.engine.classify_failure(log)
        self.assertIsNotNone(res)
        self.assertEqual(res.category, "TYPE_ERROR")
        self.assertEqual(res.file_path, "src/app.ts")
        self.assertEqual(res.line_number, 30)
        self.assertEqual(res.column_number, 12)

    def test_eslint_parsing(self) -> None:
        log = "src/app.js: line 20, col 5, Error - Unexpected console statement."
        res = self.engine.classify_failure(log)
        self.assertIsNotNone(res)
        self.assertEqual(res.category, "LINT_ERROR")
        self.assertEqual(res.file_path, "src/app.js")
        self.assertEqual(res.line_number, 20)
        self.assertEqual(res.column_number, 5)

    def test_safety_gate_blocking_test_edits(self) -> None:
        log = (
            'File "tests/test_helper.py", line 10, in test_run\n'
            "    res = 1 / 0\n"
            "ZeroDivisionError: division by zero"
        )
        step = PlanStep(
            step_id=1,
            dependencies=[],
            assigned_agent="developer",
            description="Fix test division",
        )
        sandbox = MockSandbox(fail_attempts=0)

        # Should block and return False immediately due to safety rules
        repaired = self.engine.repair_failure(
            "task_123", step, log, "dummy_path", sandbox
        )
        self.assertFalse(repaired)
        self.assertEqual(self.mock_agent.call_count, 0)

    def test_successful_repair_loop(self) -> None:
        # Fails once, succeeds on second attempt
        sandbox = MockSandbox(fail_attempts=1)
        log = "core/module.py:10:5: F821 Undefined name 'x'"
        step = PlanStep(
            step_id=1,
            dependencies=[],
            assigned_agent="developer",
            description="Fix variable",
        )

        repaired = self.engine.repair_failure(
            "task_123", step, log, "dummy_path", sandbox
        )
        self.assertTrue(repaired)
        self.assertEqual(self.mock_agent.call_count, 2)  # Two attempts executed

    def test_failed_repair_loop_exceeding_max_attempts(self) -> None:
        # Fails continually
        sandbox = MockSandbox(fail_attempts=5)
        log = "core/module.py:10:5: F821 Undefined name 'x'"
        step = PlanStep(
            step_id=1,
            dependencies=[],
            assigned_agent="developer",
            description="Fix variable",
        )

        repaired = self.engine.repair_failure(
            "task_123", step, log, "dummy_path", sandbox
        )
        self.assertFalse(repaired)
        self.assertEqual(
            self.mock_agent.call_count, 3
        )  # Exact max of 3 attempts executed
