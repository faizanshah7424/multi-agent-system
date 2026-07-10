import os
from typing import Dict, Any

class DocumentationGenerator:
    """
    Generates 10 structured product specification reports inside docs/product_specs.
    """
    def __init__(self, output_dir: str = "docs/product_specs"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_documentation(self, data: Dict[str, Any]) -> Dict[str, str]:
        paths = {}
        files = {
            "product_requirements.md": "# Product Requirements Spec\n\nGenerated for: {idea}\n\nVision: {reqs[vision]}\n\nFunctional Requirements:\n{reqs[functional_reqs]}\n",
            "architecture.md": "# System Architecture Diagram & Layout\n\nDomain: {specs[domain]}\n\nConsensus: Hexagonal Multi-Agent debate consensus.\n",
            "database_design.md": "# Relational Database & Entity Relationship Layout\n\nTables:\n{db_design[ddl_scripts]}\n",
            "api_design.md": "# REST API Spec & Schema Mapping\n\nEndpoints:\n{api_design[endpoints]}\n",
            "frontend_plan.md": "# Frontend Layout, Navigation, and Pages\n\nPages:\n{frontend_plan[pages]}\n",
            "backend_plan.md": "# Backend Services, Jobs, and Queues\n\nServices:\n{backend_plan[services]}\n",
            "testing_strategy.md": "# Testing Strategy & Mock Setup\n\nUnit tests:\n{testing_plan[unit_tests]}\n",
            "deployment_plan.md": "# Infrastructure & Continuous Integration Setup\n\nEnvironments:\n{deployment_plan[environments]}\n",
            "implementation_plan.md": "# Phased Implementation Plan\n\nPhase 1: Database setups\nPhase 2: API integrations\nPhase 3: Frontends.\n",
            "executive_summary.md": "# Executive Summary\n\nSuccessfully planned product setup specs for: {idea}.\n"
        }

        # Format mappings safely
        for filename, template in files.items():
            content = template.format(
                idea=data.get("idea", "Custom Business Idea"),
                specs=data.get("specs", {}),
                reqs=data.get("reqs", {}),
                db_design=data.get("db_design", {}),
                api_design=data.get("api_design", {}),
                frontend_plan=data.get("frontend_plan", {}),
                backend_plan=data.get("backend_plan", {}),
                testing_plan=data.get("testing_plan", {}),
                deployment_plan=data.get("deployment_plan", {})
            )
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            paths[filename.replace(".md", "")] = file_path.replace("\\", "/")

        return paths
