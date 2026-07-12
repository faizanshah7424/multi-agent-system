import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    """Unified system configuration schema supporting validation."""

    env: str = Field(
        "development", description="Environment: development, production, enterprise"
    )
    gemini_api_key: str = Field("", description="Google Gemini API credential key")
    openai_api_key: str = Field("", description="OpenAI API key")
    anthropic_api_key: str = Field("", description="Anthropic API key")
    database_url: str = Field(
        "sqlite:///data/system.db", description="Database connection URL"
    )
    api_host: str = Field("127.0.0.1", description="FastAPI host address")
    api_port: int = Field(8000, description="FastAPI port")
    persist_dir: str = Field(
        "data", description="Directory path for local files persistence"
    )
    workspace_dir: str = Field("worktrees", description="Workspace root directory")


class ConfigurationManager:
    """
    Unified Configuration Manager.
    Validates configuration parameters prior to bootstrapping the runtime.
    """

    def __init__(self, env: Optional[str] = None) -> None:
        self.env = env or os.getenv("ENVIRONMENT", "development")
        self.config = self._load_config()

    def _load_config(self) -> SystemConfig:
        return SystemConfig(
            env=self.env,
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            database_url=os.getenv("DATABASE_URL", "sqlite:///data/system.db"),
            api_host=os.getenv("API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("API_PORT", "8000")),
            persist_dir=os.getenv("PERSIST_DIR", "data"),
            workspace_dir=os.getenv("WORKSPACE_DIR", "worktrees"),
        )

    def validate(self) -> Dict[str, Any]:
        """
        Validates all configuration parameters.
        Returns a dictionary indicating verification status and any error messages.
        """
        errors = []

        # 1. Port range check
        if not (1024 <= self.config.api_port <= 65535):
            errors.append(
                f"Invalid API_PORT: {self.config.api_port}. Must be between 1024 and 65535."
            )

        # 2. Database Dialect check
        if not (
            self.config.database_url.startswith("sqlite")
            or self.config.database_url.startswith("postgresql")
        ):
            errors.append(
                f"Unsupported DATABASE_URL dialect. Supported: sqlite, postgresql."
            )

        # 3. Environment credentials check
        if self.config.env == "production" and not self.config.gemini_api_key:
            errors.append(
                "Production environment requires GEMINI_API_KEY to be configured."
            )

        # 4. Check persistence directory path validation
        try:
            p = Path(self.config.persist_dir)
            # Ensure it is not empty
            if not self.config.persist_dir:
                errors.append("PERSIST_DIR cannot be empty.")
        except Exception as e:
            errors.append(f"Invalid PERSIST_DIR path format: {e}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "config": self.config.model_dump(),
        }
