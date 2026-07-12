from typing import List
from pydantic import BaseModel, Field
from core.autonomous_repository.repository_context import RepositoryContext


class RepositoryTaskPlan(BaseModel):
    requirements: List[str] = Field(default_factory=list)
    architecture_fit: str = "Fits existing FastAPI Hexagonal architecture"
    database_changes: List[str] = Field(default_factory=list)
    api_changes: List[str] = Field(default_factory=list)
    frontend_changes: List[str] = Field(default_factory=list)
    testing_strategy: List[str] = Field(default_factory=list)
    documentation_changes: List[str] = Field(default_factory=list)
    migration_plan: List[str] = Field(default_factory=list)
    rollback_plan: List[str] = Field(default_factory=list)
    risk_analysis: List[str] = Field(default_factory=list)
    estimated_effort: str = "6 hours"
    confidence: float = 0.95


class RepositoryPlanner:
    """
    Formulates a comprehensive engineering execution plan matching natural-language goals.
    """

    def create_plan(self, goal: str, context: RepositoryContext) -> RepositoryTaskPlan:
        plan = RepositoryTaskPlan()
        goal_lower = goal.lower()

        if "login" in goal_lower or "auth" in goal_lower:
            plan.requirements = [
                "Implement signup",
                "Implement login",
                "Implement refreshes",
            ]
            plan.database_changes = [
                "Add user columns (role, is_verified)",
                "Create refresh_tokens table",
            ]
            plan.api_changes = [
                "POST /auth/signup",
                "POST /auth/login",
                "POST /auth/refresh",
            ]
            plan.frontend_changes = ["Create Login screen", "Mount views in Layout"]
            plan.testing_strategy = ["Verify auth flows in tests/test_auth_system.py"]
            plan.documentation_changes = ["Update api documentation"]
            plan.migration_plan = ["Apply user model migrations"]
            plan.rollback_plan = ["Restore user tables", "Remove auth routes"]
            plan.risk_analysis = ["Credential exposures", "Session hijacking"]
            plan.estimated_effort = "4 hours"
        else:
            plan.requirements = [f"Fulfill custom goal: {goal}"]
            plan.database_changes = []
            plan.api_changes = [f"Add endpoint `/api/{goal.replace(' ', '-').lower()}`"]
            plan.frontend_changes = [f"Add dashboard panel for {goal}"]
            plan.testing_strategy = [f"Create test case file for {goal}"]
            plan.documentation_changes = ["Add implementation details"]
            plan.migration_plan = ["None"]
            plan.rollback_plan = ["Reset files in git"]
            plan.risk_analysis = ["Architectural misalignment"]
            plan.estimated_effort = "6 hours"

        return plan
