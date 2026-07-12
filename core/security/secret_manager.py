import os
from typing import Dict


class SecretManager:
    """
    Enterprise-grade Secret Manager subsystem.
    Handles storage of credentials, environment validations, secret rotation interfaces,
    and log masking to prevent leaks in telemetry.
    """

    def __init__(self) -> None:
        self._secrets: Dict[str, str] = {}
        self.load_secrets()

    def load_secrets(self) -> None:
        """Loads secrets from environmental variables."""
        for key in [
            "GEMINI_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "POSTGRES_PASSWORD",
            "AWS_SECRET_ACCESS_KEY",
        ]:
            val = os.getenv(key, "")
            if val:
                self._secrets[key] = val

    def get_secret(self, key: str, default: str = "") -> str:
        """Retrieves a secret value by key."""
        return self._secrets.get(key, os.getenv(key, default))

    def set_secret(self, key: str, value: str) -> None:
        """Sets or updates a secret value (e.g., during rotation)."""
        self._secrets[key] = value
        # Sync to environment for subprocesses if necessary
        os.environ[key] = value

    def validate_environment(self) -> Dict[str, bool]:
        """Checks if all required model provider keys are configured."""
        return {
            "GEMINI_API_KEY": bool(self.get_secret("GEMINI_API_KEY")),
            "OPENAI_API_KEY": bool(self.get_secret("OPENAI_API_KEY")),
            "ANTHROPIC_API_KEY": bool(self.get_secret("ANTHROPIC_API_KEY")),
        }

    def mask_secrets(self, text: str) -> str:
        """Masks sensitive strings within text lines."""
        if not text:
            return text
        masked = text
        for key, val in self._secrets.items():
            if val and len(val) > 4:
                masked = masked.replace(val, f"[MASKED_{key}]")
        return masked
