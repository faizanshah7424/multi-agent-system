from typing import List, Dict
from pydantic import BaseModel, Field
from core.product_builder.domain_modeler import DomainModel


class FrontendPlan(BaseModel):
    pages: List[str] = Field(default_factory=list)
    layouts: List[str] = Field(default_factory=list)
    navigation_tree: Dict[str, List[str]] = Field(default_factory=dict)
    responsive_design_rules: List[str] = Field(default_factory=list)


class FrontendArchitect:
    """
    Plans high-level frontend assets: navigation paths, core screens, and global shell layouts.
    """

    def architect_frontend(self, model: DomainModel) -> FrontendPlan:
        pages = ["Dashboard", "Settings"] + [f"{ent}View" for ent in model.entities]
        layouts = ["DashboardLayout", "AuthLayout"]
        nav = {
            "root": ["Dashboard", "Settings"],
            "features": [f"{ent}View" for ent in model.entities],
        }
        rules = [
            "Tailwind CSS flex grid sizing.",
            "Mobile sidebar collapsible hamburger overlay.",
            "Dynamic glassmorphism theme support.",
        ]
        return FrontendPlan(
            pages=pages,
            layouts=layouts,
            navigation_tree=nav,
            responsive_design_rules=rules,
        )
