import logging
import threading
import time
from typing import Any, List, Dict, Optional

from config import settings
from core.storage.storage_adapter import IStorageAdapter, tenant_context

logger = logging.getLogger(__name__)


class PostgresStorageAdapter(IStorageAdapter):
    """
    PostgreSQL database adapter supporting multi-tenant queries, connection pooling,
    and safe transactions.
    """

    def __init__(self) -> None:
        self._pool: Optional[Any] = None
        self._local = threading.local()
        self._lock = threading.Lock()
        self.telemetry_history: List[Dict[str, Any]] = []
        self.rollback_count = 0

    def _get_pool(self) -> Any:
        """
        Lazily initializes the ThreadedConnectionPool.
        """
        if self._pool is not None:
            return self._pool

        with self._lock:
            if self._pool is not None:
                return self._pool

            # Lazy import psycopg2 to prevent startup errors if not installed
            import psycopg2
            from psycopg2.pool import ThreadedConnectionPool

            dsn = settings.database_url
            minconn = 1
            maxconn = settings.postgres_pool_size
            timeout = settings.postgres_timeout

            logger.info(
                f"Initializing ThreadedConnectionPool with DSN config, size={maxconn}"
            )
            self._pool = ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                dsn=dsn,
                connect_timeout=int(timeout),
            )
            return self._pool

    def _get_conn(self) -> Any:
        """
        Retrieves a thread-local connection from the pool.
        """
        if not hasattr(self._local, "conn") or self._local.conn is None:
            pool = self._get_pool()
            conn = pool.getconn()
            
            # Auto-commit is false by default in psycopg2 (starts transactions automatically)
            # but we will manage transactions explicitly.
            self._local.conn = conn
            self._local.cursor = conn.cursor()
            self._local.active_cursor = self._local.cursor
            self._local.in_transaction = False
            self._local.tx_start_time = None
            
        return self._local.conn

    def connect(self) -> None:
        """
        Ensures the connection pool is initialized.
        """
        self._get_pool()

    def close(self) -> None:
        """
        Releases the thread-local connection to the pool, and closes the pool.
        """
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.cursor.close()
                if self._pool is not None:
                    self._pool.putconn(self._local.conn)
            except Exception as e:
                logger.debug(f"Error putting connection back to pool: {e}")
            self._local.conn = None
            self._local.cursor = None
            self._local.active_cursor = None

        with self._lock:
            if self._pool is not None:
                try:
                    self._pool.closeall()
                except Exception as e:
                    logger.debug(f"Error closing PostgreSQL pool: {e}")
                self._pool = None

    def execute(self, query: str, params: Optional[Any] = None) -> Any:
        start_time = time.time()
        conn = self._get_conn()
        cursor = self._local.cursor
        tenant = tenant_context.get()

        try:
            # Translate SQL standard placeholder ? to PostgreSQL format %s
            query = query.replace("?", "%s")
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            self._local.active_cursor = cursor
            latency = time.time() - start_time
            self._record_telemetry(query_latency=latency, tenant=tenant)
            return cursor
        except Exception as e:
            logger.warning(f"PostgreSQL execute error: {e}")
            raise e

    def executemany(self, query: str, params: Optional[Any] = None) -> Any:
        start_time = time.time()
        conn = self._get_conn()
        cursor = self._local.cursor
        tenant = tenant_context.get()

        try:
            # Translate SQL standard placeholder ? to PostgreSQL format %s
            query = query.replace("?", "%s")
            if params is not None:
                cursor.executemany(query, params)
            else:
                cursor.executemany(query, [])

            self._local.active_cursor = cursor
            latency = time.time() - start_time
            self._record_telemetry(query_latency=latency, tenant=tenant)
            return cursor
        except Exception as e:
            logger.warning(f"PostgreSQL executemany error: {e}")
            raise e

    def fetchone(self) -> Optional[Any]:
        active_cursor = getattr(self._local, "active_cursor", None)
        if active_cursor is not None:
            return active_cursor.fetchone()
        return None

    def fetchall(self) -> List[Any]:
        active_cursor = getattr(self._local, "active_cursor", None)
        if active_cursor is not None:
            return active_cursor.fetchall()
        return []

    def begin_transaction(self) -> None:
        conn = self._get_conn()
        if not getattr(self._local, "in_transaction", False):
            # Start transaction explicitly
            conn.commit()  # Flush any implicit transaction
            self._local.in_transaction = True
            self._local.tx_start_time = time.time()

    def commit(self) -> None:
        conn = self._get_conn()
        in_tx = getattr(self._local, "in_transaction", False)
        tx_start = getattr(self._local, "tx_start_time", None)

        if in_tx:
            conn.commit()
            duration = time.time() - tx_start if tx_start else 0.0
            self._local.in_transaction = False
            self._local.tx_start_time = None
            self._record_telemetry(
                transaction_duration=duration, tenant=tenant_context.get()
            )
        else:
            conn.commit()

    def rollback(self) -> None:
        conn = self._get_conn()
        in_tx = getattr(self._local, "in_transaction", False)
        tx_start = getattr(self._local, "tx_start_time", None)

        if in_tx:
            conn.rollback()
            duration = time.time() - tx_start if tx_start else 0.0
            self._local.in_transaction = False
            self._local.tx_start_time = None
            self.rollback_count += 1
            self._record_telemetry(
                transaction_duration=duration, tenant=tenant_context.get()
            )
        else:
            conn.rollback()

    def health_check(self) -> bool:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            return row is not None and row[0] == 1
        except Exception:
            return False

    def _get_pool_status(self) -> Dict[str, int]:
        if self._pool is None:
            return {"active_connections": 0, "total_connections": 0}
        with self._lock:
            # ThreadedConnectionPool holds used conns in _used
            active = (
                len(self._pool._used) if hasattr(self._pool, "_used") else 0
            )
            idle = (
                len(self._pool._pool) if hasattr(self._pool, "_pool") else 0
            )
            return {
                "active_connections": active,
                "total_connections": active + idle,
            }

    def _record_telemetry(
        self,
        query_latency: float = 0.0,
        transaction_duration: float = 0.0,
        tenant: str = "default_tenant",
    ) -> None:
        status = self._get_pool_status()
        conn_count = status["total_connections"]

        telemetry = {
            "database_backend": "postgresql",
            "query_latency": query_latency,
            "pool_usage": status,
            "transaction_duration": transaction_duration,
            "connection_count": conn_count,
            "rollback_count": self.rollback_count,
            "tenant_identifier": tenant,
            "timestamp": time.time(),
        }

        with self._lock:
            if len(self.telemetry_history) >= 1000:
                self.telemetry_history.pop(0)
            self.telemetry_history.append(telemetry)
