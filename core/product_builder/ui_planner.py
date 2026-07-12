from typing import List, Dict
from pydantic import BaseModel, Field
from core.product_builder.domain_modeler import DomainModel


class UIComponentSpec(BaseModel):
    name: str
    component_type: str  # form, table, chart
    props: List[str] = Field(default_factory=list)


class UIPlan(BaseModel):
    components: List[UIComponentSpec] = Field(default_factory=list)
    charts_spec: List[str] = Field(default_factory=list)
    tables_spec: List[str] = Field(default_factory=list)


class UIPlanner:
    """
    Plans UI components, charts, tables, forms, and prop schemas.
    """

    def plan_ui(self, model: DomainModel) -> UIPlan:
        components = []
        for ent in model.entities:
            components.append(
                UIComponentSpec(
                    name=f"{ent}Form",
                    component_type="form",
                    props=["onSubmit", "initialValues"],
                )
            )
            components.append(
                UIComponentSpec(
                    name=f"{ent}Table",
                    component_type="table",
                    props=["data", "onEdit", "onDelete"],
                )
            )

        return UIPlan(
            components=components,
            charts_spec=[
                "Bar chart for daily metrics",
                "Line chart showing billing trends",
            ],
            tables_spec=[f"Interactive data table for {ent}" for ent in model.entities],
        )
