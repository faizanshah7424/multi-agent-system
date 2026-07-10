from typing import List
from pydantic import BaseModel, Field
from core.product_builder.business_analyzer import BusinessSpecs

class ProductRequirements(BaseModel):
    vision: str
    goals: List[str] = Field(default_factory=list)
    functional_reqs: List[str] = Field(default_factory=list)
    non_functional_reqs: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)

class RequirementsEngine:
    """
    Formulates structured product visions, functional specs, non-functional targets, and criteria.
    """
    def generate_requirements(self, specs: BusinessSpecs) -> ProductRequirements:
        return ProductRequirements(
            vision=f"A next-generation scalable system for {specs.domain}.",
            goals=[f"Automate primary processes like: {', '.join(specs.workflows[:2])}."],
            functional_reqs=[f"Users with role '{role}' must be able to execute related tasks." for role in specs.user_roles],
            non_functional_reqs=[
                "Performance latency must be <200ms on index routes.",
                "System must scale horizontally with stateless web controllers.",
                "Enforce strict transport layer security with JWT session tokens."
            ],
            constraints=[
                "Enforce Pydantic V2 schemas and Python 3.13 compatibility.",
                "Preserve fully independent unit test databases."
            ],
            risks=[
                "Database lockouts during concurrency spikes.",
                "Unauthorized authorization bypasses."
            ],
            success_metrics=[f"Reach target KPI goals: {', '.join(specs.kpis[:2])}."],
            acceptance_criteria=[
                "100% of REST endpoints covered by integration tests.",
                "UI layouts compile with zero typescript validation warnings."
            ]
        )
