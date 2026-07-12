from pathlib import Path
from pydantic import BaseModel, Field
from tools.base import BaseTool, validate_safe_path
from core.logging import get_logger

logger = get_logger("FileWriterTool")


class FileWriterInput(BaseModel):
    file_path: str = Field(
        ..., description="The absolute or relative path to the file to write."
    )
    content: str = Field(..., description="The text content to write to the file.")


class FileWriterTool(BaseTool):
    name: str = "file_writer"
    description: str = (
        "Writes content to a file on the filesystem. "
        "Will create parent directories if they do not exist and overwrite existing files."
    )
    args_schema: type[BaseModel] = FileWriterInput

    def execute(self, file_path: str, content: str) -> str:
        # Enforce content size limit of 10MB
        if len(content.encode("utf-8")) > 10 * 1024 * 1024:
            return (
                "Error: Content size exceeds the maximum permitted write limit of 10MB."
            )

        # Verify against forbidden system files and directories
        import re

        forbidden_patterns = [
            r"(?i)[/\\]\.ssh[/\\]",
            r"(?i)[/\\]\.git[/\\]",
            r"(?i)authorized_keys$",
            r"(?i)\.bashrc$",
            r"(?i)\.bash_profile$",
            r"(?i)\.profile$",
            r"(?i)\.zshrc$",
            r"(?i)\.bash_history$",
            r"(?i)ntuser\.dat$",
            r"(?i)desktop\.ini$",
            r"(?i)thumbs\.db$",
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, file_path):
                return f"Error: Write denied to forbidden destination pattern: '{file_path}'"

        try:
            path = validate_safe_path(file_path)
        except ValueError as ve:
            return f"Error: {ve}"

        logger.info(f"Writing to file: {path}")

        try:
            # Create parent directories recursively if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write contents to file using UTF-8
            path.write_text(content, encoding="utf-8")
            return f"Success: File written successfully to '{file_path}'"
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {str(e)}")
            return f"Error: Failed to write to file: {str(e)}"
