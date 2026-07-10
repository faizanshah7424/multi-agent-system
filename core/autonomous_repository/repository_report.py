import os
from typing import Dict, Any

class RepositoryReportGenerator:
    """
    Generates structured markdown documentation files summarizing task execution outcomes.
    """
    def __init__(self, output_dir: str = "docs/reports"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all_reports(self, goal: str, plan_dict: Dict[str, Any], validation_dict: Dict[str, Any]) -> Dict[str, str]:
        paths = {}

        # 1. implementation_report.md
        impl_path = os.path.join(self.output_dir, "implementation_report.md")
        with open(impl_path, "w", encoding="utf-8") as f:
            f.write(f"# Implementation Report: {goal}\n\n- **Goal**: {goal}\n- **Plan**: {plan_dict}\n")
        paths["implementation_report"] = impl_path.replace("\\", "/")

        # 2. architecture_changes.md
        arch_path = os.path.join(self.output_dir, "architecture_changes.md")
        with open(arch_path, "w", encoding="utf-8") as f:
            f.write(f"# Architecture Changes\n\n- **Tasks**: {plan_dict.get('architecture_fit', 'HEX')}\n")
        paths["architecture_changes"] = arch_path.replace("\\", "/")

        # 3. migration_report.md
        mig_path = os.path.join(self.output_dir, "migration_report.md")
        with open(mig_path, "w", encoding="utf-8") as f:
            f.write(f"# Migration Report\n\n- **Database alterations**: {plan_dict.get('database_changes', [])}\n")
        paths["migration_report"] = mig_path.replace("\\", "/")

        # 4. validation_report.md
        val_path = os.path.join(self.output_dir, "validation_report.md")
        with open(val_path, "w", encoding="utf-8") as f:
            f.write(f"# Validation Report\n\n- **Checkpoints**: {validation_dict}\n")
        paths["validation_report"] = val_path.replace("\\", "/")

        # 5. repository_changes.md
        changes_path = os.path.join(self.output_dir, "repository_changes.md")
        with open(changes_path, "w", encoding="utf-8") as f:
            f.write(f"# Repository Changes\n\n- **Apis & UI changes**: {plan_dict.get('api_changes', [])}\n")
        paths["repository_changes"] = changes_path.replace("\\", "/")

        return paths
