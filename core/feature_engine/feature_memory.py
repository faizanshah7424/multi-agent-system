import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field


class FeatureRecord(BaseModel):
    id: str
    feature_name: str
    execution_duration_seconds: float
    files_modified: List[str] = Field(default_factory=list)
    success_rate: float = 1.0  # 1.0 = success, 0.0 = failed
    confidence: float
    lessons_learned: List[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class FeatureMemory:
    """
    Saves and indexes feature generation logs in database storage.
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
            CREATE TABLE IF NOT EXISTS autonomous_feature_records (
                id TEXT PRIMARY KEY,
                feature_name TEXT,
                execution_duration_seconds REAL,
                files_modified TEXT,
                success_rate REAL,
                confidence REAL,
                lessons_learned TEXT,
                timestamp TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def add_record(self, record: FeatureRecord) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO autonomous_feature_records (
                id, feature_name, execution_duration_seconds, files_modified, success_rate, confidence, lessons_learned, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.id,
                record.feature_name,
                record.execution_duration_seconds,
                json.dumps(record.files_modified),
                record.success_rate,
                record.confidence,
                json.dumps(record.lessons_learned),
                record.timestamp,
            ),
        )
        conn.commit()
        conn.close()

    def list_records(self) -> List[FeatureRecord]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM autonomous_feature_records ORDER BY timestamp DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        records = []
        for r in rows:
            records.append(
                FeatureRecord(
                    id=r[0],
                    feature_name=r[1],
                    execution_duration_seconds=r[2],
                    files_modified=json.loads(r[3] or "[]"),
                    success_rate=r[4],
                    confidence=r[5],
                    lessons_learned=json.loads(r[6] or "[]"),
                    timestamp=r[7],
                )
            )
        return records
