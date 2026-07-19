import subprocess
import time
from typing import List
from core.sandbox.interface import ISandbox, SandboxExecutionResult


class DockerSandbox(ISandbox):
    """
    Isolated Sandbox implementation using standard Docker CLI container mounts.
    """

    def __init__(
        self,
        container_name: str,
        workspace_path: str,
        image: str = "python:3.11-slim",
        cpu_limit: str = "0.5",
        memory_limit: str = "512m",
        network_disabled: bool = True,
        read_only_root: bool = True,
    ) -> None:
        self.container_name = container_name
        self.workspace_path = workspace_path
        self.image = image
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
        self.network_disabled = network_disabled
        self.read_only_root = read_only_root

    @property
    def container_id(self) -> str:
        """
        Alias property for compatibility with SessionManager.
        """
        return self.container_name

    @container_id.setter
    def container_id(self, value: str) -> None:
        self.container_name = value

    def create(self) -> None:
        """
        Provisions a container using docker create with resource limits, read-only rootfs, and network disabled.
        """
        # Stop and remove existing container if it exists to avoid duplicate name collision
        try:
            subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True, timeout=5.0)
        except Exception:
            pass

        cmd = [
            "docker",
            "create",
            "-it",
            "--name",
            self.container_name,
            "-v",
            f"{self.workspace_path}:/workspace",
            "-w",
            "/workspace",
        ]

        # Apply CPU and Memory resource limits
        if self.cpu_limit:
            cmd += ["--cpus", self.cpu_limit]
        if self.memory_limit:
            cmd += ["-m", self.memory_limit]

        # Enforce Network Isolation
        if self.network_disabled:
            cmd += ["--network", "none"]

        # Enable Read-Only Container Root System (with ephemeral /tmp)
        if self.read_only_root:
            cmd += ["--read-only", "--tmpfs", "/tmp:rw,size=128m"]  # nosec

        cmd += [self.image, "tail", "-f", "/dev/null"]

        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            raise RuntimeError(f"Failed to create Docker sandbox container: {res.stderr.strip()}")

    def initialize(self) -> None:
        """
        Starts the created container and verifies it is running.
        """
        cmd = ["docker", "start", self.container_name]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            raise RuntimeError(f"Failed to initialize/start Docker sandbox container: {res.stderr.strip()}")

        # Verify that the container is active and running
        if not self.health_check():
            raise RuntimeError(f"Docker container {self.container_name} failed health check after start.")

    def start(self) -> None:
        """
        Delegates to create() and initialize().
        """
        self.create()
        self.initialize()

    def execute(self, cmd: List[str], timeout: float = 30.0) -> SandboxExecutionResult:
        """
        Executes commands inside the container using docker exec.
        """
        exec_cmd = ["docker", "exec", self.container_name] + cmd
        start_time = time.time()
        timeout_exceeded = False

        try:
            proc = subprocess.Popen(
                exec_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                timeout_exceeded = True

            exit_code = proc.returncode
        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = f"Docker exec crashed: {str(e)}"

        duration = time.time() - start_time

        return SandboxExecutionResult(
            exit_code=exit_code,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_seconds=duration,
            timeout_exceeded=timeout_exceeded,
        )

    def copy_in(self, local_path: str, remote_path: str) -> None:
        """
        Copies file from host onto container workspace.
        """
        cmd = ["docker", "cp", local_path, f"{self.container_name}:{remote_path}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"docker cp-in failed: {res.stderr}")

    def copy_out(self, remote_path: str, local_path: str) -> None:
        """
        Copies file from container onto host filesystem.
        """
        cmd = ["docker", "cp", f"{self.container_name}:{remote_path}", local_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"docker cp-out failed: {res.stderr}")

    def destroy(self) -> None:
        """
        Stops and removes the ephemeral container, ignoring cleanup errors safely.
        """
        try:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True, timeout=10.0)
        except Exception:
            pass

        try:
            subprocess.run(["docker", "rm", self.container_name], capture_output=True, timeout=10.0)
        except Exception:
            pass

    def terminate(self) -> None:
        """
        Stops and removes the ephemeral container.
        """
        self.destroy()

    def health_check(self) -> bool:
        """
        Checks if the container exists and is running.
        """
        cmd = [
            "docker",
            "inspect",
            "--format",
            "{{.State.Running}}",
            self.container_name,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            return False
        return res.stdout.strip().lower() == "true"

