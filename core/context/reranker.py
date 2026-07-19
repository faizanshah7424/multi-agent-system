from typing import List, Protocol, runtime_checkable
from core.schemas import RetrievedCodeChunk


@runtime_checkable
class IReranker(Protocol):
    """
    Interface for context search and retrieval semantic reranker.
    """

    def rerank(
        self, query: str, chunks: List[RetrievedCodeChunk]
    ) -> List[RetrievedCodeChunk]:
        """
        Reranks retrieved code chunks based on semantic relevance to the query.

        Args:
            query: The search query.
            chunks: A list of candidate RetrievedCodeChunk instances.

        Returns:
            A list of reranked and filtered RetrievedCodeChunk instances.
        """
        ...

    def health_check(self) -> bool:
        """
        Performs a health check on the reranker.

        Returns:
            True if the reranker is operational, False otherwise.
        """
        ...
