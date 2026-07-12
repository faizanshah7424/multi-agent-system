import os
import sqlite3
from datetime import datetime, timezone
from typing import List


class MigrationManager:
    """
    Handles schema migrations, version tracking, validation, and rollback procedures.
    """

    def __init__(self, db_path: str = "data/learning.db"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_migration_table()

    def initialize_migration_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                sql_script TEXT,
                rollback_script TEXT,
                applied_at TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def apply_migration(
        self, version: str, sql_script: str, rollback_script: str
    ) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cleaned_sql = sql_script.strip()
            if cleaned_sql and not cleaned_sql.startswith("--"):
                cursor.executescript(cleaned_sql)

            cursor.execute(
                """
                INSERT OR REPLACE INTO schema_migrations (version, sql_script, rollback_script, applied_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    version,
                    sql_script,
                    rollback_script,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[MIGRATION ERROR] {str(e)}")
            return False
        finally:
            conn.close()

    def rollback_migration(self, version: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT rollback_script FROM schema_migrations WHERE version = ?",
                (version,),
            )
            row = cursor.fetchone()
            if not row:
                return False

            rollback_script = row[0]
            cleaned_rollback = rollback_script.strip()
            if cleaned_rollback and not cleaned_rollback.startswith("--"):
                cursor.executescript(cleaned_rollback)

            cursor.execute(
                "DELETE FROM schema_migrations WHERE version = ?", (version,)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[ROLLBACK ERROR] {str(e)}")
            return False
        finally:
            conn.close()

    def validate_migrations(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]
