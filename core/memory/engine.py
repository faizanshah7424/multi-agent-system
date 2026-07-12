import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, Integer, DateTime, Text
from core.database import Base, engine, get_db_session
from core.logging import get_logger
from core.memory.interface import IEngineeringMemoryEngine
from core.memory.compaction import MemoryCompactionManager

logger = get_logger("EngineeringMemoryEngine")


class DBEngineeringMemory(Base):
    """
    SQLAlchemy table persisting episodic software engineering memories.
    """

    __tablename__ = "engineering_memories"

    memory_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), nullable=False)
    step_id = Column(Integer, nullable=False)
    file_path = Column(String(255), nullable=False)
    error_msg = Column(Text, nullable=False)  # Compacted traceback representation
    applied_fix = Column(Text, nullable=False)
    timestamp = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )


class DBEngineeringConvention(Base):
    """
    SQLAlchemy table persisting software engineering conventions/standards.
    """

    __tablename__ = "engineering_conventions"

    convention_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=True)  # Optional target file path/pattern
    convention_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general")
    timestamp = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )


# Initialize database schema dynamically
Base.metadata.create_all(bind=engine)


class EngineeringMemoryEngine(IEngineeringMemoryEngine):
    """
    Persistent Engineering Memory Engine (EME) specialized for software engineering workflows.
    Utilizes hybrid search (Jaccard keyword matching + semantic vector embeddings)
    for both episodic bug-fix retrieval and convention enforcement.
    """

    def __init__(self) -> None:
        self.compactor = MemoryCompactionManager()

    def record_fix(
        self,
        task_id: str,
        step_id: int,
        file_path: str,
        error_msg: str,
        applied_fix: str,
    ) -> None:
        """
        Records a successful debug/repair session in the persistent episodic ledger and local vector DB.
        """
        compacted_msg = self.compactor.compact_log(error_msg)

        with get_db_session() as session:
            memory = DBEngineeringMemory(
                task_id=task_id,
                step_id=step_id,
                file_path=file_path,
                error_msg=compacted_msg,
                applied_fix=applied_fix,
            )
            session.add(memory)
            session.flush()  # Populate memory_id before committing
            memory_id = memory.memory_id

        # Async-safe dynamic import to prevent circular import issues
        try:
            from core.memory import VectorMemoryIndex

            vector_index = VectorMemoryIndex("eme_fixes_index")
            vector_index.add_memory(
                text=compacted_msg,
                metadata={
                    "memory_id": memory_id,
                    "task_id": task_id,
                    "step_id": step_id,
                    "file_path": file_path,
                    "applied_fix": applied_fix,
                },
            )
        except Exception as e:
            logger.warning(
                f"Could not index fix semantically in VectorMemoryIndex: {e}"
            )

        logger.info(
            f"Recorded engineering fix memory in EME database for file {file_path}"
        )

    def retrieve_similar_fixes(
        self, error_msg: str, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Queries EME to retrieve relevant past fixes using hybrid search (vector matching + Jaccard tokens).
        """
        compacted_query = self.compactor.compact_log(error_msg)
        query_tokens = self._tokenize(compacted_query)

        if not query_tokens:
            return []

        # Try semantic search via vector index
        vector_results = []
        try:
            from core.memory import VectorMemoryIndex

            vector_index = VectorMemoryIndex("eme_fixes_index")
            vector_results = vector_index.search(compacted_query, limit=limit * 2)
        except Exception as e:
            logger.warning(f"Could not search VectorMemoryIndex for fixes: {e}")

        with get_db_session() as session:
            records = session.query(DBEngineeringMemory).all()
            memory_list = [
                {
                    "memory_id": r.memory_id,
                    "file_path": r.file_path,
                    "error_msg": r.error_msg,
                    "applied_fix": r.applied_fix,
                }
                for r in records
            ]

        vector_scores = {
            item.metadata["memory_id"]: score
            for item, score in vector_results
            if "memory_id" in item.metadata
        }

        scored_records = []
        for mem in memory_list:
            mid = mem["memory_id"]
            stored_tokens = self._tokenize(mem["error_msg"])

            # Compute Jaccard overlap coefficient
            intersection = query_tokens.intersection(stored_tokens)
            union = query_tokens.union(stored_tokens)
            jaccard_score = len(intersection) / len(union) if union else 0.0

            # Get vector similarity score
            vector_score = vector_scores.get(mid, 0.0)

            # Compute hybrid score
            if vector_scores:
                hybrid_score = 0.4 * jaccard_score + 0.6 * vector_score
            else:
                hybrid_score = jaccard_score  # Fallback to pure Jaccard

            if (
                jaccard_score > 0.0
            ):  # Require some keyword/token overlap for software tracebacks
                scored_records.append((hybrid_score, mem))

        # Sort by overlap score descending
        scored_records.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, mem in scored_records[:limit]:
            results.append(
                {
                    "memory_id": mem["memory_id"],
                    "file_path": mem["file_path"],
                    "error_msg": mem["error_msg"],
                    "applied_fix": mem["applied_fix"],
                    "score": score,
                }
            )

        logger.info(f"EME query matched {len(results)} past fix profiles.")
        return results

    def record_convention(
        self,
        task_id: str,
        file_path: str,
        convention_name: str,
        description: str,
        category: str = "general",
    ) -> None:
        """
        Records a software engineering convention or styling policy in both DB and Vector DB.
        """
        with get_db_session() as session:
            convention = DBEngineeringConvention(
                task_id=task_id,
                file_path=file_path,
                convention_name=convention_name,
                description=description,
                category=category,
            )
            session.add(convention)
            session.flush()
            convention_id = convention.convention_id

        # Index in VectorMemoryIndex for semantic search
        try:
            from core.memory import VectorMemoryIndex

            vector_index = VectorMemoryIndex("eme_conventions_index")
            text_to_embed = f"Category: {category}\nConvention: {convention_name}\nDescription: {description}"
            vector_index.add_memory(
                text=text_to_embed,
                metadata={
                    "convention_id": convention_id,
                    "task_id": task_id,
                    "file_path": file_path,
                    "convention_name": convention_name,
                    "category": category,
                },
            )
        except Exception as e:
            logger.warning(
                f"Could not index convention semantically in VectorMemoryIndex: {e}"
            )

        logger.info(
            f"Recorded engineering convention '{convention_name}' in EME for path {file_path}"
        )

    def retrieve_similar_conventions(
        self, query: str, file_path: Optional[str] = None, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Queries EME to retrieve relevant conventions based on a file path or semantic query.
        """
        # Try semantic search via vector index
        vector_results = []
        try:
            from core.memory import VectorMemoryIndex

            vector_index = VectorMemoryIndex("eme_conventions_index")
            vector_results = vector_index.search(query, limit=limit * 2)
        except Exception as e:
            logger.warning(f"Could not search VectorMemoryIndex for conventions: {e}")

        # Fetch records from SQLite db for fallback and path-based Jaccard overlap
        with get_db_session() as session:
            records = session.query(DBEngineeringConvention).all()
            convention_list = [
                {
                    "convention_id": r.convention_id,
                    "task_id": r.task_id,
                    "file_path": r.file_path,
                    "convention_name": r.convention_name,
                    "description": r.description,
                    "category": r.category,
                }
                for r in records
            ]

        # Score candidates
        scored_candidates = []
        vector_scores = {
            item.metadata["convention_id"]: score
            for item, score in vector_results
            if "convention_id" in item.metadata
        }

        query_tokens = self._tokenize(query)

        for conv in convention_list:
            cid = conv["convention_id"]

            # 1. Semantic score from vector search
            vector_score = vector_scores.get(cid, 0.0)

            # 2. Text keyword match score (Jaccard) on convention content
            conv_text = (
                f"{conv['convention_name']} {conv['description']} {conv['category']}"
            )
            conv_tokens = self._tokenize(conv_text)
            text_score = 0.0
            if query_tokens and conv_tokens:
                intersection = query_tokens.intersection(conv_tokens)
                union = query_tokens.union(conv_tokens)
                text_score = len(intersection) / len(union) if union else 0.0

            # 3. Path-based matching bonus (engineering workflow specific)
            path_score = 0.0
            if file_path and conv["file_path"]:
                norm_fp = file_path.replace("\\", "/").lower()
                norm_conv_fp = conv["file_path"].replace("\\", "/").lower()
                if norm_conv_fp in norm_fp or norm_fp in norm_conv_fp:
                    path_score = 0.5
                else:
                    # Token overlap on file paths
                    fp_tokens = set(re.split(r"[/\\_.]", norm_fp))
                    conv_fp_tokens = set(re.split(r"[/\\_.]", norm_conv_fp))
                    fp_tokens = {t for t in fp_tokens if len(t) > 2}
                    conv_fp_tokens = {t for t in conv_fp_tokens if len(t) > 2}
                    if fp_tokens and conv_fp_tokens:
                        path_score = len(fp_tokens.intersection(conv_fp_tokens)) / len(
                            fp_tokens.union(conv_fp_tokens)
                        )

            # Combine scores with weighting
            if vector_scores:
                hybrid_score = 0.4 * vector_score + 0.3 * text_score + 0.3 * path_score
            else:
                hybrid_score = 0.5 * text_score + 0.5 * path_score  # Fallback

            if hybrid_score > 0.0:
                scored_candidates.append((hybrid_score, conv))

        # Sort by hybrid score descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, conv in scored_candidates[:limit]:
            results.append(
                {
                    "convention_id": conv["convention_id"],
                    "task_id": conv["task_id"],
                    "file_path": conv["file_path"],
                    "convention_name": conv["convention_name"],
                    "description": conv["description"],
                    "category": conv["category"],
                    "score": score,
                }
            )

        logger.info(f"EME query matched {len(results)} conventions.")
        return results

    def compact_memories(self) -> None:
        """
        Triggers memory compaction on all existing verbose logs.
        """
        with get_db_session() as session:
            records = session.query(DBEngineeringMemory).all()
            for r in records:
                if "\n" in r.error_msg:  # If contains newlines, it's verbose
                    r.error_msg = self.compactor.compact_log(r.error_msg)
        logger.info("Database memories compaction completed.")

    def _tokenize(self, text: str) -> set:
        """
        Splits string trace into relevant alphanumeric tokens (filtering out paths and line numbers).
        """
        # Strip paths and select standard identifiers and exception names
        words = re.findall(r"[a-zA-Z_]\w*", text)
        return {w.lower() for w in words if len(w) > 3}
