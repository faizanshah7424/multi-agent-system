import os
import re
from core.logging import get_logger

logger = get_logger("MemoryCompactionManager")


class MemoryCompactionManager:
    """
    Summarizes verbose software logs, compiler outputs, and tracebacks
    into compact, token-efficient structural fix descriptions.
    """

    def __init__(self) -> None:
        pass

    def compact_log(self, verbose_log: str) -> str:
        """
        Parses complex compiler log outputs and extracts core traceback line message,
        filtering out redundant environmental paths and warnings.
        """
        logger.info("Compacting verbose log context...")
        if not verbose_log:
            return ""

        # Normalize paths by stripping absolute directory paths
        cwd = os.getcwd()
        cwd_norm = cwd.replace("\\", "/")
        sanitized_log = verbose_log.replace(cwd, "").replace(cwd_norm, "")

        lines = sanitized_log.splitlines()

        # Capture trace/error occurrences
        important_lines = []
        for line in lines:
            line_str = line.strip()
            # Capture python stack file lines, pytest assert marks, and error name details
            if (
                line_str.startswith("File ")
                or line_str.startswith("E ")
                or "error" in line_str.lower()
                or "failure" in line_str.lower()
                or "warning" in line_str.lower()
                or re.search(r"\.py:\d+:\d+:", line_str)
                or re.search(r"\.ts\(\d+,\d+\):", line_str)
            ):
                important_lines.append(line_str)

        if not important_lines:
            # Fallback to first few lines if no specific traceback markers match
            return "\n".join(lines[:3])

        compacted = " | ".join(
            important_lines[:5]
        )  # Cap to top 5 lines for prompt efficiency
        logger.info(
            f"Compacted log length from {len(verbose_log)} to {len(compacted)} chars."
        )
        return compacted
