import os
import sys
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Setup system path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from core.database import (
    init_db,
    get_db_session,
    Task,
    TaskLog,
    AgentMessage,
    MemoryEntry,
    WorkflowExecution,
)
from core.repositories import TaskRepository, MemoryRepository, WorkflowRepository


def migrate():
    print("=== Starting JSON to SQLite Migration Audit ===")

    # 1. Initialize SQLite Database schemas
    init_db()

    persist_dir = settings.persist_path
    tasks_dir = persist_dir / "tasks"
    memory_dir = persist_dir / "memory"

    tasks_migrated = 0
    logs_migrated = 0
    messages_migrated = 0
    steps_migrated = 0
    memory_migrated = 0

    # Run the entire migration atomically in a single database transaction
    try:
        with get_db_session() as session:
            task_repo = TaskRepository(session)
            mem_repo = MemoryRepository(session)
            work_repo = WorkflowRepository(session)

            # --- PHASE 1: Migrate Tasks ---
            if tasks_dir.exists():
                print("1. Migrating Task Records...")
                for task_file in tasks_dir.glob("*.json"):
                    try:
                        with open(task_file, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        # Validate basic fields
                        task_id = data.get("task_id")
                        if not task_id:
                            print(
                                f"   [Warning] Skipped invalid task file: {task_file}"
                            )
                            continue

                        # Format timestamps
                        created_at = (
                            datetime.fromisoformat(data.get("created_at"))
                            if data.get("created_at")
                            else datetime.now(timezone.utc).replace(tzinfo=None)
                        )
                        started_at = (
                            datetime.fromisoformat(data.get("started_at"))
                            if data.get("started_at")
                            else None
                        )
                        completed_at = (
                            datetime.fromisoformat(data.get("completed_at"))
                            if data.get("completed_at")
                            else None
                        )

                        # Insert Task
                        db_task = Task(
                            task_id=task_id,
                            user_id=data.get("user_id"),
                            task_type=data.get("task_type", "workflow"),
                            payload_json=data.get("payload", {}),
                            status=data.get("status", "QUEUED"),
                            created_at=created_at,
                            started_at=started_at,
                            completed_at=completed_at,
                            retry_count=data.get("retry_count", 0),
                            error=data.get("error"),
                        )
                        session.add(db_task)
                        tasks_migrated += 1

                    except Exception as te:
                        print(
                            f"   [Error] Failed to read/parse task file {task_file}: {str(te)}"
                        )
                        raise te
                # Flush tasks to SQLite so they exist when Phase 2 processes logs/messages (preventing FOREIGN KEY errors)
                session.flush()

            # --- PHASE 2: Migrate Session Logs, Messages, and Steps ---
            print("2. Migrating Session Memory Logs and Message History...")
            for session_file in persist_dir.glob("*.json"):
                # Skip files inside memory or tasks folders
                if session_file.parent != persist_dir:
                    continue
                # Skip database system file or any temp files that match by accident
                if session_file.stem == "system" or session_file.name.endswith(".db"):
                    continue

                try:
                    session_id = session_file.stem
                    with open(session_file, "r", encoding="utf-8") as f:
                        state_data = json.load(f)

                    # A. Migrate Logs
                    logs_list = state_data.get("logs", [])
                    for log_entry in logs_list:
                        ts = (
                            datetime.fromisoformat(log_entry.get("timestamp"))
                            if log_entry.get("timestamp")
                            else datetime.now(timezone.utc).replace(tzinfo=None)
                        )
                        db_log = TaskLog(
                            task_id=session_id,
                            source=log_entry.get("agent", "system"),
                            message=log_entry.get("message", ""),
                            level=log_entry.get("level", "INFO"),
                            timestamp=ts,
                        )
                        session.add(db_log)
                        logs_migrated += 1

                    # B. Migrate Messages
                    msgs_list = state_data.get("messages", [])
                    for msg_entry in msgs_list:
                        ts = (
                            datetime.fromisoformat(msg_entry.get("timestamp"))
                            if msg_entry.get("timestamp")
                            else datetime.now(timezone.utc).replace(tzinfo=None)
                        )
                        db_msg = AgentMessage(
                            task_id=session_id,
                            role=msg_entry.get("receiver", "assistant"),
                            agent_name=msg_entry.get("sender", "assistant"),
                            content=msg_entry.get("content", ""),
                            timestamp=ts,
                        )
                        session.add(db_msg)
                        messages_migrated += 1

                    # C. Migrate Workflow Steps (if stored in variables data dict)
                    steps_list = state_data.get("data", {}).get("workflow_steps", [])
                    for step_entry in steps_list:
                        start_t = (
                            datetime.fromisoformat(step_entry.get("started_at"))
                            if step_entry.get("started_at")
                            else None
                        )
                        end_t = (
                            datetime.fromisoformat(step_entry.get("completed_at"))
                            if step_entry.get("completed_at")
                            else None
                        )
                        db_step = WorkflowExecution(
                            task_id=session_id,
                            step_id=step_entry.get("step_id", 0),
                            name=step_entry.get("name", "Unnamed Step"),
                            description=step_entry.get("description", ""),
                            assigned_agent=step_entry.get(
                                "assigned_agent", "developer"
                            ),
                            status=step_entry.get("status", "pending"),
                            result=step_entry.get("result"),
                            started_at=start_t,
                            completed_at=end_t,
                        )
                        session.add(db_step)
                        steps_migrated += 1

                except Exception as se:
                    print(
                        f"   [Error] Failed to read/parse memory session file {session_file}: {str(se)}"
                    )
                    raise se

            # --- PHASE 3: Migrate Semantic Vector Memory ---
            if memory_dir.exists():
                print("3. Migrating Semantic Vector Memories...")
                for index_file in memory_dir.glob("*.json"):
                    try:
                        index_name = index_file.stem
                        with open(index_file, "r", encoding="utf-8") as f:
                            items_data = json.load(f)

                        for item in items_data:
                            ts = (
                                datetime.fromisoformat(item.get("timestamp"))
                                if item.get("timestamp")
                                else datetime.now(timezone.utc).replace(tzinfo=None)
                            )

                            # Embed the vector inside metadata_json for SQLite storage
                            metadata = item.get("metadata", {})
                            metadata["vector"] = item.get("vector", [])

                            db_entry = MemoryEntry(
                                session_id=index_name,
                                text=item.get("text", ""),
                                metadata_json=metadata,
                                timestamp=ts,
                            )
                            session.add(db_entry)
                            memory_migrated += 1

                    except Exception as me:
                        print(
                            f"   [Error] Failed to read/parse vector index file {index_file}: {str(me)}"
                        )
                        raise me

        print("\n=== MIGRATION COMPLETE ===")
        print(f"Tasks Migrated:      {tasks_migrated}")
        print(f"Logs Migrated:       {logs_migrated}")
        print(f"Messages Migrated:   {messages_migrated}")
        print(f"Steps Migrated:      {steps_migrated}")
        print(f"Memories Migrated:   {memory_migrated}")
        print("Status: SUCCESS (Atomic Transaction Committed)")

    except Exception as e:
        print(f"\nFATAL: Migration aborted and rolled back. Error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    migrate()
