from typing import List
from pydantic import BaseModel, Field
from core.product_builder.domain_modeler import DomainModel

class TestingPlan(BaseModel):
    unit_tests: List[str] = Field(default_factory=list)
    integration_tests: List[str] = Field(default_factory=list)
    performance_tests: List[str] = Field(default_factory=list)
    mock_dependencies: List[str] = Field(default_factory=list)

class TestingPlanner:
    """
    Plans testing requirements, mock objects, and stress load bounds.
    """
    def plan_tests(self, model: DomainModel) -> TestingPlan:
        units = [f"test_{ent.lower()}_crud" for ent in model.entities]
        integrations = [f"test_{ent.lower()}_workflows" for ent in model.entities]
        mocks = ["S3StorageMock", "PaymentGatewayMock", "EmailClientMock"]
        return TestingPlan(
            unit_tests=units,
            integration_tests=integrations,
            performance_tests=["LoadTestIndexEndpoints", "ConcurrentBookingPressureTest"],
            mock_dependencies=mocks
        )
