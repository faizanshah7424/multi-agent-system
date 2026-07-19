import contextvars
from typing import Any, List, Optional, Protocol, runtime_checkable

# Thread-safe and async-safe context variable for multi-tenant isolation
tenant_context = contextvars.ContextVar("tenant_id", default="default_tenant")


@runtime_checkable
class IStorageAdapter(Protocol):
    """
    Interface for database operations, decoupling the application from the physical backend.
    """

    def connect(self) -> None:
        """
        Establishes a connection or initializes the connection pool.
        """
        ...

    def close(self) -> None:
        """
        Closes active connections or connection pools.
        """
        ...

    def execute(self, query: str, params: Optional[Any] = None) -> Any:
        """
        Executes a single SQL statement.
        """
        ...

    def executemany(self, query: str, params: Optional[Any] = None) -> Any:
        """
        Executes an SQL statement against multiple parameter sets.
        """
        ...

    def fetchone(self) -> Optional[Any]:
        """
        Fetches the next row of a query result.
        """
        ...

    def fetchall(self) -> List[Any]:
        """
        Fetches all rows of a query result.
        """
        ...

    def begin_transaction(self) -> None:
        """
        Begins a database transaction.
        """
        ...

    def commit(self) -> None:
        """
        Commits the current database transaction.
        """
        ...

    def rollback(self) -> None:
        """
        Rolls back the current database transaction.
        """
        ...

    def health_check(self) -> bool:
        """
        Verifies if the database backend is healthy and reachable.
        """
        ...
