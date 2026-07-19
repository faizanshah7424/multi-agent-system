import sys
import unittest
from unittest.mock import MagicMock

# Globally mock psycopg2 so PostgreSQL adapter tests run on any system
mock_psycopg2 = MagicMock()
mock_pool_module = MagicMock()
mock_pool_class = MagicMock()
mock_pool_module.ThreadedConnectionPool = mock_pool_class
mock_psycopg2.pool = mock_pool_module

# Configure mock connections and pools
mock_postgres_conn = MagicMock()
mock_postgres_cursor = MagicMock()
mock_postgres_conn.cursor.return_value = mock_postgres_cursor
mock_pool_instance = MagicMock()
mock_pool_instance.getconn.return_value = mock_postgres_conn
mock_pool_class.return_value = mock_pool_instance

sys.modules["psycopg2"] = mock_psycopg2
sys.modules["psycopg2.pool"] = mock_pool_module


from config import settings
from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.storage.storage_adapter import IStorageAdapter, tenant_context
from core.storage.sqlite_adapter import SQLiteStorageAdapter
from core.storage.postgres_adapter import PostgresStorageAdapter
from core.context.retrieval import RetrievalPipeline, get_current_tenant_id


class TestStorageAdapterAndMultiTenancy(unittest.TestCase):
    def setUp(self) -> None:
        DIContainer.clear()
        
        # Backup settings
        self._backup_backend = settings.database_backend
        self._backup_db_url = settings.database_url
        self._backup_sqlite_path = settings.sqlite_path
        self._backup_pool_size = settings.postgres_pool_size
        self._backup_timeout = settings.postgres_timeout
        self._backup_mt_enabled = settings.enable_multi_tenancy
        self._backup_default_tenant = settings.default_tenant_id

        # Defaults for tests
        settings.database_backend = "sqlite"
        settings.database_url = ""
        settings.sqlite_path = ":memory:"  # fast in-memory sqlite
        settings.enable_multi_tenancy = False
        settings.default_tenant_id = "default_tenant"

        bootstrap_di()

    def tearDown(self) -> None:
        # Restore settings
        settings.database_backend = self._backup_backend
        settings.database_url = self._backup_db_url
        settings.sqlite_path = self._backup_sqlite_path
        settings.postgres_pool_size = self._backup_pool_size
        settings.postgres_timeout = self._backup_timeout
        settings.enable_multi_tenancy = self._backup_mt_enabled
        settings.default_tenant_id = self._backup_default_tenant

        # Reset mocks
        mock_pool_class.reset_mock()
        mock_pool_instance.reset_mock()
        mock_postgres_conn.reset_mock()
        mock_postgres_cursor.reset_mock()

    def test_di_registration(self) -> None:
        """
        Verify that IStorageAdapter is correctly registered and SQLite is default.
        """
        storage = DIContainer.get(IStorageAdapter)
        self.assertIsInstance(storage, SQLiteStorageAdapter)

    def test_backend_switching_via_di(self) -> None:
        """
        Verify that switching configuration updates DI registration dynamically.
        """
        DIContainer.clear()
        settings.database_backend = "postgres"
        bootstrap_di()

        storage = DIContainer.get(IStorageAdapter)
        self.assertIsInstance(storage, PostgresStorageAdapter)

    def test_sqlite_adapter_basics(self) -> None:
        """
        Verify SQLite connections, parameter query execution, and transactions.
        """
        adapter = SQLiteStorageAdapter()
        adapter.connect()
        self.assertTrue(adapter.health_check())

        # Test execute and fetch
        adapter.execute("SELECT ? as num", (42,))
        row = adapter.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 42)

        # Test transaction commit
        adapter.begin_transaction()
        adapter.execute("SELECT 1")
        adapter.commit()

        # Test transaction rollback
        adapter.begin_transaction()
        adapter.execute("SELECT 2")
        adapter.rollback()
        self.assertEqual(adapter.rollback_count, 1)

        adapter.close()

    def test_postgres_adapter_basics(self) -> None:
        """
        Verify Postgres pool lazy loading, statement translation, and connection reuse.
        """
        settings.database_backend = "postgres"
        settings.database_url = "postgresql://user:pass@host:5432/db"
        settings.postgres_pool_size = 8
        settings.postgres_timeout = 15.0

        adapter = PostgresStorageAdapter()
        # Verify lazy initialization
        self.assertIsNone(adapter._pool)

        adapter.connect()
        self.assertIsNotNone(adapter._pool)
        mock_pool_class.assert_called_once_with(
            minconn=1, maxconn=8, dsn=settings.database_url, connect_timeout=15
        )

        # Verify query translation (translating standard ? to psycopg2 %s)
        adapter.execute("SELECT * FROM users WHERE id = ? AND name = ?", (123, "Alice"))
        mock_postgres_cursor.execute.assert_called_once_with(
            "SELECT * FROM users WHERE id = %s AND name = %s", (123, "Alice")
        )

        # Verify transaction commit
        adapter.begin_transaction()
        adapter.commit()
        mock_postgres_conn.commit.assert_called()

        # Verify transaction rollback
        adapter.begin_transaction()
        adapter.rollback()
        mock_postgres_conn.rollback.assert_called()
        self.assertEqual(adapter.rollback_count, 1)

        # Close pool
        adapter.close()
        mock_pool_instance.putconn.assert_called_once_with(mock_postgres_conn)
        mock_pool_instance.closeall.assert_called_once()

    def test_tenant_isolation(self) -> None:
        """
        Verify that retrieval queries strictly restrict scopes to the active tenant.
        """
        settings.enable_multi_tenancy = True
        
        storage = SQLiteStorageAdapter()
        pipeline = RetrievalPipeline(storage=storage)

        # Seed data for Tenant A
        tenant_context.set("tenant_A")
        storage.execute(
            """
            INSERT INTO retrieval_code_symbols 
            (tenant_id, task_id, file_path, symbol_name, symbol_type, start_line, end_line, content, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("tenant_A", "t1", "file_a.py", "func_a", "def", 1, 10, "content a", "hash_a")
        )

        # Seed data for Tenant B
        tenant_context.set("tenant_B")
        storage.execute(
            """
            INSERT INTO retrieval_code_symbols 
            (tenant_id, task_id, file_path, symbol_name, symbol_type, start_line, end_line, content, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("tenant_B", "t1", "file_b.py", "func_b", "def", 1, 10, "content b", "hash_b")
        )

        # Query as Tenant A -> should only see Tenant A's documents
        tenant_context.set("tenant_A")
        results_a = pipeline._get_all_indexed_chunks("t1")
        self.assertEqual(len(results_a), 1)
        self.assertEqual(results_a[0].file_path, "file_a.py")

        # Query as Tenant B -> should only see Tenant B's documents
        tenant_context.set("tenant_B")
        results_b = pipeline._get_all_indexed_chunks("t1")
        self.assertEqual(len(results_b), 1)
        self.assertEqual(results_b[0].file_path, "file_b.py")

    def test_telemetry(self) -> None:
        """
        Verify that database executions record performance and structural telemetry.
        """
        tenant_context.set("test_tenant")
        storage = SQLiteStorageAdapter()
        storage.connect()
        storage.execute("SELECT 1")

        self.assertGreater(len(storage.telemetry_history), 0)
        tel = storage.telemetry_history[-1]
        self.assertEqual(tel["database_backend"], "sqlite")
        self.assertEqual(tel["tenant_identifier"], "test_tenant")
        self.assertIn("query_latency", tel)
        self.assertIn("connection_count", tel)

    def test_backward_compatibility(self) -> None:
        """
        Verify that when multi-tenancy is disabled, the tenant_id defaults to default_tenant_id.
        """
        settings.enable_multi_tenancy = False
        settings.default_tenant_id = "default_legacy_id"

        # Even if a context tenant is set, the pipeline must resolve to the default legacy ID.
        tenant_context.set("custom_tenant")
        resolved = get_current_tenant_id()
        self.assertEqual(resolved, "default_legacy_id")
