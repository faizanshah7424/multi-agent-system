from typing import List
from pydantic import BaseModel, Field
from core.feature_engine.feature_parser import FeatureSpec

class FeatureExecutionPlan(BaseModel):
    affected_files: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    database_migration_steps: List[str] = Field(default_factory=list)
    api_steps: List[str] = Field(default_factory=list)
    frontend_steps: List[str] = Field(default_factory=list)
    testing_strategy: List[str] = Field(default_factory=list)
    rollback_strategy: List[str] = Field(default_factory=list)
    estimated_time: str = "4 hours"
    confidence: float = 0.95

class FeaturePlanner:
    """
    Creates FeatureExecutionPlan based on Feature Specs.
    """
    def create_plan(self, spec: FeatureSpec) -> FeatureExecutionPlan:
        plan = FeatureExecutionPlan()
        plan.affected_files = list(spec.dependencies)

        for db_change in spec.database_changes:
            table = db_change.get("table", "")
            action = db_change.get("action", "")
            # Prefix with '--' to treat as SQL comment, avoiding parse errors in migration scripts
            plan.database_migration_steps.append(f"-- migration: {action} on {table}")

        for api in spec.apis:
            plan.api_steps.append(f"Add API endpoint {api['method']} {api['path']}")

        for ui in spec.ui_components:
            plan.frontend_steps.append(f"Build frontend component: {ui}")

        plan.execution_order = [
            "1. Run database schema migrations.",
            "2. Implement backend structures and services.",
            "3. Add API endpoints in router files.",
            "4. Mount frontend views on dashboard router.",
            "5. Execute verification tests."
        ]
        plan.testing_strategy = [
            "Write pytest integration cases for the new feature.",
            "Verify lint/ruff compliance.",
            "Run full platform regression test suites."
        ]
        plan.rollback_strategy = [
            "Use git manager to checkout safety checkpoint files.",
            "Run migration manager rollback schema migrations."
        ]

        plan.estimated_time = "4 hours"
        plan.confidence = 0.95

        return plan
