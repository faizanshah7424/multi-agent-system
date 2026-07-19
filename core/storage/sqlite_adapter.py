import logging
import threading
import time
from pathlib import Path
from typing import Any, List, Dict, Optional

import sqlite3
from config import settings
from core.storage.storage_adapter import IStorageAdapter, tenant_context

logger = logging.getLogger(__name__)


class SQLiteStorageAdapter(IStorageAdapter):
    """
    SQLite database adapter supporting multi-tenant queries, thread-local connections,
    and safe transactions.
    """

    def __init__(self) -> None:
        self._local = threading.local()
        self._connections: List[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self.telemetry_history: List[Dict[str, Any]] = []
        self.rollback_count = 0

    def _get_conn(self) -> sqlite3.Connection:
        """
        Retrieves or initializes a thread-local SQLite connection.
        """
        if not hasattr(self._local, "conn") or self._local.conn is None:
            sqlite_path = settings.sqlite_path
            if not sqlite_path:
                db_path = settings.persist_path / "system.db"
            else:
                db_path = Path(sqlite_path)

            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Opening SQLite connection to {db_path} on thread {threading.get_ident()}")
            conn = sqlite3.connect(str(db_path), timeout=30.0)
            
            from core.context.budget import DatabaseConfigurator
            DatabaseConfigurator.configure_connection(conn, "sqlite")
            
            self._local.conn = conn
            self._local.cursor = conn.cursor()
            self._local.active_cursor = self._local.cursor
            self._local.in_transaction = False
            self._local.tx_start_time = None
            
            with self._lock:
                self._connections.append(conn)

        return self._local.conn

    def connect(self) -> None:
        """
        Initializes the database connection. Connections are created lazily.
        """
        self._get_conn()

    def close(self) -> None:
        """
        Closes all cached connections across threads.
        """
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.debug(f"Error closing SQLite connection: {e}")
            self._connections.clear()
            
        if hasattr(self._local, "conn"):
            self._local.conn = None
            self._local.cursor = None
            self._local.active_cursor = None

    def execute(self, query: str, params: Optional[Any] = None) -> Any:
        start_time = time.time()
        conn = self._get_conn()
        cursor = self._local.cursor
        tenant = tenant_context.get()

        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self._local.active_cursor = cursor
            latency = time.time() - start_time
            self._record_telemetry(query_latency=latency, tenant=tenant)
            return cursor
        except Exception as e:
            logger.warning(f"SQLite execute error: {e}")
            raise e

    def executemany(self, query: str, params: Optional[Any] = None) -> Any:
        start_time = time.time()
        conn = self._get_conn()
        cursor = self._local.cursor
        tenant = tenant_context.get()

        try:
            if params is not None:
                cursor.executemany(query, params)
            else:
                cursor.executemany(query, [])
                
            self._local.active_cursor = cursor
            latency = time.time() - start_time
            self._record_telemetry(query_latency=latency, tenant=tenant)
            return cursor
        except Exception as e:
            logger.warning(f"SQLite executemany error: {e}")
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
            # In SQLite, executing BEGIN starts a transaction manually in WAL mode
            conn.execute("BEGIN TRANSACTION")
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
            self._record_telemetry(transaction_duration=duration, tenant=tenant_context.get())

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
            self._record_telemetry(transaction_duration=duration, tenant=tenant_context.get())

    def health_check(self) -> bool:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            return row is not None and row[0] == 1
        except Exception:
            return False

    def _record_telemetry(
        self,
        query_latency: float = 0.0,
        transaction_duration: float = 0.0,
        tenant: str = "default_tenant",
    ) -> None:
        with self._lock:
            conn_count = len(self._connections)
            
        telemetry = {
            "database_backend": "sqlite",
            "query_latency": query_latency,
            "pool_usage": {
                "active_connections": 1 if hasattr(self._local, "conn") and self._local.conn else 0,
                "total_connections": conn_count,
            },
            "transaction_duration": transaction_duration,
            "connection_count": conn_count,
            "rollback_count": self.rollback_count,
            "tenant_identifier": tenant,
            "timestamp": time.time(),
        }
        
        # Keep list size bounded
        with self._lock:
            if len(self.telemetry_history) >= 1000:
                self.telemetry_history.pop(0)
            self.telemetry_history.append(telemetry)
