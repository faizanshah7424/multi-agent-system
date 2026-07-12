from pathlib import Path
from core.logging import get_logger
from core.benchmark.schemas import InjectableBug

logger = get_logger("FailureInjectionEngine")

class FailureInjectionEngine:
    """
    Deterministic bug injection engine modifying and reverting benchmark code files.
    """
    def __init__(self) -> None:
        pass

    def inject_bug(self, workspace_path: str, bug: InjectableBug) -> bool:
        """
        Locates code snippet and replaces it with bug content.
        """
        file_path = Path(workspace_path) / bug.file_path
        if not file_path.exists():
            logger.error(f"Cannot inject bug: file {bug.file_path} not found.")
            return False

        content = file_path.read_text(encoding="utf-8")
        if bug.target_content not in content:
            logger.warning(f"Target content snippet not found in {bug.file_path}. Incomplete injection.")
            return False

        injected_content = content.replace(bug.target_content, bug.bug_content)
        file_path.write_text(injected_content, encoding="utf-8")
        logger.info(f"Successfully injected bug '{bug.bug_id}' in file {bug.file_path}")
        return True

    def revert_bug(self, workspace_path: str, bug: InjectableBug) -> bool:
        """
        Restores original file content by reversing bug substitution.
        """
        file_path = Path(workspace_path) / bug.file_path
        if not file_path.exists():
            return False

        content = file_path.read_text(encoding="utf-8")
        if bug.bug_content not in content:
            return False

        reverted_content = content.replace(bug.bug_content, bug.target_content)
        file_path.write_text(reverted_content, encoding="utf-8")
        logger.info(f"Successfully reverted bug '{bug.bug_id}' in file {bug.file_path}")
        return True
