from typing import List, Dict, Any
from pydantic import BaseModel, Field
from core.product_builder.business_analyzer import BusinessSpecs

class EntityRelation(BaseModel):
    source: str
    target: str
    relation_type: str  # one-to-many, many-to-one, etc.

class DomainModel(BaseModel):
    entities: List[str] = Field(default_factory=list)
    relationships: List[EntityRelation] = Field(default_factory=list)
    db_tables: List[str] = Field(default_factory=list)
    indexes: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    er_diagram_data: Dict[str, Any] = Field(default_factory=dict)

class DomainModeler:
    """
    Constructs database entity mappings, relationships, keys, indexes, and ER diagram formats.
    """
    def model_domain(self, specs: BusinessSpecs) -> DomainModel:
        relationships = []
        if len(specs.entities) >= 2:
            relationships.append(EntityRelation(
                source=specs.entities[0],
                target=specs.entities[1],
                relation_type="one-to-many"
            ))
            if len(specs.entities) >= 3:
                relationships.append(EntityRelation(
                    source=specs.entities[1],
                    target=specs.entities[2],
                    relation_type="many-to-one"
                ))

        db_tables = [f"tbl_{entity.lower()}s" for entity in specs.entities]
        indexes = [f"idx_{entity.lower()}_id" for entity in specs.entities]
        constraints = [f"fk_{entity.lower()}_user_id" for entity in specs.entities]

        er_nodes = [{"id": ent, "label": ent} for ent in specs.entities]
        er_edges = [{"from": rel.source, "to": rel.target, "label": rel.relation_type} for rel in relationships]

        return DomainModel(
            entities=specs.entities,
            relationships=relationships,
            db_tables=db_tables,
            indexes=indexes,
            constraints=constraints,
            er_diagram_data={"nodes": er_nodes, "edges": er_edges}
        )
