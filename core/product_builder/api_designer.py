from typing import List, Dict
from pydantic import BaseModel, Field
from core.product_builder.domain_modeler import DomainModel

class EndpointSpec(BaseModel):
    method: str
    path: str
    description: str
    parameters: List[str] = Field(default_factory=list)

class ApiDesignSpecs(BaseModel):
    endpoints: List[EndpointSpec] = Field(default_factory=list)
    auth_mechanism: str = "Bearer JWT Tokenization"
    search_spec: str
    filtering_spec: str
    pagination_spec: str
    analytics_endpoints: List[EndpointSpec] = Field(default_factory=list)

class ApiDesigner:
    """
    Designs standard REST APIs covering auth, CRUD endpoints, and search filters.
    """
    def design_apis(self, model: DomainModel) -> ApiDesignSpecs:
        endpoints = [
            EndpointSpec(method="POST", path="/auth/login", description="Authenticate sessions"),
            EndpointSpec(method="POST", path="/auth/signup", description="Enroll users")
        ]

        for ent in model.entities:
            ent_lower = ent.lower()
            endpoints.append(EndpointSpec(
                method="GET",
                path=f"/api/{ent_lower}s",
                description=f"Query list of {ent_lower}s",
                parameters=["page", "limit", "filter", "search"]
            ))
            endpoints.append(EndpointSpec(
                method="POST",
                path=f"/api/{ent_lower}s",
                description=f"Create a new {ent_lower}"
            ))
            endpoints.append(EndpointSpec(
                method="GET",
                path=f"/api/{ent_lower}s/{{id}}",
                description=f"Fetch a specific {ent_lower}"
            ))
            endpoints.append(EndpointSpec(
                method="PUT",
                path=f"/api/{ent_lower}s/{{id}}",
                description=f"Update a specific {ent_lower}"
            ))
            endpoints.append(EndpointSpec(
                method="DELETE",
                path=f"/api/{ent_lower}s/{{id}}",
                description=f"Remove a specific {ent_lower}"
            ))

        analytics = [
            EndpointSpec(method="GET", path="/api/analytics/summary", description="Fetch business KPI summaries"),
            EndpointSpec(method="GET", path="/api/analytics/trends", description="Fetch billing and admissions rate charts data")
        ]

        return ApiDesignSpecs(
            endpoints=endpoints,
            search_spec="Supports exact and partial token search via SQL LIKE or Postgres Vector search.",
            filtering_spec="Standard filtering on status, created_at, and relational foreign keys.",
            pagination_spec="Cursor-based and skip/limit query offset pagination.",
            analytics_endpoints=analytics
        )
