from typing import List, Literal, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class SymbolDefinition(BaseModel):
    """
    Metadata representation of a source code symbol definition.
    """

    name: str = Field(..., description="Name identifier of the symbol.")
    symbol_type: Literal["class", "function", "module", "decorator"] = Field(
        ..., description="Symbol classification."
    )
    file_path: str = Field(..., description="Source path relative to workspace root.")
    start_line: int = Field(..., description="Declaring start line (1-indexed).")
    end_line: int = Field(..., description="Declaring end line (1-indexed).")
    docstring: Optional[str] = Field(None, description="Extracted docstring summary.")
    imports: List[str] = Field(
        default_factory=list, description="Symbol-level import dependencies."
    )


@runtime_checkable
class ICodeIndexer(Protocol):
    """
    Protocol for parsing repositories to build dynamic call graphs and index symbols.
    """

    def index_repository(self, repo_path: str) -> None:
        """
        Scans codebases and generates symbol listings stored in database.
        """
        ...

    def find_symbol(self, name: str) -> List[SymbolDefinition]:
        """
        Looks up occurrences and definitions of a class or function symbol.
        """
        ...

    def get_references(self, symbol_name: str) -> List[str]:
        """
        Locates paths importing or calling a given symbol name.
        """
        ...
