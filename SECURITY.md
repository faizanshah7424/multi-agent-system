# Security Policy

We take the security of the **Multi-Agent AI Platform** seriously. This document outlines our supported versions, reporting procedures, and the robust security mechanisms implemented across the platform to ensure safe LLM agent execution.

## Supported Versions

Only the latest release receives active security updates and patches.

| Version | Supported |
| --- | :---: |
| v1.2.x (Current) | ✅ Yes |
| v1.1.x | ❌ No |
| v1.0.x | ❌ No |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please do **not** open a public issue. Instead, report it directly through one of the following channels:

* **Email**: Send a detailed description of the vulnerability to [security@example.com](mailto:security@example.com).
* **Details to Include**:
  * Step-by-step instructions to reproduce the issue.
  * Potential impact (e.g., Remote Code Execution, Privilege Escalation).
  * Any proof-of-concept scripts or payload details.
  * System environment details.

We will acknowledge receipt of your vulnerability report within **24 hours** and provide a status update or fix within **3 business days**.

---

## Implemented Security Guardrails

The platform has gone through an intensive **Security Hardening Sprint** to defend against adversarial agent behavior and external attacks. The key hardened components are:

### 1. Safe Workspace Confinement
* **Files**: [base.py](file:///E:/multi-agent-system/tools/base.py) | [file_reader.py](file:///E:/multi-agent-system/tools/file_reader.py) | [file_writer.py](file:///E:/multi-agent-system/tools/file_writer.py)
* **Mechanisms**:
  * Bypasses like null byte injections (`\x00`) and control characters are rejected.
  * Real absolute paths are fully resolved via `resolve(strict=False)` before validation to flatten parent traversals (`..`) and symlinks.
  * Confinement is validated strictly using path components rather than string prefixes, preventing common-prefix bypasses (e.g., mapping `multi-agent-system-evil` to `multi-agent-system`).
  * Enforces strict read/write boundaries (files are limited to **10MB** max).
  * System-critical paths (e.g., `.ssh/`, `.git/`, `.bashrc`, `ntuser.dat`) are explicitly blacklisted for writes.

### 2. AST-Safe Python Sandbox
* **File**: [python_executor.py](file:///E:/multi-agent-system/tools/python_executor.py)
* **Mechanisms**:
  * Prior to execution, Python code is parsed into an Abstract Syntax Tree (AST) to verify safety.
  * Direct/indirect imports of low-level modules are blocked (e.g., `os`, `sys`, `importlib`, `builtins`, `subprocess`, `ctypes`, `shutil`, `pathlib`).
  * Banned execution builtins include `eval`, `exec`, `open`, `compile`, `getattr`, `setattr`, etc.
  * Double-underscore attributes (like `__class__`, `__subclasses__`, `__globals__`) are statically blocked to prevent runtime sandbox escapes.
  * Subprocesses are executed via safe `Popen` streams with buffer caps (discarding output exceeding **2MB** to avoid pipe deadlocks and Out-Of-Memory crashes) and a strict **30-second execution timeout**.

### 3. API Layer Enforcement
* **Files**: [app.py](file:///E:/multi-agent-system/api/app.py) | [routes.py](file:///E:/multi-agent-system/api/routes.py) | [models.py](file:///E:/multi-agent-system/api/models.py)
* **Mechanisms**:
  * Input fields (like `session_id` and `task_id`) are validated using Pydantic regex validators (`^[a-zA-Z0-9_\-]+$`) to eliminate SQL/path injection.
  * Custom FastAPI middleware enforces a global payload size limit of **10MB** on all request streams.
  * The rate-limiting middleware prunes stale memory buckets periodically when tracking more than 1,000 active IPs, preventing Denials of Service (DoS) due to memory leaks.
  * Task status, history, and cancellation endpoints enforce Broken Object Level Authorization (BOLA) validation by verifying request ownership against the database task owner.

### 4. Memory Layer Sanitization
* **File**: [memory.py](file:///E:/multi-agent-system/core/memory.py)
* **Mechanisms**:
  * Stored memory keys are restricted to alphanumeric characters under **100 characters**.
  * Modifying system-reserved keys is explicitly blocked.
  * Stored values must be JSON-serializable and are capped at **5MB** to prevent database serialization crashes.

### 5. Log Credential Redaction
* **File**: [logging.py](file:///E:/multi-agent-system/core/logging.py)
* **Mechanisms**:
  * The custom `SecretRedactingFormatter` sanitizes all terminal outputs and log files.
  * Redacts active system credentials, raw API key patterns (e.g., `AIzaSy`), authorization headers, and password properties before they are written to disk.

Security is validated continuously via our automated test suite in [test_security_hardening.py](file:///E:/multi-agent-system/tests/test_security_hardening.py).
