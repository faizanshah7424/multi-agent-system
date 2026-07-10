from typing import List
from pydantic import BaseModel, Field

class DeploymentPlan(BaseModel):
    environments: List[str] = Field(default_factory=list)
    infrastructure_providers: List[str] = Field(default_factory=list)
    cicd_pipelines: List[str] = Field(default_factory=list)
    backup_strategies: List[str] = Field(default_factory=list)

class DeploymentPlanner:
    """
    Formulates standard staging and production setup blueprints.
    """
    def plan_deployment(self) -> DeploymentPlan:
        return DeploymentPlan(
            environments=["development", "staging", "production"],
            infrastructure_providers=["AWS (ECS/RDS/ElastiCache)", "Vercel (Frontend Next.js)"],
            cicd_pipelines=["GitHub Actions (lint, test, Docker build, Deploy to AWS ECS)"],
            backup_strategies=["Hourly database snapshots", "Multi-region S3 replication"]
        )
