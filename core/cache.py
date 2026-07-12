import hashlib
import json
import time
import threading
from typing import Any, Dict, Optional
from core.logging import get_logger

logger = get_logger("CacheSystem")


class CacheEntry:
    """
    Individual cache cell carrying value, creation time, and time-to-live.
    """

    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class LLMCache:
    """
    In-memory prompt hash cache for Gemini API requests.
    Optimizes performance and reduces token consumption costs.
    """

    def __init__(self, default_ttl: Optional[float] = 300.0):
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

        # Metrics
        self.hits = 0
        self.misses = 0

    def _hash_key(
        self,
        prompt: str,
        system_instruction: Optional[str],
        model: str,
        schema: Optional[str] = None,
    ) -> str:
        data = f"{prompt}||{system_instruction or ''}||{model}||{schema or ''}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def get(
        self,
        prompt: str,
        system_instruction: Optional[str],
        model: str,
        schema: Optional[str] = None,
    ) -> Optional[str]:
        key = self._hash_key(prompt, system_instruction, model, schema)
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                if entry.is_expired():
                    del self._cache[key]
                    self.misses += 1
                    return None
                self.hits += 1
                return entry.value
            self.misses += 1
            return None

    def set(
        self,
        prompt: str,
        system_instruction: Optional[str],
        model: str,
        value: str,
        schema: Optional[str] = None,
        ttl: Optional[float] = None,
    ) -> None:
        key = self._hash_key(prompt, system_instruction, model, schema)
        target_ttl = ttl if ttl is not None else self.default_ttl
        entry = CacheEntry(value, target_ttl)
        with self._lock:
            self._cache[key] = entry

    def invalidate(self) -> None:
        with self._lock:
            self._cache.clear()
            logger.info("LLM prompt cache invalidated.")

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "size": len(self._cache),
            }


class ToolCache:
    """
    In-memory caching system for tool executions (specifically file reads,
    directory scans, and web search results). Tracks hit/miss and latency reductions.
    """

    def __init__(self, default_ttl: Optional[float] = 60.0):
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

        # Metrics
        self.hits = 0
        self.misses = 0
        self.latency_saved_ms = 0.0

    def _hash_key(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        # Sort arguments keys for consistent JSON stringification
        args_str = json.dumps(arguments, sort_keys=True)
        data = f"{tool_name}||{args_str}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def get(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        # Only cache read-only tools to avoid state out-of-sync
        if tool_name not in (
            "file_reader",
            "dir_scanner",
            "web_search",
            "memory_recall",
        ):
            return None

        key = self._hash_key(tool_name, arguments)
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                if entry.is_expired():
                    del self._cache[key]
                    self.misses += 1
                    return None
                self.hits += 1
                return entry.value
            self.misses += 1
            return None

    def set(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        if tool_name not in (
            "file_reader",
            "dir_scanner",
            "web_search",
            "memory_recall",
        ):
            return

        key = self._hash_key(tool_name, arguments)
        target_ttl = ttl if ttl is not None else self.default_ttl
        entry = CacheEntry(value, target_ttl)
        with self._lock:
            self._cache[key] = entry

    def record_latency_saved(self, latency_ms: float) -> None:
        with self._lock:
            self.latency_saved_ms += latency_ms

    def invalidate(self) -> None:
        with self._lock:
            self._cache.clear()
            logger.info("Tool cache invalidated.")

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "latency_saved_ms": self.latency_saved_ms,
                "size": len(self._cache),
            }


# Instantiated singletons
llm_cache = LLMCache()
tool_cache = ToolCache()
