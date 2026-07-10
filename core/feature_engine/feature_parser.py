from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FeatureSpec(BaseModel):
    goals: List[str] = Field(default_factory=list)
    functional_requirements: List[str] = Field(default_factory=list)
    non_functional_requirements: List[str] = Field(default_factory=list)
    apis: List[Dict[str, Any]] = Field(default_factory=list)
    database_changes: List[Dict[str, Any]] = Field(default_factory=list)
    ui_components: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

class FeatureParser:
    """
    Transforms natural-language requirements into structured Feature Specifications.
    """
    def parse_requirement(self, requirement: str) -> FeatureSpec:
        req_lower = requirement.lower()
        spec = FeatureSpec()

        if "login" in req_lower or "auth" in req_lower:
            spec.goals = ["Implement a JWT authentication system for users."]
            spec.functional_requirements = [
                "Allow user signup with email and password.",
                "Allow user login returning access & refresh tokens.",
                "Verify email addresses.",
                "Reset forgotten passwords."
            ]
            spec.non_functional_requirements = ["Secure password hashing with PBKDF2.", "JWT expires in 15 minutes."]
            spec.apis = [
                {"path": "/auth/signup", "method": "POST", "desc": "Signup new user"},
                {"path": "/auth/login", "method": "POST", "desc": "Login user"}
            ]
            spec.database_changes = [
                {"table": "users", "action": "add_columns", "columns": ["role", "is_verified"]}
            ]
            spec.ui_components = ["LoginScreen", "SignupScreen"]
            spec.risks = ["Brute force attacks", "Token leakage"]
            spec.dependencies = ["core/database.py", "core/auth/security.py"]
        elif "inventory" in req_lower:
            spec.goals = ["Implement inventory management tracking items, stock levels, and audits."]
            spec.functional_requirements = ["Add stock item", "Update stock levels", "List items"]
            spec.non_functional_requirements = ["Consistent transactional operations", "Fast query retrieval"]
            spec.apis = [
                {"path": "/inventory/items", "method": "POST", "desc": "Add item"},
                {"path": "/inventory/items", "method": "GET", "desc": "List items"}
            ]
            spec.database_changes = [
                {"table": "inventory_items", "action": "create_table", "columns": ["id", "sku", "quantity"]}
            ]
            spec.ui_components = ["InventoryList", "ItemForm"]
            spec.risks = ["Stock discrepancies", "Race conditions on stock count"]
            spec.dependencies = ["core/database.py"]
        else:
            spec.goals = [f"Implement custom feature: {requirement}"]
            spec.functional_requirements = [f"Fulfill {requirement} core requests"]
            spec.non_functional_requirements = ["Standard REST API standards"]
            spec.apis = [{"path": "/api/custom-feature", "method": "POST", "desc": "Execute feature action"}]
            spec.database_changes = []
            spec.ui_components = ["CustomFeatureView"]
            spec.risks = ["Unknown architecture conflicts"]
            spec.dependencies = []

        return spec
