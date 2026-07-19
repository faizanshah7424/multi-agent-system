import subprocess
import uuid
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
        # Generate a unique task/session identifier if missing
        if not task_id:
            task_id = f"temp_{uuid.uuid4().hex[:8]}"

        from core.cleanup import CleanupCoordinator

        try:
            # Check if docker is available on host system
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=3.0)
            if res.returncode == 0:
                container_name = f"task_sandbox_{task_id}"
                sandbox = DockerSandbox(container_name, workspace_path)
                CleanupCoordinator.register_resource(
                    task_id=task_id,
                    resource_type="container",
                    resource_identifier=container_name,
                    cleanup_callable=sandbox.terminate
                )
                return sandbox
        except Exception:
            pass

        sandbox = LocalProcessSandbox(workspace_path)
        CleanupCoordinator.register_resource(
            task_id=task_id,
            resource_type="local_process_sandbox",
            resource_identifier=workspace_path,
            cleanup_callable=sandbox.terminate
        )
        return sandbox

