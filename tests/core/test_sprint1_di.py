import unittest
from typing import List

from core.di import DIContainer
from core.sandbox.interface import ISandbox, SandboxExecutionResult


# Concrete implementation to test protocol compliance and DI registration
class MockSandbox:
    def create(self) -> None:
        pass

    def initialize(self) -> None:
        pass

    def start(self) -> None:
        pass

    def execute(self, cmd: List[str], timeout: float = 30.0) -> SandboxExecutionResult:
        return SandboxExecutionResult(
            exit_code=0,
            stdout="success",
            stderr="",
            duration_seconds=0.1,
            timeout_exceeded=False,
        )

    def copy_in(self, local_path: str, remote_path: str) -> None:
        pass

    def copy_out(self, remote_path: str, local_path: str) -> None:
        pass

    def destroy(self) -> None:
        pass

    def terminate(self) -> None:
        pass

    def health_check(self) -> bool:
        return True


class TestDIAndInterfaces(unittest.TestCase):
    def setUp(self) -> None:
        DIContainer.clear()

    def tearDown(self) -> None:
        DIContainer.clear()

    def test_protocol_conformance(self) -> None:
        # Verify that MockSandbox complies with the ISandbox protocol at runtime
        sandbox_instance = MockSandbox()
        self.assertTrue(isinstance(sandbox_instance, ISandbox))

    def test_di_container_registration_and_retrieval(self) -> None:
        # Register the protocol with our mock implementation
        sandbox_instance = MockSandbox()
        DIContainer.register(ISandbox, sandbox_instance)

        # Retrieve the registered instance
        retrieved_instance = DIContainer.get(ISandbox)
        self.assertEqual(retrieved_instance, sandbox_instance)
        self.assertTrue(isinstance(retrieved_instance, ISandbox))

    def test_di_container_missing_registration_raises_error(self) -> None:
        with self.assertRaises(KeyError):
            DIContainer.get(ISandbox)
