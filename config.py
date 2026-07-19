import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """
    Application settings and configuration loaded from environment variables and .env file.
    """

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    default_model: str = Field(
        default="gemini-2.5-flash", validation_alias="DEFAULT_MODEL"
    )

    # Model configuration for specific agents
    planner_model: str = Field(
        default="gemini-2.5-flash", validation_alias="PLANNER_MODEL"
    )
    researcher_model: str = Field(
        default="gemini-2.5-flash", validation_alias="RESEARCHER_MODEL"
    )
    developer_model: str = Field(
        default="gemini-2.5-flash", validation_alias="DEVELOPER_MODEL"
    )
    reviewer_model: str = Field(
        default="gemini-2.5-flash", validation_alias="REVIEWER_MODEL"
    )

    # API endpoints configuration
    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    # Logger level and paths
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    persist_dir: str = Field(default="data", validation_alias="PERSIST_DIR")

    # Configurable pricing model for models per 1M tokens
    model_pricing: dict[str, dict[str, float]] = Field(
        default={
            "gemini-2.5-flash": {
                "input": 0.075 / 1_000_000,
                "output": 0.30 / 1_000_000,
            },
            "gemini-2.5-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
            "text-embedding-004": {"input": 0.025 / 1_000_000, "output": 0.0},
        },
        validation_alias="MODEL_PRICING",
    )

    # Context Optimization settings
    enable_context_optimization: bool = Field(default=True, validation_alias="ENABLE_CONTEXT_OPTIMIZATION")
    sqlite_use_wal: bool = Field(default=True, validation_alias="SQLITE_USE_WAL")
    sqlite_busy_timeout: int = Field(default=5000, validation_alias="SQLITE_BUSY_TIMEOUT")
    context_isolation_start_tag: str = Field(default="<source_context>", validation_alias="CONTEXT_ISOLATION_START_TAG")
    context_isolation_end_tag: str = Field(default="</source_context>", validation_alias="CONTEXT_ISOLATION_END_TAG")

    # Reranker settings
    reranker_enabled: bool = Field(default=False, validation_alias="RERANKER_ENABLED")
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", validation_alias="RERANKER_MODEL")
    rerank_top_k: int = Field(default=3, validation_alias="RERANK_TOP_K")
    rerank_score_threshold: float = Field(default=0.0, validation_alias="RERANK_SCORE_THRESHOLD")
    rerank_batch_size: int = Field(default=16, validation_alias="RERANK_BATCH_SIZE")
    rerank_device: str = Field(default="cpu", validation_alias="RERANK_DEVICE")

    # Database & Multi-Tenant Settings
    database_backend: str = Field(default="sqlite", validation_alias="DATABASE_BACKEND")
    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    sqlite_path: str = Field(default="", validation_alias="SQLITE_PATH")
    postgres_pool_size: int = Field(default=10, validation_alias="POSTGRES_POOL_SIZE")
    postgres_timeout: float = Field(default=30.0, validation_alias="POSTGRES_TIMEOUT")
    enable_multi_tenancy: bool = Field(default=False, validation_alias="ENABLE_MULTI_TENANCY")
    default_tenant_id: str = Field(default="default_tenant", validation_alias="DEFAULT_TENANT_ID")


    # Configuration metadata
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
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
