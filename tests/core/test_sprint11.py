import unittest
from unittest.mock import patch, MagicMock

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.security.secret_manager import SecretManager
from core.security.policy_manager import RuntimePolicyManager
from core.security.audit import SecurityAuditEngine, SecurityFinding
from core.models.providers import (
    FailoverModelProvider,
    OpenAIProvider,
    AnthropicProvider,
)
from core.models.interface import ModelParameters
from core.sandbox.docker_sandbox import DockerSandbox


class TestSprint11SecurityAndRuntime(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.secret_mgr = DIContainer.get(SecretManager)
        self.policy_mgr = DIContainer.get(RuntimePolicyManager)
        self.audit_engine = DIContainer.get(SecurityAuditEngine)

    def test_secret_manager_masking(self) -> None:
        # Register a temporary secret
        self.secret_mgr.set_secret("TEST_SECRET_KEY", "super_secret_password_123")

        # Test masking in raw text
        log_message = (
            "Attempted connection with password super_secret_password_123 on database."
        )
        masked = self.secret_mgr.mask_secrets(log_message)

        self.assertNotIn("super_secret_password_123", masked)
        self.assertIn("[MASKED_TEST_SECRET_KEY]", masked)

    def test_runtime_policy_command_validation(self) -> None:
        # Test allowed command
        res = self.policy_mgr.validate_command(["python", "script.py"])
        self.assertTrue(res["allowed"])

        # Test forbidden executable
        res = self.policy_mgr.validate_command(["powershell", "Get-Process"])
        self.assertFalse(res["allowed"])
        self.assertTrue(res["needs_approval"])

        # Test destructive git command
        res = self.policy_mgr.validate_command(["git", "reset", "--hard", "HEAD"])
        self.assertFalse(res["allowed"])
        self.assertIn("Git Reset", res["reason"])

        res2 = self.policy_mgr.validate_command(["git", "push", "-f", "origin"])
        self.assertFalse(res2["allowed"])
        self.assertIn("Git Push", res2["reason"])

        # Test root/git deletion
        res3 = self.policy_mgr.validate_command(["rm", "-rf", ".git"])
        self.assertFalse(res3["allowed"])
        self.assertIn("git folder", res3["reason"])

    def test_runtime_policy_path_and_file(self) -> None:
        # Test path traversal prevention
        self.assertFalse(self.policy_mgr.validate_path("../../outside_workspace.py"))

        # Test protected configuration files
        self.assertTrue(self.policy_mgr.is_protected_file("tsconfig.json"))
        self.assertTrue(self.policy_mgr.is_protected_file("package.json"))
        self.assertFalse(self.policy_mgr.is_protected_file("utils.py"))

    def test_security_audit_findings(self) -> None:
        # Audit unsafe python source code
        unsafe_code = (
            "import os\n"
            "# Secret key\n"
            "OPENAI_KEY = 'sk-aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3a4b5c6d7e'\n"
            "os.system('rm -rf /')\n"
            "eval('x + y')\n"
            "open('../outside_dir.txt')\n"
        )
        findings = self.audit_engine.audit_code(unsafe_code, "test_file.py")

        categories = [f.category for f in findings]
        self.assertIn("SECRET_EXPOSURE", categories)
        self.assertIn("UNSAFE_SHELL", categories)
        self.assertIn("PATH_TRAVERSAL", categories)

    def test_model_provider_failover(self) -> None:
        # Create a mock provider that always crashes
        mock1 = MagicMock()
        mock1.generate.side_effect = RuntimeError("Service Unavailable")

        # Create a mock provider that succeeds
        mock2 = MagicMock()
        mock2.generate.return_value = "OpenAI response"

        failover_provider = FailoverModelProvider([mock1, mock2])
        params = ModelParameters()

        res = failover_provider.generate("Hello", "You are assistant", params)
        self.assertEqual(res, "OpenAI response")

        # Ensure both were called (mock1 failed, mock2 was invoked)
        mock1.generate.assert_called_once()
        mock2.generate.assert_called_once()

    def test_docker_sandbox_limits(self) -> None:
        sandbox = DockerSandbox(
            container_name="test_docker_sandbox",
            workspace_path="/tmp/workspace",
            cpu_limit="2.0",
            memory_limit="1024m",
            network_disabled=True,
            read_only_root=True,
        )
        self.assertEqual(sandbox.cpu_limit, "2.0")
        self.assertEqual(sandbox.memory_limit, "1024m")
        self.assertTrue(sandbox.network_disabled)
        self.assertTrue(sandbox.read_only_root)


if __name__ == "__main__":
    unittest.main()
