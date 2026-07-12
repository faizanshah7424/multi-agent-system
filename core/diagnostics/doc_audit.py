import os
from pathlib import Path
from typing import List, Dict


class DocumentationAudit:
    """
    Subsystem auditing workspace documentation.
    Scans project folders for READMEs, Architecture markdown, API descriptions,
    and logs missing document warnings.
    """

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root).resolve()

        # Required core documents
        self.required_files = [
            "README.md",
            "CONSTITUTION.md",
            "docs/BENCHMARK_SUITE.md",
            "docs/reports/benchmark_history.md",
        ]

        # Directories that should contain a README.md or corresponding docs
        self.required_dir_docs = ["agents", "core", "api"]

    def run_audit(self) -> Dict[str, Any]:
        """
        Executes audit checks on expected file paths.
        Returns validation results and warnings.
        """
        warnings = []
        passed = True

        # 1. Check core files
        for rel_path in self.required_files:
            file_path = self.project_root / rel_path
            if not file_path.exists():
                passed = False
                warnings.append(
                    f"Missing core document: '{rel_path}' is not present at project root."
                )

        # 2. Check directory-level READMEs
        for folder_name in self.required_dir_docs:
            folder_path = self.project_root / folder_name
            if folder_path.exists():
                readme_path = folder_path / "README.md"
                # Check if there is at least one markdown doc inside the folder if README is missing
                md_files = list(folder_path.glob("*.md"))
                if not readme_path.exists() and not md_files:
                    warnings.append(
                        f"Directory warning: '{folder_name}' has no README.md or descriptive markdown docs."
                    )

        return {
            "passed": passed,
            "warnings": warnings,
            "status": "ALL_DOCS_VERIFIED" if passed else "MISSING_DOCS_WARNING",
        }


from typing import Any
