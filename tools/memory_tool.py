from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from tools.base import BaseTool
from core.memory import VectorMemoryIndex

class MemoryRecallArgs(BaseModel):
    query: str = Field(..., description="The semantic query search term (e.g. 'How did we fix the FastAPI validation?')")
    limit: int = Field(default=3, description="Maximum number of historical memory snippets to return.")

class MemoryRecallTool(BaseTool):
    name: str = "memory_recall"
    description: str = (
        "Query the semantic long-term memory vector index for past decisions, "
        "reusable code implementations, styling rules, or error resolutions."
    )
    args_schema: Type[BaseModel] = MemoryRecallArgs

    def execute(self, query: str, limit: int = 3) -> str:
        try:
            index = VectorMemoryIndex()
            results = index.search(query, limit=limit)
            if not results:
                return "No matching semantic memories were found in the long-term history index."
            
            output = []
            for idx, (item, similarity) in enumerate(results):
                output.append(
                    f"Memory #{idx+1} (Similarity: {similarity:.4f}, Saved: {item.timestamp})\n"
                    f"Content:\n{item.text}\n"
                    f"Metadata: {item.metadata}\n"
                    f"---"
                )
            return "\n\n".join(output)
        except Exception as e:
            return f"Error executing memory recall: {str(e)}"

class MemoryStoreArgs(BaseModel):
    text: str = Field(..., description="The learning, code snippet, styling rule, or observation text to store.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata key-value tags.")

class MemoryStoreTool(BaseTool):
    name: str = "memory_store"
    description: str = (
        "Directly saves a learning or observation text to the semantic long-term memory vector index."
    )
    args_schema: Type[BaseModel] = MemoryStoreArgs

    def execute(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        try:
            index = VectorMemoryIndex()
            index.add_memory(text, metadata=metadata)
            return "Observation successfully persisted to semantic vector index."
        except Exception as e:
            return f"Error executing memory store: {str(e)}"
