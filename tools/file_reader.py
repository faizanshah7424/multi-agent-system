from pathlib import Path
from pydantic import BaseModel, Field
from tools.base import BaseTool, validate_safe_path
from core.logging import get_logger

logger = get_logger("FileReaderTool")

class FileReaderInput(BaseModel):
    file_path: str = Field(
        ..., 
        description="The absolute or relative path to the file to be read."
    )

class FileReaderTool(BaseTool):
    name: str = "file_reader"
    description: str = (
        "Reads and returns the complete text content of a file on the filesystem. "
        "Useful for inspecting code, logs, and configurations."
    )
    args_schema: type[BaseModel] = FileReaderInput

    def execute(self, file_path: str) -> str:
        try:
            path = validate_safe_path(file_path)
        except ValueError as ve:
            return f"Error: {ve}"
            
        logger.info(f"Reading file: {path}")
        
        if not path.exists():
            return f"Error: File '{file_path}' does not exist at path '{path}'"
            
        if not path.is_file():
            return f"Error: Path '{file_path}' is a directory, not a file."
            
        # Enforce maximum file size limit (10MB) to prevent memory exhaustion
        try:
            if path.stat().st_size > 10 * 1024 * 1024:
                return f"Error: File '{file_path}' size ({path.stat().st_size} bytes) exceeds the maximum permitted read limit of 10MB."
        except Exception as e:
            logger.warning(f"Could not check file size for {file_path}: {e}")
            
        try:
            # Safely open file with UTF-8 encoding
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback to general read if encoding fails
            try:
                with open(path, "rb") as f:
                    return f.read().decode("latin-1")
            except Exception as e:
                return f"Error reading binary content: {str(e)}"
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return f"Error: Failed to read file: {str(e)}"
