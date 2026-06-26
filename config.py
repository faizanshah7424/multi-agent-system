import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings and configuration loaded from environment variables and .env file.
    """
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    default_model: str = Field(default="gemini-2.5-flash", validation_alias="DEFAULT_MODEL")
    
    # Model configuration for specific agents
    planner_model: str = Field(default="gemini-2.5-flash", validation_alias="PLANNER_MODEL")
    researcher_model: str = Field(default="gemini-2.5-flash", validation_alias="RESEARCHER_MODEL")
    developer_model: str = Field(default="gemini-2.5-flash", validation_alias="DEVELOPER_MODEL")
    reviewer_model: str = Field(default="gemini-2.5-flash", validation_alias="REVIEWER_MODEL")
    
    # API endpoints configuration
    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    
    # Logger level and paths
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    persist_dir: str = Field(default="data", validation_alias="PERSIST_DIR")
    
    # Configurable pricing model for models per 1M tokens
    model_pricing: dict[str, dict[str, float]] = Field(
        default={
            "gemini-2.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
            "gemini-2.5-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
            "text-embedding-004": {"input": 0.025 / 1_000_000, "output": 0.0},
        },
        validation_alias="MODEL_PRICING"
    )

    # Configuration metadata
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def persist_path(self) -> Path:
        """Returns the resolved persistence directory path."""
        path = Path(self.persist_dir)
        if not path.is_absolute():
            # Treat relative paths relative to current workspace directory
            path = Path(__file__).parent.resolve() / path
        return path

# Initialize configurations
settings = Settings()
