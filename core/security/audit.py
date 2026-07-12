import re
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SecurityFinding(BaseModel):
    """Structured security audit finding representing code vulnerability or policy violation."""

    finding_id: str = Field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:6]}")
    category: str = Field(
        ...,
        description="Vulnerability type (e.g. SECRET_EXPOSURE, UNSAFE_SHELL, PATH_TRAVERSAL, UNSAFE_WRITE)",
    )
    severity: str = Field(
        "MEDIUM", description="Severity level: LOW, MEDIUM, HIGH, CRITICAL"
    )
    message: str = Field(..., description="Details of the detection.")
    file_path: Optional[str] = Field(None, description="Affected file path.")
    line_number: Optional[int] = Field(None, description="Affected line number.")


class SecurityAuditEngine:
    """
    Subsystem scanning proposed implementations and commands to audit for
    unsafe shell executions, path traversals, secrets, and raw filesystem writes.
    """

    def __init__(self) -> None:
        # Regex patterns for scanning secrets
        self.secret_patterns = [
            (
                r"(?i)(api_key|password|secret|auth_token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
                "SECRET_EXPOSURE",
                "HIGH",
            ),
            (
                r"AIzaSy[a-zA-Z0-9_\-]{33}",
                "SECRET_EXPOSURE",
                "CRITICAL",
            ),  # Google API key
            (r"sk-[a-zA-Z0-9]{48}", "SECRET_EXPOSURE", "CRITICAL"),  # OpenAI API key
        ]

        # Unsafe shell command structures in python code
        self.unsafe_py_calls = [
            (r"os\.system\(", "UNSAFE_SHELL", "HIGH"),
            (r"eval\(", "UNSAFE_SHELL", "MEDIUM"),
            (r"exec\(", "UNSAFE_SHELL", "HIGH"),
            (
                r"subprocess\.(Popen|run|call)\(.*shell\s*=\s*True",
                "UNSAFE_SUBPROCESS",
                "HIGH",
            ),
        ]

    def audit_code(
        self, code_content: str, file_path: str = "unknown"
    ) -> List[SecurityFinding]:
        """
        Scans code line-by-line for credentials, traversal attempts, or subprocess usage.
        """
        findings = []
        lines = code_content.splitlines()

        for idx, line in enumerate(lines, 1):
            # 1. Scan for secrets
            for pattern, cat, sev in self.secret_patterns:
                if re.search(pattern, line):
                    findings.append(
                        SecurityFinding(
                            category=cat,
                            severity=sev,
                            message="Potential hardcoded credential or API key found in source line.",
                            file_path=file_path,
                            line_number=idx,
                        )
                    )

            # 2. Scan for unsafe python calls
            for pattern, cat, sev in self.unsafe_py_calls:
                if re.search(pattern, line):
                    findings.append(
                        SecurityFinding(
                            category=cat,
                            severity=sev,
                            message=f"Dangerous dynamic execution or subprocess shell=True call found: '{line.strip()}'",
                            file_path=file_path,
                            line_number=idx,
                        )
                    )

            # 3. Path traversal patterns in strings
            if ".." in line and (
                "open(" in line or "Path(" in line or "os.path" in line
            ):
                findings.append(
                    SecurityFinding(
                        category="PATH_TRAVERSAL",
                        severity="MEDIUM",
                        message="Relative path parent references ('..') found during filesystem access.",
                        file_path=file_path,
                        line_number=idx,
                    )
                )

        return findings

    def audit_command(self, cmd: List[str]) -> List[SecurityFinding]:
        """
        Audits shell command tokens prior to sandbox run.
        """
        findings = []
        cmd_str = " ".join(cmd)

        # Redirection chaining or token evaluation check
        if any(token in cmd for token in [";", "&&", "|", "||"]):
            findings.append(
                SecurityFinding(
                    category="UNSAFE_SHELL",
                    severity="HIGH",
                    message="Command contains chaining operators which can lead to shell injection.",
                )
            )

        if ".." in cmd_str:
            findings.append(
                SecurityFinding(
                    category="PATH_TRAVERSAL",
                    severity="MEDIUM",
                    message="Command contains path traversal arguments ('..').",
                )
            )

        return findings
