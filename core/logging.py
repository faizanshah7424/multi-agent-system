import logging
import sys
import contextvars
import uuid
from pathlib import Path
from config import settings

# Define context variables for correlation tracking
correlation_context = contextvars.ContextVar(
    "correlation_context",
    default={
        "task_id": "N/A",
        "workflow_id": "N/A",
        "agent_name": "N/A",
        "execution_id": "N/A",
        "request_id": "N/A",
        "session_id": "N/A",
    },
)


def set_correlation_context(
    task_id: str = "N/A",
    workflow_id: str = "N/A",
    agent_name: str = "N/A",
    execution_id: Optional[str] = None,
    request_id: str = "N/A",
    session_id: str = "N/A",
):
    correlation_context.set(
        {
            "task_id": task_id,
            "workflow_id": workflow_id,
            "agent_name": agent_name,
            "execution_id": execution_id or f"exec_{uuid.uuid4().hex[:8]}",
            "request_id": request_id,
            "session_id": session_id,
        }
    )


def get_correlation_context() -> dict:
    return correlation_context.get()


class CorrelationFilter(logging.Filter):
    """
    Injects context variables (task_id, workflow_id, agent_name, execution_id)
    directly into each LogRecord.
    """

    def filter(self, record):
        context = correlation_context.get()
        record.task_id = context.get("task_id", "N/A")
        record.workflow_id = context.get("workflow_id", "N/A")
        record.agent_name = context.get("agent_name", "N/A")
        record.execution_id = context.get("execution_id", "N/A")
        return True


from typing import Optional


class SecretRedactingFormatter(logging.Formatter):
    """
    Custom Formatter that redacts sensitive strings, API keys, and authorization headers from log messages.
    """

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        import re
        from config import settings

        # Redact the configured Gemini API key if present
        gemini_key = getattr(settings, "gemini_api_key", None)
        if gemini_key and len(gemini_key) > 5:
            original = original.replace(gemini_key, "[REDACTED_GEMINI_KEY]")

        # Redact common Gemini API Key patterns (AIzaSy...)
        original = re.sub(
            r"AIzaSy[a-zA-Z0-9_\-]{33}", "[REDACTED_GEMINI_KEY]", original
        )

        # Redact generic bearer tokens
        original = re.sub(
            r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]+", r"\1[REDACTED]", original
        )

        # Redact common password / key query params and json keys
        original = re.sub(
            r'(?i)(api_key\s*=\s*["\']?)[a-zA-Z0-9_\-]{16,}', r"\1[REDACTED]", original
        )
        original = re.sub(
            r'(?i)(password\s*=\s*["\']?)[a-zA-Z0-9_\-]{4,}', r"\1[REDACTED]", original
        )
        original = re.sub(
            r'(?i)("api_key"\s*:\s*["\']?)[a-zA-Z0-9_\-]{16,}',
            r"\1[REDACTED]",
            original,
        )
        original = re.sub(
            r'(?i)("password"\s*:\s*["\']?)[a-zA-Z0-9_\-]{4,}',
            r"\1[REDACTED]",
            original,
        )

        # Dynamic SecretManager masking
        try:
            from core.di import DIContainer
            from core.security.secret_manager import SecretManager

            secret_mgr = DIContainer.get(SecretManager)
            original = secret_mgr.mask_secrets(original)
        except Exception:
            pass

        return original


def get_logger(name: str) -> logging.Logger:
    """
    Get a pre-configured logger with the app's standard format, correlation filtering, and log level.
    """
    logger = logging.getLogger(name)

    # If the logger already has handlers, don't add more (prevents duplicate logs)
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level.upper())

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level.upper())
    console_handler.addFilter(CorrelationFilter())

    # Formatter with log correlation properties and secret redaction
    formatter = SecretRedactingFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [task:%(task_id)s|wf:%(workflow_id)s|agent:%(agent_name)s|exec:%(execution_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file logger if persistence dir is setup
    try:
        persist_path = settings.persist_path
        persist_path.mkdir(parents=True, exist_ok=True)
        log_file = persist_path / "system.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(settings.log_level.upper())
        file_handler.addFilter(CorrelationFilter())
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        # Fallback if file writing fails
        pass

    return logger
