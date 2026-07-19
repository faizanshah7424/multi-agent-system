import json
import sqlite3
import hashlib
import time
import logging
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pathlib import Path

from config import settings
from core.schemas import RetrievedCodeChunk
from core.context.budget import DatabaseConfigurator
from core.context.reranker import IReranker
from core.storage.storage_adapter import IStorageAdapter, tenant_context

logger = logging.getLogger(__name__)


def get_current_tenant_id() -> str:
    """
    Returns the active tenant ID based on configuration and current context.
    """
    if settings.enable_multi_tenancy:
        return tenant_context.get()
    return settings.default_tenant_id


def get_db_connection() -> sqlite3.Connection:
    """
    Exposes a WAL-configured SQLite connection using database configurations.
    """
    db_path = settings.persist_path / "system.db"
    settings.persist_path.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    DatabaseConfigurator.configure_connection(conn, "sqlite")
    return conn


@runtime_checkable
class IRetrievalPolicy(Protocol):
    """
    Interface for context search and retrieval ranking algorithms.
    """

    def retrieve_chunks(
        self, chunks: List[RetrievedCodeChunk], query: str, limit: int
    ) -> List[RetrievedCodeChunk]:
        ...


class ExactMatchPolicy(IRetrievalPolicy):
    """
    Retrieval policy matching exact keywords or symbol strings.
    """

    def retrieve_chunks(
        self, chunks: List[RetrievedCodeChunk], query: str, limit: int
    ) -> List[RetrievedCodeChunk]:
        query_lower = query.lower().strip()
        matched = []
        for c in chunks:
            if query_lower in c.content.lower() or (
                c.symbol_name and query_lower in c.symbol_name.lower()
            ):
                score = (
                    1.0
                    if c.symbol_name and query_lower == c.symbol_name.lower()
                    else 0.8
                )
                matched.append(
                    RetrievedCodeChunk(
                        file_path=c.file_path,
                        content=c.content,
                        score=score,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        symbol_name=c.symbol_name,
                    )
                )
        matched.sort(key=lambda x: x.score, reverse=True)
        return matched[:limit]


class SemanticPolicy(IRetrievalPolicy):
    """
    Retrieval policy ranking chunks based on word match frequency.
    """

    def retrieve_chunks(
        self, chunks: List[RetrievedCodeChunk], query: str, limit: int
    ) -> List[RetrievedCodeChunk]:
        query_words = set(query.lower().split())
        matched = []
        for c in chunks:
            text_words = c.content.lower().split()
            if not query_words or not text_words:
                score = 0.0
            else:
                match_count = sum(1 for w in text_words if w in query_words)
                score = match_count / len(query_words)
            if score > 0.0:
                matched.append(
                    RetrievedCodeChunk(
                        file_path=c.file_path,
                        content=c.content,
                        score=score,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        symbol_name=c.symbol_name,
                    )
                )
        matched.sort(key=lambda x: x.score, reverse=True)
        return matched[:limit]


class HybridPolicy(IRetrievalPolicy):
    """
    Combines ExactMatch and Semantic policies with a merged score ranking.
    """

    def retrieve_chunks(
        self, chunks: List[RetrievedCodeChunk], query: str, limit: int
    ) -> List[RetrievedCodeChunk]:
        exact_results = ExactMatchPolicy().retrieve_chunks(
            chunks, query, len(chunks)
        )
        semantic_results = SemanticPolicy().retrieve_chunks(
            chunks, query, len(chunks)
        )

        merged: Dict[str, RetrievedCodeChunk] = {}
        for r in exact_results:
            key = f"{r.file_path}:{r.start_line}:{r.symbol_name}"
            merged[key] = r

        for r in semantic_results:
            key = f"{r.file_path}:{r.start_line}:{r.symbol_name}"
            if key in merged:
                merged[key] = RetrievedCodeChunk(
                    file_path=r.file_path,
                    content=r.content,
                    score=merged[key].score * 0.5 + r.score * 0.5,
                    start_line=r.start_line,
                    end_line=r.end_line,
                    symbol_name=r.symbol_name,
                )
            else:
                merged[key] = r

        results_list = list(merged.values())
        results_list.sort(key=lambda x: x.score, reverse=True)
        return results_list[:limit]


class RetrievalPipeline:
    """
    Retrieval workflow pipeline executing caching, indexing, and policy ranking.
    """

    def __init__(
        self,
        indexer: Optional[Any] = None,
        reranker: Optional[IReranker] = None,
        storage: Optional[IStorageAdapter] = None,
    ) -> None:
        if indexer is None:
            try:
                from core.di import DIContainer
                from core.context.indexer import TreeSitterIndexer
                indexer = DIContainer.get(TreeSitterIndexer)
            except Exception:
                from core.context.indexer import TreeSitterIndexer
                indexer = TreeSitterIndexer()
        self.indexer = indexer

        if reranker is None:
            try:
                from core.di import DIContainer
                from core.context.reranker import IReranker
                reranker = DIContainer.get(IReranker)
            except Exception:
                from core.context.cross_encoder_reranker import CrossEncoderReranker
                reranker = CrossEncoderReranker()
        self.reranker = reranker

        if storage is None:
            try:
                from core.di import DIContainer
                from core.storage.storage_adapter import IStorageAdapter
                storage = DIContainer.get(IStorageAdapter)
            except Exception:
                from core.storage.sqlite_adapter import SQLiteStorageAdapter
                storage = SQLiteStorageAdapter()
        self.storage = storage

        # Initialize schema lazily
        try:
            self.init_schema()
        except Exception as e:
            logger.warning(f"Could not initialize database schema: {e}")

    def init_schema(self) -> None:
        """
        Initializes database schema for the active storage backend.
        """
        self.storage.connect()
        is_postgres = (settings.database_backend == "postgres" or settings.database_backend == "postgresql")
        
        if not is_postgres:
            # SQLite check for symbols table
            self.storage.execute("PRAGMA table_info(retrieval_code_symbols)")
            columns = [row[1] for row in self.storage.fetchall()]
            if columns and ("language" not in columns or "tenant_id" not in columns):
                self.storage.execute("DROP TABLE retrieval_code_symbols")
                
            # SQLite check for cache table
            self.storage.execute("PRAGMA table_info(retrieval_cache)")
            cache_columns = [row[1] for row in self.storage.fetchall()]
            if cache_columns and "tenant_id" not in cache_columns:
                self.storage.execute("DROP TABLE retrieval_cache")
        else:
            # PostgreSQL check for symbols table
            try:
                self.storage.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'retrieval_code_symbols'"
                )
                columns = [row[0] for row in self.storage.fetchall()]
                if columns and ("language" not in columns or "tenant_id" not in columns):
                    self.storage.execute("DROP TABLE retrieval_code_symbols CASCADE")
            except Exception:
                pass
                
            # PostgreSQL check for cache table
            try:
                self.storage.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'retrieval_cache'"
                )
                cache_columns = [row[0] for row in self.storage.fetchall()]
                if cache_columns and "tenant_id" not in cache_columns:
                    self.storage.execute("DROP TABLE retrieval_cache CASCADE")
            except Exception:
                pass

        # Create multi-tenant tables
        self.storage.execute(
            """
            CREATE TABLE IF NOT EXISTS retrieval_code_symbols (
                tenant_id TEXT,
                task_id TEXT,
                file_path TEXT,
                symbol_name TEXT,
                symbol_type TEXT,
                start_line INTEGER,
                end_line INTEGER,
                content TEXT,
                checksum TEXT,
                language TEXT,
                kind TEXT,
                signature TEXT,
                parent TEXT,
                updated_at REAL,
                PRIMARY KEY (tenant_id, task_id, file_path, symbol_name)
            )
            """
        )

        self.storage.execute(
            """
            CREATE TABLE IF NOT EXISTS retrieval_cache (
                tenant_id TEXT,
                task_id TEXT,
                query TEXT,
                results TEXT,
                created_at REAL,
                PRIMARY KEY (tenant_id, task_id, query)
            )
            """
        )

        # Create indexes
        self.storage.execute("CREATE INDEX IF NOT EXISTS idx_retrieval_lang_name ON retrieval_code_symbols (language, symbol_name)")
        self.storage.execute("CREATE INDEX IF NOT EXISTS idx_retrieval_filepath ON retrieval_code_symbols (file_path)")
        self.storage.execute("CREATE INDEX IF NOT EXISTS idx_retrieval_kind ON retrieval_code_symbols (kind)")
        self.storage.execute("CREATE INDEX IF NOT EXISTS idx_retrieval_checksum ON retrieval_code_symbols (checksum)")
        self.storage.execute("CREATE INDEX IF NOT EXISTS idx_retrieval_tenant ON retrieval_code_symbols (tenant_id)")

    def retrieve(
        self, task_id: str, query: str, workspace_path: str
    ) -> List[RetrievedCodeChunk]:
        cached = self._get_cached_retrieval(task_id, query)
        if cached is not None:
            return cached

        # Intent Detection: check if query points directly to a single symbol keyword
        is_symbol_intent = False
        target_symbol = ""
        words = query.strip().split()
        if len(words) == 1:
            is_symbol_intent = True
            target_symbol = words[0]
        elif len(words) == 2 and words[0] in ("class", "def", "function"):
            is_symbol_intent = True
            target_symbol = words[1]

        chunks = []
        if is_symbol_intent:
            chunks = self._search_symbol_index(task_id, target_symbol)

        if not chunks:
            all_chunks = self._get_all_indexed_chunks(task_id)
            if not all_chunks:
                self.index_workspace(task_id, workspace_path)
                all_chunks = self._get_all_indexed_chunks(task_id)

            if all_chunks:
                policy = HybridPolicy()
                if settings.reranker_enabled:
                    # Retrieve a larger pool of candidates capped at candidate limit
                    candidate_limit = settings.rerank_top_k * 5
                    candidates = policy.retrieve_chunks(all_chunks, query, limit=candidate_limit)
                    chunks = self.reranker.rerank(query, candidates)
                else:
                    chunks = policy.retrieve_chunks(all_chunks, query, limit=5)

        self._cache_retrieval(task_id, query, chunks)
        return chunks

    def index_workspace(self, task_id: str, workspace_path: str) -> None:
        ws_dir = Path(workspace_path)
        if not ws_dir.exists():
            return

        import os
        skipped_dirs = {
            "venv",
            ".venv",
            ".git",
            ".pytest_cache",
            "__pycache__",
            "node_modules",
            "data",
            "dist",
            "build",
        }

        seen_files = set()
        tenant_id = get_current_tenant_id()

        self.storage.begin_transaction()
        try:
            for root, dirs, files in os.walk(str(ws_dir)):
                # Prune skipped directories in-place to prevent os.walk from entering them
                dirs[:] = [d for d in dirs if d not in skipped_dirs]

                for file in files:
                    suffix = os.path.splitext(file)[1]
                    if suffix in (
                        ".py",
                        ".js",
                        ".jsx",
                        ".ts",
                        ".tsx",
                        ".go",
                        ".java",
                    ):
                        file_path = os.path.join(root, file)
                        p = Path(file_path)
                        try:
                            rel_path = str(p.relative_to(ws_dir)).replace(
                                "\\", "/"
                            )
                            content = p.read_text(encoding="utf-8", errors="ignore")
                        except Exception:
                            continue

                        seen_files.add(rel_path)
                        checksum = hashlib.sha256(
                            content.encode("utf-8")
                        ).hexdigest()[:16]

                        # Check if file has same checksum
                        self.storage.execute(
                            "SELECT DISTINCT checksum FROM retrieval_code_symbols WHERE tenant_id = ? AND task_id = ? AND file_path = ?",
                            (tenant_id, task_id, rel_path),
                        )
                        row = self.storage.fetchone()
                        if row and row[0] == checksum:
                            continue

                        # Delete old symbols for this file
                        self.storage.execute(
                            "DELETE FROM retrieval_code_symbols WHERE tenant_id = ? AND task_id = ? AND file_path = ?",
                            (tenant_id, task_id, rel_path),
                        )

                        # Extract symbols using tree-sitter
                        symbols = self.indexer.extract_symbols(rel_path, content)
                        lines = content.splitlines()

                        for sym in symbols:
                            sym_content = "\n".join(
                                lines[sym.start_line - 1 : sym.end_line]
                            )
                            self.storage.execute(
                                """
                                INSERT INTO retrieval_code_symbols 
                                (tenant_id, task_id, file_path, symbol_name, symbol_type, start_line, end_line, content, checksum, language, kind, signature, parent, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT (tenant_id, task_id, file_path, symbol_name) DO UPDATE SET
                                    symbol_type = EXCLUDED.symbol_type,
                                    start_line = EXCLUDED.start_line,
                                    end_line = EXCLUDED.end_line,
                                    content = EXCLUDED.content,
                                    checksum = EXCLUDED.checksum,
                                    language = EXCLUDED.language,
                                    kind = EXCLUDED.kind,
                                    signature = EXCLUDED.signature,
                                    parent = EXCLUDED.parent,
                                    updated_at = EXCLUDED.updated_at
                                """,
                                (
                                    tenant_id,
                                    task_id,
                                    sym.filepath,
                                    sym.name,
                                    sym.kind,
                                    sym.start_line,
                                    sym.end_line,
                                    sym_content,
                                    sym.checksum,
                                    sym.language,
                                    sym.kind,
                                    sym.signature,
                                    sym.parent,
                                    time.time(),
                                ),
                            )

            # Delete removed symbols
            self.storage.execute(
                "SELECT DISTINCT file_path FROM retrieval_code_symbols WHERE tenant_id = ? AND task_id = ?",
                (tenant_id, task_id),
            )
            indexed_files = [r[0] for r in self.storage.fetchall()]
            for f in indexed_files:
                if f not in seen_files:
                    self.storage.execute(
                        "DELETE FROM retrieval_code_symbols WHERE tenant_id = ? AND task_id = ? AND file_path = ?",
                        (tenant_id, task_id, f),
                    )

            self.storage.commit()
        except Exception as e:
            self.storage.rollback()
            logger.warning(f"Failed to index workspace: {e}. Rolled back indexing transaction.")
            raise e

    def _get_cached_retrieval(
        self, task_id: str, query: str
    ) -> Optional[List[RetrievedCodeChunk]]:
        tenant_id = get_current_tenant_id()
        try:
            self.storage.execute(
                "SELECT results FROM retrieval_cache WHERE tenant_id = ? AND task_id = ? AND query = ?",
                (tenant_id, task_id, query),
            )
            row = self.storage.fetchone()
            if row:
                data = json.loads(row[0])
                return [RetrievedCodeChunk(**d) for d in data]
        except Exception as e:
            logger.warning(f"Error fetching from retrieval cache: {e}")
        return None

    def _cache_retrieval(
        self, task_id: str, query: str, chunks: List[RetrievedCodeChunk]
    ) -> None:
        tenant_id = get_current_tenant_id()
        data = json.dumps([c.model_dump() for c in chunks])
        try:
            self.storage.execute(
                """
                INSERT INTO retrieval_cache (tenant_id, task_id, query, results, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (tenant_id, task_id, query) DO UPDATE SET
                    results = EXCLUDED.results,
                    created_at = EXCLUDED.created_at
                """,
                (tenant_id, task_id, query, data, time.time()),
            )
        except Exception as e:
            logger.warning(f"Error writing to retrieval cache: {e}")

    def _search_symbol_index(
        self, task_id: str, symbol_name: str
    ) -> List[RetrievedCodeChunk]:
        tenant_id = get_current_tenant_id()
        try:
            self.storage.execute(
                """
                SELECT file_path, content, start_line, end_line, symbol_name 
                FROM retrieval_code_symbols 
                WHERE tenant_id = ? AND task_id = ? AND symbol_name = ?
                """,
                (tenant_id, task_id, symbol_name),
            )
            rows = self.storage.fetchall()
        except Exception as e:
            logger.warning(f"Error searching symbol index: {e}")
            rows = []

        chunks = []
        for r in rows:
            chunks.append(
                RetrievedCodeChunk(
                    file_path=r[0],
                    content=r[1],
                    score=1.0,
                    start_line=r[2],
                    end_line=r[3],
                    symbol_name=r[4],
                )
            )
        return chunks

    def _get_all_indexed_chunks(self, task_id: str) -> List[RetrievedCodeChunk]:
        tenant_id = get_current_tenant_id()
        try:
            self.storage.execute(
                """
                SELECT file_path, content, start_line, end_line, symbol_name 
                FROM retrieval_code_symbols 
                WHERE tenant_id = ? AND task_id = ?
                """,
                (tenant_id, task_id),
            )
            rows = self.storage.fetchall()
        except Exception as e:
            logger.warning(f"Error getting indexed chunks: {e}")
            rows = []

        chunks = []
        for r in rows:
            chunks.append(
                RetrievedCodeChunk(
                    file_path=r[0],
                    content=r[1],
                    score=0.0,
                    start_line=r[2],
                    end_line=r[3],
                    symbol_name=r[4],
                )
            )
        return chunks


def init_db() -> None:
    try:
        from core.di import DIContainer
        from core.storage.storage_adapter import IStorageAdapter
        storage = DIContainer.get(IStorageAdapter)
    except Exception:
        from core.storage.sqlite_adapter import SQLiteStorageAdapter
        storage = SQLiteStorageAdapter()

    pipeline = RetrievalPipeline(storage=storage)
    pipeline.init_schema()


try:
    init_db()
except Exception as e:
    logger.warning(f"Database initialization failed on import: {e}. Will retry on demand.")
