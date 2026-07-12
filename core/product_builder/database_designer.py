from typing import List
from pydantic import BaseModel, Field
from core.product_builder.domain_modeler import DomainModel


class DatabaseDesignSpecs(BaseModel):
    ddl_scripts: List[str] = Field(default_factory=list)
    schema_details: str


class DatabaseDesigner:
    """
    Transforms logical domain models into physical DDL specs and indices definitions.
    """

    def design_database(self, model: DomainModel) -> DatabaseDesignSpecs:
        ddl = []
        for tbl in model.db_tables:
            ddl.append(
                f"CREATE TABLE {tbl} (\n    id VARCHAR(50) PRIMARY KEY,\n    created_at TIMESTAMP,\n    updated_at TIMESTAMP\n);"
            )

        details = f"Designed {len(model.db_tables)} database tables, including indexes like: {', '.join(model.indexes)}."
        return DatabaseDesignSpecs(ddl_scripts=ddl, schema_details=details)
