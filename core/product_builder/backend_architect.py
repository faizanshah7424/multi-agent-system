from typing import List
from pydantic import BaseModel, Field
from core.product_builder.domain_modeler import DomainModel


class BackendPlan(BaseModel):
    services: List[str] = Field(default_factory=list)
    repositories: List[str] = Field(default_factory=list)
    controllers: List[str] = Field(default_factory=list)
    validation_schemas: List[str] = Field(default_factory=list)
    background_jobs: List[str] = Field(default_factory=list)
    queues: List[str] = Field(default_factory=list)
    workers: List[str] = Field(default_factory=list)


class BackendArchitect:
    """
    Constructs high-level backend configurations: services, validation schemas, background jobs.
    """

    def architect_backend(self, model: DomainModel) -> BackendPlan:
        return BackendPlan(
            services=[f"{ent}Service" for ent in model.entities],
            repositories=[f"{ent}Repository" for ent in model.entities],
            controllers=[f"{ent}Controller" for ent in model.entities],
            validation_schemas=[
                schema
                for ent in model.entities
                for schema in [f"{ent}CreateSchema", f"{ent}UpdateSchema"]
            ],
            background_jobs=["DailyReportCompilation", "NotificationBroadcastJob"],
            queues=["kpi_calculation_queue", "email_notification_queue"],
            workers=["KPIWorker", "NotificationWorker"],
        )
