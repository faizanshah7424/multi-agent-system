import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class RepositoryRecord(BaseModel):
    id: str
    goal: str
    repo_snapshot: Dict[str, Any] = Field(default_factory=dict)
    generated_files: List[str] = Field(default_factory=list)
    confidence: float
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    rollback_snapshot: str = ""
    execution_duration_seconds: float
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RepositoryMemory:
    """
    Saves and indexes autonomous repository engineering records in SQLite storage.
    """

    def __init__(self, db_path: str = "data/learning.db"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_tables()

    def initialize_tables(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS autonomous_repository_records (
                id TEXT PRIMARY KEY,
                goal TEXT,
                repo_snapshot TEXT,
                generated_files TEXT,
                confidence REAL,
                validation_results TEXT,
                rollback_snapshot TEXT,
                execution_duration_seconds REAL,
                timestamp TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def add_record(self, record: RepositoryRecord) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO autonomous_repository_records (
                id, goal, repo_snapshot, generated_files, confidence, validation_results, rollback_snapshot, execution_duration_seconds, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.id,
                record.goal,
                json.dumps(record.repo_snapshot),
                json.dumps(record.generated_files),
                record.confidence,
                json.dumps(record.validation_results),
                record.rollback_snapshot,
                record.execution_duration_seconds,
                record.timestamp,
            ),
        )
        conn.commit()
        conn.close()

    def list_records(self) -> List[RepositoryRecord]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM autonomous_repository_records ORDER BY timestamp DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        records = []
        for r in rows:
            records.append(
                RepositoryRecord(
                    id=r[0],
                    goal=r[1],
                    repo_snapshot=json.loads(r[2] or "{}"),
                    generated_files=json.loads(r[3] or "[]"),
                    confidence=r[4],
                    validation_results=json.loads(r[5] or "{}"),
                    rollback_snapshot=r[6],
                    execution_duration_seconds=r[7],
                    timestamp=r[8],
                )
            )
        return records
