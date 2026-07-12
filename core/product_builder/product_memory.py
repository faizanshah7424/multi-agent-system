import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ProductRecord(BaseModel):
    id: str
    idea: str
    domain: str
    requirements: Dict[str, Any] = Field(default_factory=dict)
    architecture: Dict[str, Any] = Field(default_factory=dict)
    generated_documents: Dict[str, str] = Field(default_factory=dict)
    confidence: float
    debate_results: Dict[str, Any] = Field(default_factory=dict)
    execution_duration_seconds: float
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ProductMemory:
    """
    Manages persistent SQLite logging of all product requirements, DDL architectures, and outputs.
    """

    def __init__(self, db_path: str = "data/learning.db"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_tables()

    def initialize_tables(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_product_records (
                id TEXT PRIMARY KEY,
                idea TEXT,
                domain TEXT,
                requirements TEXT,
                architecture TEXT,
                generated_documents TEXT,
                confidence REAL,
                debate_results TEXT,
                execution_duration_seconds REAL,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_record(self, record: ProductRecord) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO autonomous_product_records (
                id, idea, domain, requirements, architecture, generated_documents, confidence, debate_results, execution_duration_seconds, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.id,
                record.idea,
                record.domain,
                json.dumps(record.requirements),
                json.dumps(record.architecture),
                json.dumps(record.generated_documents),
                record.confidence,
                json.dumps(record.debate_results),
                record.execution_duration_seconds,
                record.timestamp,
            ),
        )
        conn.commit()
        conn.close()

    def list_records(self) -> List[ProductRecord]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM autonomous_product_records ORDER BY timestamp DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        records = []
        for r in rows:
            records.append(
                ProductRecord(
                    id=r[0],
                    idea=r[1],
                    domain=r[2],
                    requirements=json.loads(r[3] or "{}"),
                    architecture=json.loads(r[4] or "{}"),
                    generated_documents=json.loads(r[5] or "{}"),
                    confidence=r[6],
                    debate_results=json.loads(r[7] or "{}"),
                    execution_duration_seconds=r[8],
                    timestamp=r[9],
                )
            )
        return records
