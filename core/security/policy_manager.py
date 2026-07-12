import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class RuntimePolicyManager:
    """
    Runtime Policy Manager enforcing execution policies, command allowlists,
    filesystem boundaries, and repository protection rules.
    """
    def __init__(self, workspace_path: Optional[str] = None) -> None:
        self.workspace_path = Path(workspace_path or os.getcwd()).resolve()
        
        # Standard allowed base commands
        self.allowed_command_prefixes = {
            "python", "pip", "pytest", "npm", "npx", "git",
            "cargo", "poetry", "docker", "echo", "cat", "ls", "mkdir", "rm"
        }
        
        # Protected files that cannot be edited or deleted without approval
        self.protected_configs = {
            "package.json", "tsconfig.json", "settings.json",
            "pyproject.toml", ".env", "docker-compose.yml"
        }

    def validate_command(self, cmd: List[str]) -> Dict[str, Any]:
        """
        Validates a shell command against security restrictions and rules.
        """
        if not cmd:
            return {"allowed": False, "reason": "Empty command", "needs_approval": False}

        base_cmd = cmd[0].lower()
        
        # 1. Command allowlist check
        # Check standard executable name (e.g. resolve windows path or python.exe)
        executable_name = Path(base_cmd).name.replace(".exe", "")
        if executable_name not in self.allowed_command_prefixes:
            return {
                "allowed": False,
                "reason": f"Executable '{executable_name}' is not in the allowed command registry.",
                "needs_approval": True
            }

        # 2. Block destructive Git operations
        cmd_str = " ".join(cmd).lower()
        if "git" in cmd_str:
            if "push" in cmd_str and ("-f" in cmd_str or "--force" in cmd_str):
                return {
                    "allowed": False,
                    "reason": "Destructive Operation Blocked: Force Git Push is strictly forbidden.",
                    "needs_approval": True
                }
            if "reset" in cmd_str and "--hard" in cmd_str:
                return {
                    "allowed": False,
                    "reason": "Destructive Operation Blocked: Hard Git Reset is strictly forbidden.",
                    "needs_approval": True
                }

        # 3. Block destructive directory deletions
        if "rm" in cmd_str or "remove" in cmd_str or "delete" in cmd_str:
            if "/" in cmd_str or "core" in cmd_str or "E:\\" in cmd_str or "C:\\" in cmd_str:
                return {
                    "allowed": False,
                    "reason": "Destructive Operation Blocked: Attempting to delete root or core directories.",
                    "needs_approval": True
                }
            if ".git" in cmd_str:
                return {
                    "allowed": False,
                    "reason": "Destructive Operation Blocked: Attempting to delete hidden git folder.",
                    "needs_approval": True
                }

        return {"allowed": True, "reason": "Command conforms to runtime policy.", "needs_approval": False}

    def validate_path(self, target_path: str) -> bool:
        """
        Prevents path traversal by ensuring the target path resides within the workspace boundary.
        """
        try:
            resolved_target = Path(target_path).resolve()
            # Target must be inside workspace or equal to workspace
            return self.workspace_path in resolved_target.parents or resolved_target == self.workspace_path
        except Exception:
            return False

    def is_protected_file(self, target_path: str) -> bool:
        """
        Returns True if the target path references a protected configuration file.
        """
        filename = Path(target_path).name
        return filename in self.protected_configs
