import subprocess
from typing import Optional
from core.sandbox.interface import ISandbox
from core.sandbox.docker_sandbox import DockerSandbox
from core.sandbox.local_sandbox import LocalProcessSandbox


class SandboxFactory:
    """
    Factory creating DockerSandbox if the Docker daemon is available,
    falling back to LocalProcessSandbox for virtualenv-scoped process execution.
    """

    @staticmethod
    def create_sandbox(workspace_path: str, task_id: Optional[str] = None) -> ISandbox:
        try:
            # Check if docker is available on host system
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=3.0)
            if res.returncode == 0:
                container_name = (
                    f"task_sandbox_{task_id}" if task_id else "temp_sandbox"
                )
                return DockerSandbox(container_name, workspace_path)
        except Exception:
            pass

        return LocalProcessSandbox(workspace_path)
