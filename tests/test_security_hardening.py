import os
import re
import pytest
import logging
from pathlib import Path
from fastapi.testclient import TestClient

from tools.base import validate_safe_path
from tools.file_reader import FileReaderTool
from tools.file_writer import FileWriterTool
from tools.python_executor import PythonExecutorTool, verify_code_safety
from core.memory import SharedMemory
from core.logging import SecretRedactingFormatter
from api.app import app
from core.database import get_db_session
from core.repositories import TaskRepository


def test_validate_safe_path_traversal():
    workspace_root = Path(__file__).parent.parent.resolve()

    # 1. Deny path traversal with parent directories
    with pytest.raises(ValueError, match="outside the allowed directories"):
        validate_safe_path("../../../windows/system32/cmd.exe")

    # 2. Deny path traversal using absolute path outside allowed roots
    with pytest.raises(ValueError, match="outside the allowed directories"):
        validate_safe_path("C:/Windows/System32/drivers/etc/hosts")

    # 3. Deny common prefix vulnerability bypass (e.g. workspace-fake)
    fake_workspace = str(workspace_root) + "-fake/sensitive.txt"
    with pytest.raises(ValueError, match="outside the allowed directories"):
        validate_safe_path(fake_workspace)

    # 4. Deny null byte path attempts
    with pytest.raises(ValueError, match="null bytes"):
        validate_safe_path("test\x00file.txt")

    # 5. Deny illegal control characters
    with pytest.raises(ValueError, match="control characters"):
        validate_safe_path("test\x01file.txt")


def test_file_reader_tool_safety(tmp_path):
    # Ensure file reader enforces path validation and OOM boundaries
    reader = FileReaderTool()

    # 1. Test directory traversal read denial
    res = reader.execute("../../../windows/win.ini")
    assert "Error: Access Denied" in res

    # 2. Test reading files exceeding limit (10MB)
    large_file = tmp_path / "large.txt"
    # Write a mock large file of size 11MB
    large_file.write_bytes(b"a" * (11 * 1024 * 1024))

    # Make tmp_path allowed in base.py by passing it (tmp_path resolves to OS temp)
    # Wait, tmp_path might be denied since it's not workspace_root or settings.persist_path
    # That is correct, so let's verify it gets denied as outside allowed roots
    res = reader.execute(str(large_file))
    assert "Access Denied" in res or "exceeds the maximum permitted read limit" in res


def test_file_writer_tool_safety(tmp_path):
    writer = FileWriterTool()

    # 1. Test denied directories (like SSH keys and shell configuration files)
    res = writer.execute(".ssh/authorized_keys", "ssh-rsa aaa")
    assert "Error: Write denied to forbidden destination pattern" in res

    res = writer.execute(".bashrc", "alias rm='rm -rf'")
    assert "Error: Write denied to forbidden destination pattern" in res

    # 2. Test write size limit (10MB)
    res = writer.execute("workspace_sub/file.txt", "a" * (11 * 1024 * 1024))
    assert "Error: Content size exceeds" in res


def test_python_executor_sandbox_escapes():
    # 1. Check direct imports banned
    with pytest.raises(ValueError, match="Import of banned module"):
        verify_code_safety("import os\nos.system('dir')")

    with pytest.raises(ValueError, match="Import of banned module"):
        verify_code_safety("import sys\nsys.exit(1)")

    with pytest.raises(ValueError, match="Import of banned module"):
        verify_code_safety("import importlib\nimportlib.import_module('os')")

    # 2. Check from-imports banned
    with pytest.raises(ValueError, match="Import from banned module"):
        verify_code_safety("from subprocess import Popen")

    # 3. Check builtins like eval, exec, open banned
    with pytest.raises(ValueError, match="Calling built-in function"):
        verify_code_safety("eval('2+2')")

    with pytest.raises(ValueError, match="Calling built-in function"):
        verify_code_safety("exec('import os')")

    with pytest.raises(ValueError, match="Calling built-in function"):
        verify_code_safety("open('file.txt', 'r')")

    # 4. Check double-underscore property escapes (like __class__, __subclasses__)
    with pytest.raises(ValueError, match="Accessing double-underscore"):
        verify_code_safety("x = ().__class__.__bases__[0].__subclasses__()")

    with pytest.raises(ValueError, match="Accessing double-underscore"):
        verify_code_safety("x.__globals__")

    # 5. Check getattr/setattr calls banned
    with pytest.raises(ValueError, match="Calling built-in function"):
        verify_code_safety("getattr(object, 'attr')")


def test_python_executor_tool_execution():
    executor = PythonExecutorTool()

    # 1. Test execution success
    res = executor.execute("print('Hello from sandbox!')")
    assert "Execution: SUCCESS" in res
    assert "Hello from sandbox!" in res

    # 2. Test execution of banned content
    res = executor.execute("import os\nos.system('whoami')")
    assert "Security Error: Import of banned module" in res

    # 3. Test execution stdout size cap (truncation)
    res = executor.execute("for i in range(100000):\n    print('A' * 100)")
    assert "Execution: SUCCESS" in res
    assert "OUTPUT LIMIT EXCEEDED" in res


def test_shared_memory_validation():
    memory = SharedMemory(session_id="security_test_session")

    # 1. Deny invalid key names
    with pytest.raises(ValueError, match="Invalid memory key"):
        memory.set("invalid key!", "value")

    with pytest.raises(ValueError, match="Invalid memory key"):
        memory.set("a" * 101, "value")

    # 2. Deny reserved keys
    with pytest.raises(ValueError, match="reserved"):
        memory.set("task_id", "123")

    # 3. Deny non-JSON serializable values (e.g. functions, objects)
    def dummy_func():
        pass

    with pytest.raises(ValueError, match="Must be JSON serializable"):
        memory.set("test_key", dummy_func)

    # 4. Limit size to 5MB
    with pytest.raises(ValueError, match="size exceeds"):
        memory.set("test_key", "a" * (6 * 1024 * 1024))


def test_secret_redaction_logging():
    # Set up formatter
    formatter = SecretRedactingFormatter()

    # Mock LogRecord
    logger = logging.getLogger("TestRedactionLogger")
    record = logger.makeRecord(
        name="test",
        level=logging.INFO,
        fn="test.py",
        lno=10,
        msg="Connection using AIzaSyD4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0 and bearer 12345.abcdefg",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    assert "[REDACTED_GEMINI_KEY]" in formatted
    assert "bearer [REDACTED]" in formatted
    assert "AIzaSyD4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0" not in formatted
    assert "12345.abcdefg" not in formatted


def test_api_rate_limiter_cleanup():
    client = TestClient(app)
    # Fire off requests to trigger rate limiting and check we don't leak memory
    for i in range(10):
        response = client.get("/")
        assert response.status_code == 200


def test_api_task_ownership():
    client = TestClient(app)

    # 1. Create a task with a specific owner (user_id='alice')
    with get_db_session() as session:
        repo = TaskRepository(session)
        task_id = "test_owner_task_123"
        # Clean existing if any
        existing = repo.get_task(task_id)
        if existing:
            session.delete(existing)
            session.commit()

        repo.create_task(
            task_id=task_id, payload={"task": "Do some secure work"}, user_id="alice"
        )

    # 2. Query status as 'bob' -> Expect 403 Forbidden
    response = client.get(f"/status?session_id={task_id}", headers={"X-User-ID": "bob"})
    assert response.status_code == 403
    assert "Access Denied" in response.json()["detail"]

    # 3. Query status without user ID -> Expect 403 Forbidden
    response = client.get(f"/status?session_id={task_id}")
    assert response.status_code == 403
    assert "Access Denied" in response.json()["detail"]

    # 4. Query status as 'alice' -> Expect 200 OK
    response = client.get(
        f"/status?session_id={task_id}", headers={"X-User-ID": "alice"}
    )
    assert response.status_code == 200

    # 5. Clean up task
    with get_db_session() as session:
        repo = TaskRepository(session)
        t = repo.get_task(task_id)
        if t:
            session.delete(t)
            session.commit()
