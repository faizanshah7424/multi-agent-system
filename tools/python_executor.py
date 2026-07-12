import os
import sys
import tempfile
import subprocess
import ast
import threading
import time
from typing import List
from pydantic import BaseModel, Field
from tools.base import BaseTool
from core.logging import get_logger

logger = get_logger("PythonExecutorTool")


def verify_code_safety(code: str) -> None:
    """
    Parses Python code and raises ValueError if dangerous calls, imports,
    or execution statements are detected.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as se:
        raise ValueError(f"Syntax error in script: {se}")

    # Broadened banned modules for process execution, networking, file tools bypass, and direct system access
    BANNED_IMPORTS = {
        "subprocess",
        "socket",
        "ctypes",
        "pty",
        "webbrowser",
        "requests",
        "urllib",
        "httpx",
        "ftplib",
        "smtplib",
        "telnetlib",
        "multiprocessing",
        "threading",
        "concurrent",
        "os",
        "sys",
        "importlib",
        "builtins",
        "shutil",
        "pathlib",
        "platform",
        "runpy",
        "code",
        "compileall",
        "winreg",
        "bdb",
        "pdb",
        "pickle",
        "marshal",
        "shelve",
        "dbm",
        "sqlite3",
    }

    # Banned built-ins that bypass static imports, execute strings, or dynamically query attributes
    BANNED_CALLS = {
        "eval",
        "exec",
        "__import__",
        "compile",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "hasattr",
        "delattr",
        "open",
        "file",
    }

    # Banned os execution functions (fallback check)
    BANNED_OS_FUNCS = {
        "system",
        "popen",
        "exec",
        "execve",
        "execl",
        "execle",
        "execlp",
        "execlpe",
        "execv",
        "execvp",
        "execvpe",
        "spawn",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnvp",
        "spawnvpe",
        "fork",
        "forkpty",
        "kill",
        "killpg",
        "startfile",
    }

    for node in ast.walk(tree):
        # 1. Check direct imports (e.g., import subprocess)
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name in BANNED_IMPORTS:
                    raise ValueError(
                        f"Import of banned module '{name}' is forbidden for security reasons."
                    )

        # 2. Check from-imports (e.g., from subprocess import Popen)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                name = node.module.split(".")[0]
                if name in BANNED_IMPORTS:
                    raise ValueError(
                        f"Import from banned module '{name}' is forbidden for security reasons."
                    )

        # 3. Check function calls
        elif isinstance(node, ast.Call):
            # Direct calls to banned built-ins
            if isinstance(node.func, ast.Name):
                if node.func.id in BANNED_CALLS:
                    raise ValueError(
                        f"Calling built-in function '{node.func.id}' is forbidden for security reasons."
                    )
            # Attribute calls (like os.system or sys.modules)
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    val_id = node.func.value.id
                    if val_id in BANNED_IMPORTS:
                        raise ValueError(
                            f"Accessing attributes of banned module '{val_id}' is forbidden."
                        )
                if node.func.attr in BANNED_OS_FUNCS or node.func.attr in BANNED_CALLS:
                    raise ValueError(
                        f"Calling dangerous attribute '{node.func.attr}' is forbidden."
                    )

        # 4. Check Names (prevent reference to banned modules or __builtins__)
        elif isinstance(node, ast.Name):
            if node.id.startswith("__") and node.id not in ("__name__", "__main__"):
                raise ValueError(
                    f"Accessing double-underscore identifier '{node.id}' is forbidden."
                )
            if node.id in BANNED_IMPORTS:
                raise ValueError(
                    f"Usage of banned identifier '{node.id}' is forbidden."
                )

        # 5. Check Attributes (prevent double-underscore sandbox bypass e.g. __class__, __subclasses__)
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise ValueError(
                    f"Accessing double-underscore attribute '{node.attr}' is forbidden."
                )
            if isinstance(node.value, ast.Name) and node.value.id in BANNED_IMPORTS:
                raise ValueError(
                    f"Accessing attribute '{node.attr}' on banned module '{node.value.id}' is forbidden."
                )


class PythonExecutorInput(BaseModel):
    code: str = Field(
        ..., description="The complete, executable Python code script as a text block."
    )


class PythonExecutorTool(BaseTool):
    name: str = "python_executor"
    description: str = (
        "Executes a block of Python code locally in the system's environment. "
        "Captures and returns standard output (stdout) and standard error (stderr). "
        "Enforces a 30-second execution timeout."
    )
    args_schema: type[BaseModel] = PythonExecutorInput

    def execute(self, code: str) -> str:
        logger.info("Executing Python code block...")

        # Enforce AST-based static safety analysis before running code
        try:
            verify_code_safety(code)
        except ValueError as ve:
            logger.warning(f"Python script blocked by security validation: {ve}")
            return f"Security Error: {ve}"

        # Write the code to a temporary file
        try:
            fd, temp_file_path = tempfile.mkstemp(suffix=".py", text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            logger.error(f"Failed to create temporary script file: {str(e)}")
            return f"Error: Failed to write temporary script file: {str(e)}"

        proc = None
        try:
            # Resolve the active python interpreter path
            python_executable = sys.executable

            # Start the script in a subprocess with piped stdout/stderr to prevent OOM
            proc = subprocess.Popen(
                [python_executable, temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            stdout_lines: List[str] = []
            stderr_lines: List[str] = []
            max_bytes = 2 * 1024 * 1024  # 2MB limits per stream

            def read_stream(stream, lines_list):
                bytes_read = 0
                limit_hit = False
                for line in stream:
                    if not limit_hit:
                        if bytes_read < max_bytes:
                            lines_list.append(line)
                            bytes_read += len(line.encode("utf-8", errors="replace"))
                        else:
                            lines_list.append("\n[OUTPUT LIMIT EXCEEDED - TRUNCATED]\n")
                            limit_hit = True
                    # Continue consuming and discarding line to prevent subprocess pipe blocking

            t1 = threading.Thread(
                target=read_stream, args=(proc.stdout, stdout_lines), daemon=True
            )
            t2 = threading.Thread(
                target=read_stream, args=(proc.stderr, stderr_lines), daemon=True
            )
            t1.start()
            t2.start()

            # Wait for execution with 30-second timeout
            start_time = time.time()
            timeout = 30.0
            while proc.poll() is None:
                if time.time() - start_time > timeout:
                    proc.kill()
                    proc.wait()
                    logger.warning("Python script execution timed out (limit: 30s).")
                    return (
                        "Error: Python execution timed out (exceeded 30-second limit)."
                    )
                time.sleep(0.05)

            t1.join(timeout=1.0)
            t2.join(timeout=1.0)

            stdout_content = "".join(stdout_lines)
            stderr_content = "".join(stderr_lines)

            output_parts = []
            if proc.returncode == 0:
                output_parts.append("Execution: SUCCESS")
            else:
                output_parts.append(f"Execution: FAILED (Exit Code {proc.returncode})")

            if stdout_content:
                output_parts.append(f"--- STDOUT ---\n{stdout_content.strip()}")
            if stderr_content:
                output_parts.append(f"--- STDERR ---\n{stderr_content.strip()}")

            if not stdout_content and not stderr_content:
                output_parts.append("No outputs generated in stdout or stderr.")

            return "\n\n".join(output_parts)

        except Exception as e:
            if proc:
                try:
                    proc.kill()
                    proc.wait()
                except Exception:
                    pass
            logger.error(f"Error during script subprocess run: {str(e)}")
            return f"Error: Subprocess execution failed: {str(e)}"
        finally:
            # Clean up the temporary file
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                logger.warning(
                    f"Could not delete temporary script file {temp_file_path}: {str(e)}"
                )
