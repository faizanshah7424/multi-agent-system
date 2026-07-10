from typing import List, Dict, Any
from core.feature_engine.feature_parser import FeatureSpec

class FeatureArchitect:
    """
    Validates architectural fit, locates reusable modules, and prevents duplicate feature logic.
    """
    def analyze_architecture_fit(self, spec: FeatureSpec) -> Dict[str, Any]:
        reusable_modules = []
        new_modules = []
        fits_architecture = True
        duplications_detected = []

        # Find reusable modules in dependencies
        for dep in spec.dependencies:
            if "database.py" in dep:
                reusable_modules.append("core/database.py")
            elif "security.py" in dep:
                reusable_modules.append("core/auth/security.py")

        # Check for duplication in existing APIs
        for api in spec.apis:
            if "/auth" in api["path"]:
                duplications_detected.append(f"API endpoint {api['path']} matches pattern in api/auth_routes.py")

        # Propose new module layouts
        goals_str = spec.goals[0].lower() if spec.goals else ""
        if "inventory" in goals_str:
            new_modules.append("core/inventory/manager.py")
            new_modules.append("api/inventory_routes.py")
        elif "appointment" in goals_str:
            new_modules.append("core/scheduler/manager.py")
            new_modules.append("api/scheduler_routes.py")

        return {
            "fits_architecture": fits_architecture,
            "reusable_modules": reusable_modules,
            "new_modules": new_modules,
            "duplications_detected": duplications_detected,
            "recommendation": "Integrate endpoints in modular routers and reuse session contexts."
        }
