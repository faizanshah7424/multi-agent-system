from pathlib import Path
from pydantic import BaseModel, Field
from tools.base import BaseTool, validate_safe_path
from core.logging import get_logger

logger = get_logger("DirScannerTool")


class DirScannerInput(BaseModel):
    directory_path: str = Field(
        default=".",
        description="The directory path to scan. Defaults to standard project root ('.').",
    )
    recursive: bool = Field(
        default=False,
        description="Whether to scan recursively or just the top-level files/directories.",
    )


class DirScannerTool(BaseTool):
    name: str = "dir_scanner"
    description: str = (
        "Lists files and subdirectories within a target folder. "
        "Intelligently filters out virtual environments, cache folders, and version control directories."
    )
    args_schema: type[BaseModel] = DirScannerInput

    def execute(self, directory_path: str = ".", recursive: bool = False) -> str:
        try:
            path = validate_safe_path(directory_path)
        except ValueError as ve:
            return f"Error: {ve}"

        logger.info(f"Scanning directory (recursive={recursive}): {path}")

        if not path.exists():
            return (
                f"Error: Directory '{directory_path}' does not exist at path '{path}'"
            )

        if not path.is_dir():
            return f"Error: Path '{directory_path}' is a file, not a directory."

        # Common system and environment directories to ignore
        exclude_dirs = {
            ".git",
            "venv",
            "env",
            "__pycache__",
            ".gemini",
            ".pytest_cache",
            ".vscode",
            ".idea",
            "node_modules",
            "dist",
            "build",
        }

        try:
            results = []

            def scan_dir(dir_path: Path, indent: str = "") -> None:
                # Group items: directories first, then files (alphabetically sorted)
                try:
                    items = sorted(
                        dir_path.iterdir(),
                        key=lambda p: (not p.is_dir(), p.name.lower()),
                    )
                except PermissionError:
                    results.append(f"{indent}[Permission Denied for {dir_path.name}]")
                    return

                for item in items:
                    if item.name in exclude_dirs:
                        continue

                    if item.is_dir():
                        results.append(f"{indent}📁 {item.name}/")
                        if recursive:
                            scan_dir(item, indent + "  ")
                    else:
                        size_str = f"{item.stat().st_size:,} bytes"
                        results.append(f"{indent}📄 {item.name} ({size_str})")

            scan_dir(path)

            if not results:
                return f"Directory '{directory_path}' is empty or contains only ignored paths."

            return "\n".join(results)

        except Exception as e:
            logger.error(f"Failed to scan directory {directory_path}: {str(e)}")
            return f"Error: Failed to scan directory: {str(e)}"
