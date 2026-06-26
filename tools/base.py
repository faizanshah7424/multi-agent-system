from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel, Field

class BaseTool(ABC):
    """
    Abstract base class for all tools in the system.
    Follows the Command and Strategy patterns to provide a unified tool execution interface.
    """
    name: str = Field(..., description="The name of the tool, used by the model for tool-calling.")
    description: str = Field(..., description="A detailed description of what the tool does and when it should be used.")
    args_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool action with the provided inputs.
        
        Args:
            **kwargs: Inputs matching the args_schema of the tool.
            
        Returns:
            The execution result (typically a string or serializable structure).
        """
        pass

    def run(self, **kwargs: Any) -> Any:
        """
        Wrapper around execute to provide validation, caching, and metrics logging.
        """
        import time
        from core.cache import tool_cache
        
        # Check cache (only applies to read-only actions: file reads, scans, searches, memory queries)
        start_time = time.time()
        cached_val = tool_cache.get(self.name, kwargs)
        if cached_val is not None:
            # Latency saved estimations
            estimated_latency_ms = 350.0 if self.name == "web_search" else 50.0
            tool_cache.record_latency_saved(estimated_latency_ms)
            
            try:
                from core.metrics import metrics_collector
                metrics_collector.record_tool_run()
            except Exception:
                pass
            return cached_val
            
        # Record run
        try:
            from core.metrics import metrics_collector
            metrics_collector.record_tool_run()
        except Exception:
            pass

        # Execute core tool
        if self.args_schema:
            try:
                # Validate input arguments against Pydantic schema
                validated_args = self.args_schema(**kwargs)
                result = self.execute(**validated_args.model_dump())
            except Exception as e:
                return f"Error: Invalid arguments for tool '{self.name}': {str(e)}"
        else:
            try:
                result = self.execute(**kwargs)
            except Exception as e:
                return f"Error executing tool '{self.name}': {str(e)}"
                
        # Cache successful results (exclude error messages)
        if "error" not in str(result).lower():
            tool_cache.set(self.name, kwargs, result)
            
        return result

def validate_safe_path(target_path_str: str) -> Path:
    """
    Validates that a path is safe to access:
    1. Prevents path traversal (e.g. use of '..').
    2. Confines the path to the workspace root or allowed directories.
    3. Resolves symlinks and ensures they do not point outside.
    
    Raises ValueError if path is invalid or unsafe.
    """
    import os
    import string
    from pathlib import Path
    from config import settings
    
    # 1. Null byte and control character checks
    if not target_path_str or "\x00" in target_path_str:
        raise ValueError("Access Denied: Path contains null bytes or is empty.")
        
    # Check for non-printable control characters
    if any(c in target_path_str for c in (chr(i) for i in range(32) if i not in (9, 10, 13))):
        raise ValueError("Access Denied: Path contains illegal control characters.")

    workspace_root = Path(__file__).parent.parent.resolve()
    persist_root = settings.persist_path.resolve()
    app_data_root = (Path.home() / ".gemini" / "antigravity-cli").resolve()
    
    allowed_roots = [
        workspace_root,
        persist_root,
        persist_root.parent,
        app_data_root
    ]
    
    # Resolve absolute path to handle symlinks and relative elements
    try:
        # Use strict=False to resolve non-existing paths (e.g. for FileWriterTool)
        target = Path(target_path_str)
        if not target.is_absolute():
            target = (workspace_root / target).resolve(strict=False)
        else:
            target = target.resolve(strict=False)
    except Exception as e:
        # Fallback to abspath if resolve fails
        try:
            target = Path(os.path.abspath(target_path_str))
        except Exception:
            raise ValueError(f"Access Denied: Path '{target_path_str}' could not be resolved safely.")

    is_allowed = False
    for root in allowed_roots:
        resolved_root = root.resolve()
        try:
            # Check using relative_to (Pydantic / pathlib native)
            target.relative_to(resolved_root)
            is_allowed = True
            break
        except ValueError:
            # Fallback to part-by-part case-insensitive check (handles Windows case normalizations)
            try:
                target_parts = [p.lower() for p in target.parts]
                root_parts = [p.lower() for p in resolved_root.parts]
                if len(target_parts) >= len(root_parts) and target_parts[:len(root_parts)] == root_parts:
                    is_allowed = True
                    break
            except Exception:
                pass
            
    if not is_allowed:
        raise ValueError(
            f"Access Denied: Path '{target_path_str}' resolves to '{target}', "
            f"which is outside the allowed directories."
        )
        
    return target
