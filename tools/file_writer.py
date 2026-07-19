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

    def _get_sandbox(self) -> tuple:
        """
        Resolves the active workspace path and sandbox instance for the current task session.
        """
        from core.database import get_db_session
        from core.workspace.session_manager import DBSessionState
        from core.logging import get_correlation_context
        from core.di import DIContainer
        from pathlib import Path

        context = get_correlation_context()
        task_id = context.get("task_id")
        workspace_path = None

        if task_id and task_id != "N/A":
            try:
                with get_db_session() as session:
                    record = session.query(DBSessionState).filter(DBSessionState.task_id == task_id).first()
                    if record:
                        workspace_path = record.workspace_path
            except Exception:
                pass

        if not workspace_path:
            # Fallback to host workspace root
            workspace_path = str(Path(__file__).parent.parent.resolve())

        # Construct sandbox instance
        try:
            sandbox_factory = DIContainer.get("sandbox_factory")
        except Exception:
            from core.sandbox.sandbox_factory import SandboxFactory
            sandbox_factory = SandboxFactory.create_sandbox

        sandbox = sandbox_factory(workspace_path, task_id if task_id != "N/A" else None)
        return sandbox, workspace_path

    def _resolve_sandbox_path(self, file_path_str: str, workspace_path: str):
        from pathlib import Path
        # 1. Null byte and control character checks
        if not file_path_str or "\x00" in file_path_str:
            raise ValueError("Access Denied: Path contains null bytes or is empty.")
        if any(c in file_path_str for c in (chr(i) for i in range(32) if i not in (9, 10, 13))):
            raise ValueError("Access Denied: Path contains illegal control characters.")

        # Ensure no directory traversal attempt
        norm_path = file_path_str.replace("\\", "/")
        if "/../" in norm_path or norm_path.startswith("../") or norm_path.endswith("/..") or norm_path == "..":
            raise ValueError("Access Denied: Path traversal is prohibited.")

        workspace_dir = Path(workspace_path).resolve()
        
        target = Path(file_path_str)
        if not target.is_absolute():
            target = (workspace_dir / target).resolve(strict=False)
        else:
            target = target.resolve(strict=False)

        # Check confinement
        try:
            rel_path = target.relative_to(workspace_dir)
        except ValueError:
            target_parts = [p.lower() for p in target.parts]
            root_parts = [p.lower() for p in workspace_dir.parts]
            if len(target_parts) >= len(root_parts) and target_parts[: len(root_parts)] == root_parts:
                rel_path = Path(*target.parts[len(root_parts):])
            else:
                raise ValueError("Access Denied: Path is outside the active sandbox workspace.")

        return rel_path

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

        import os
        import tempfile
        from pathlib import Path

        # 1. Resolve sandbox & workspace
        try:
            sandbox, workspace_path = self._get_sandbox()
            rel_path = self._resolve_sandbox_path(file_path, workspace_path)
        except ValueError as ve:
            return f"Error: {ve}"

        logger.info(f"Writing to file '{rel_path}' inside sandbox...")

        # 2. Determine container path and pre-create parent directories inside sandbox
        if sandbox.__class__.__name__ == "DockerSandbox":
            remote_path = f"/workspace/{str(rel_path).replace('\\', '/')}"
            # Execute mkdir -p inside container for parents
            parent_dir = "/workspace/" + str(rel_path.parent).replace("\\", "/")
            if parent_dir != "/workspace/.":
                sandbox.execute(["mkdir", "-p", parent_dir])
        else:
            remote_path = str(rel_path)
            # Ensure local parent dir exists
            (Path(workspace_path) / rel_path).parent.mkdir(parents=True, exist_ok=True)

        # 3. Write content to a temporary host file
        try:
            fd, temp_host_path = tempfile.mkstemp()
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            return f"Error: Failed to write transient source content: {str(e)}"

        try:
            # 4. Copy the file into the sandbox
            sandbox.copy_in(temp_host_path, remote_path)
            return f"Success: File written successfully to '{file_path}'"
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {str(e)}")
            return f"Error: Failed to write to file: {str(e)}"
        finally:
            try:
                if os.path.exists(temp_host_path):
                    os.remove(temp_host_path)
            except Exception:
                pass

