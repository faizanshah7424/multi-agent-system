import logging
import math
import time
from typing import List, Dict, Any, Optional

from config import settings
from core.schemas import RetrievedCodeChunk
from core.context.reranker import IReranker

logger = logging.getLogger(__name__)


class CrossEncoderReranker(IReranker):
    """
    Production-ready Cross-Encoder reranking engine that optimizes retrieval relevance.
    Implements lazy model loading, telemetry instrumentation, sigmoid normalization,
    and robust error fallback handling.
    """

    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._model_load_time: float = 0.0
        self._is_healthy: bool = True
        self.telemetry_history: List[Dict[str, Any]] = []

    def _sigmoid(self, x: float) -> float:
        """
        Numerically stable sigmoid function to normalize logits to [0.0, 1.0].
        """
        if x >= 0:
            z = math.exp(-x)
            return 1.0 / (1.0 + z)
        else:
            z = math.exp(x)
            return z / (1.0 + z)

    def _load_model(self) -> None:
        """
        Loads the Cross-Encoder model. Only called on-demand to support lazy loading.
        """
        if self._model is not None:
            return

        start_time = time.time()
        try:
            # Lazy import to ensure no heavy modules are loaded on startup
            from sentence_transformers import CrossEncoder

            device = settings.rerank_device
            model_name = settings.reranker_model

            logger.info(
                f"Loading Cross-Encoder model '{model_name}' on device '{device}'..."
            )
            self._model = CrossEncoder(model_name, device=device)
            self._model_load_time = time.time() - start_time
            self._is_healthy = True
            logger.info(
                f"Cross-Encoder model '{model_name}' loaded successfully in {self._model_load_time:.4f}s."
            )
        except Exception as e:
            self._model_load_time = time.time() - start_time
            self._is_healthy = False
            logger.warning(
                f"Failed to load Cross-Encoder model. Error: {e}. Graceful bypass activated."
            )
            raise e

    def rerank(
        self, query: str, chunks: List[RetrievedCodeChunk]
    ) -> List[RetrievedCodeChunk]:
        """
        Semantic reranking of retrieval candidates.
        """
        if not settings.reranker_enabled:
            return chunks

        if not chunks:
            return chunks

        # Limit the candidate pool to prevent latency explosion
        candidate_limit = settings.rerank_top_k * 5
        candidates_to_process = chunks[:candidate_limit]
        candidate_count = len(candidates_to_process)

        start_time = time.time()
        try:
            self._load_model()
            if not self._is_healthy or self._model is None:
                logger.warning(
                    "Cross-Encoder model is not available. Bypassing reranking."
                )
                return chunks

            # Construct query-chunk text pairs for batch inference
            pairs = [[query, chunk.content] for chunk in candidates_to_process]
            batch_size = settings.rerank_batch_size

            # Perform batched inference
            scores = self._model.predict(
                pairs, batch_size=batch_size, show_progress_bar=False
            )

            reranked_chunks = []
            total_confidence = 0.0

            for idx, score in enumerate(scores):
                normalized_score = self._sigmoid(float(score))
                total_confidence += normalized_score

                chunk = candidates_to_process[idx]
                updated_chunk = RetrievedCodeChunk(
                    file_path=chunk.file_path,
                    content=chunk.content,
                    score=normalized_score,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    symbol_name=chunk.symbol_name,
                )
                reranked_chunks.append(updated_chunk)

            # Sort candidate list using normalized confidence scores
            reranked_chunks.sort(key=lambda x: x.score, reverse=True)

            # Apply relevance threshold filter
            threshold = settings.rerank_score_threshold
            filtered_chunks = [
                c for c in reranked_chunks if c.score >= threshold
            ]
            filtered_count = len(reranked_chunks) - len(filtered_chunks)

            # Apply top-k cap selection
            top_k_chunks = filtered_chunks[: settings.rerank_top_k]

            rerank_latency = time.time() - start_time
            avg_confidence = (
                (total_confidence / candidate_count) if candidate_count > 0 else 0.0
            )

            # Record telemetry metadata
            telemetry = {
                "model_load_time": self._model_load_time,
                "rerank_latency": rerank_latency,
                "batch_size": batch_size,
                "candidate_count": candidate_count,
                "filtered_count": filtered_count,
                "average_confidence": avg_confidence,
            }
            self.telemetry_history.append(telemetry)

            logger.info(
                f"Reranking completed in {rerank_latency:.4f}s | "
                f"Candidates: {candidate_count} -> Top-K: {len(top_k_chunks)} | "
                f"Filtered: {filtered_count} | Avg Confidence: {avg_confidence:.4f}"
            )

            return top_k_chunks

        except Exception as e:
            rerank_latency = time.time() - start_time
            logger.warning(
                f"Reranker encountered error: {e}. Gracefully reverting to original candidates."
            )

            # Record error telemetry
            telemetry = {
                "model_load_time": self._model_load_time,
                "rerank_latency": rerank_latency,
                "batch_size": settings.rerank_batch_size,
                "candidate_count": candidate_count,
                "filtered_count": 0,
                "average_confidence": 0.0,
                "error": str(e),
            }
            self.telemetry_history.append(telemetry)
            return chunks

    def health_check(self) -> bool:
        """
        Check health status of reranker.
        """
        if not settings.reranker_enabled:
            return False
        return self._is_healthy
