from typing import List, Optional
from sqlalchemy import Column, String, Integer, Text, Table
from core.database import Base, engine, get_db_session
from core.indexer.interface import SymbolDefinition


# SQLAlchemy Model for Code Symbols
class DBSymbol(Base):
    __tablename__ = "code_symbols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    symbol_type = Column(
        String(50), nullable=False, index=True
    )  # class, function, method, module, decorator
    file_path = Column(String(512), nullable=False, index=True)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    docstring = Column(Text, nullable=True)
    parent_scope = Column(String(255), nullable=True)


# SQLAlchemy Model for Relationship Edges
class DBCodeEdge(Base):
    __tablename__ = "code_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String(512), nullable=False, index=True)
    target_file = Column(String(512), nullable=False, index=True)
    relation_type = Column(
        String(50), nullable=False, index=True
    )  # import, dependency, parent, child


# Auto-initialize tables in target SQLite DB
Base.metadata.create_all(bind=engine)


class CodeGraphDB:
    """
    Handles SQLite transactions for persisting and querying symbol definitions
    and dependency edges.
    """

    def clear_symbols(self) -> None:
        """Clears all symbols and edges in the database."""
        with get_db_session() as session:
            session.query(DBSymbol).delete()
            session.query(DBCodeEdge).delete()

    def insert_symbols(self, symbols: List[SymbolDefinition]) -> None:
        """Persists a list of SymbolDefinitions into code_symbols."""
        with get_db_session() as session:
            for s in symbols:
                db_sym = DBSymbol(
                    name=s.name,
                    symbol_type=s.symbol_type,
                    file_path=s.file_path,
                    start_line=s.start_line,
                    end_line=s.end_line,
                    docstring=s.docstring,
                    parent_scope=None,  # Calculated from AST nesting or parent
                )
                session.add(db_sym)

    def insert_edges(
        self, source_file: str, target_file: str, relation_type: str
    ) -> None:
        """Inserts a directed relation edge between files."""
        with get_db_session() as session:
            edge = DBCodeEdge(
                source_file=source_file,
                target_file=target_file,
                relation_type=relation_type,
            )
            session.add(edge)

    def query_symbols(self, name: str) -> List[SymbolDefinition]:
        """Queries symbols matching a specific identifier name."""
        with get_db_session() as session:
            db_symbols = session.query(DBSymbol).filter(DBSymbol.name == name).all()
            return [
                SymbolDefinition(
                    name=s.name,
                    symbol_type=s.symbol_type,
                    file_path=s.file_path,
                    start_line=s.start_line,
                    end_line=s.end_line,
                    docstring=s.docstring,
                    imports=[],  # Resolved dynamically
                )
                for s in db_symbols
            ]

    def query_edges_by_source(self, source_file: str) -> List[str]:
        """Finds all target files a source file depends on (outgoing edges)."""
        with get_db_session() as session:
            edges = (
                session.query(DBCodeEdge)
                .filter(DBCodeEdge.source_file == source_file)
                .all()
            )
            return [e.target_file for e in edges]

    def query_edges_by_target(self, target_file: str) -> List[str]:
        """Finds all source files that depend on a target file (incoming edges)."""
        with get_db_session() as session:
            edges = (
                session.query(DBCodeEdge)
                .filter(DBCodeEdge.target_file == target_file)
                .all()
            )
            return [e.source_file for e in edges]
