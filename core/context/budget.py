import time
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from core.schemas import (
    ContextBudgetConfig,
    ContextBudgetAllocation,
    ContextTelemetry,
    RetrievedCodeChunk,
)


@runtime_checkable
class ITokenizer(Protocol):
    """
    Extended capability interface for token counting and model capabilities.
    """

    def count_tokens(self, text: str) -> int:
        """Counts tokens for the target text block."""
        ...

    def model_name(self) -> str:
        """Returns the identifier of the LLM model."""
        ...

    def max_context_window(self) -> int:
        """Returns the maximum context tokens for the model."""
        ...

    def max_output_tokens(self) -> int:
        """Returns the maximum output tokens for the model."""
        ...

    def supports_tool_calling(self) -> bool:
        """Returns true if the model supports tool calling APIs."""
        ...

    def supports_reasoning(self) -> bool:
        """Returns true if the model is a reasoning model (e.g. o1/o3)."""
        ...

    def supports_multimodal(self) -> bool:
        """Returns true if the model supports vision/audio inputs."""
        ...


class TiktokenTokenizer(ITokenizer):
    """
    ITokenizer implementation wrapping OpenAI tiktoken.
    """

    def __init__(self, model: str = "gpt-4") -> None:
        self._model = model
        try:
            import tiktoken

            self._encoding = tiktoken.encoding_for_model(model)
        except Exception:
            try:
                import tiktoken

                self._encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self._encoding = None

    def count_tokens(self, text: str) -> int:
        if self._encoding:
            return len(self._encoding.encode(text, disallowed_special=()))
        return len(text) // 4

    def model_name(self) -> str:
        return self._model

    def max_context_window(self) -> int:
        if "gpt-4o" in self._model:
            return 128000
        elif "gpt-4" in self._model:
            return 8192
        return 128000

    def max_output_tokens(self) -> int:
        return 4096

    def supports_tool_calling(self) -> bool:
        return True

    def supports_reasoning(self) -> bool:
        return "o1" in self._model or "o3" in self._model

    def supports_multimodal(self) -> bool:
        return "vision" in self._model or "gpt-4o" in self._model


class GeminiTokenizer(ITokenizer):
    """
    ITokenizer implementation abstracting Google Gemini SentencePiece token metrics.
    """

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self._model = model

    def count_tokens(self, text: str) -> int:
        # Client-side proxy fallback calculation to prevent calling Google API endpoint directly
        return len(text) // 4

    def model_name(self) -> str:
        return self._model

    def max_context_window(self) -> int:
        if "gemini-2.5-pro" in self._model:
            return 2000000
        return 1000000

    def max_output_tokens(self) -> int:
        return 8192

    def supports_tool_calling(self) -> bool:
        return True

    def supports_reasoning(self) -> bool:
        return "thinking" in self._model

    def supports_multimodal(self) -> bool:
        return True


class TokenizerRegistry:
    """
    Registry that lazily instantiates ITokenizer implementations on-demand.
    """

    _instances: Dict[str, ITokenizer] = {}

    @classmethod
    def get_tokenizer(cls, model_name: str) -> ITokenizer:
        if model_name not in cls._instances:
            if "gemini" in model_name.lower():
                cls._instances[model_name] = GeminiTokenizer(model_name)
            else:
                cls._instances[model_name] = TiktokenTokenizer(model_name)
        return cls._instances[model_name]

    @classmethod
    def clear(cls) -> None:
        cls._instances.clear()


@runtime_checkable
class IBudgetStrategy(Protocol):
    """
    Interface for context token allocation strategies.
    """

    def allocate(
        self,
        config: ContextBudgetConfig,
        tokenizer: ITokenizer,
        history_original_tokens: int,
        history_compressed_tokens: int,
    ) -> ContextBudgetAllocation:
        ...


class BalancedBudgetStrategy(IBudgetStrategy):
    """
    Default balanced allocation strategy distributing tokens based on configured percentages.
    """

    def allocate(
        self,
        config: ContextBudgetConfig,
        tokenizer: ITokenizer,
        history_original_tokens: int,
        history_compressed_tokens: int,
    ) -> ContextBudgetAllocation:
        total = config.total_budget

        system_prompt = int(total * config.system_prompt_pct)
        reserved_response = int(total * config.reserved_response_pct)
        history = int(total * config.history_pct)
        file_focus = int(total * config.file_focus_pct)
        retrieved_chunks = int(total * config.retrieved_chunks_pct)
        tool_outputs = int(total * config.tool_outputs_pct)
        scratchpad = int(total * config.scratchpad_pct)

        allocated = (
            system_prompt
            + reserved_response
            + history
            + file_focus
            + retrieved_chunks
            + tool_outputs
            + scratchpad
        )
        remaining = total - allocated

        compression_ratio = 1.0
        if history_compressed_tokens > 0:
            compression_ratio = history_original_tokens / history_compressed_tokens

        telemetry = ContextTelemetry(
            model=tokenizer.model_name(),
            total_tokens=tokenizer.max_context_window(),
            allocated_tokens=allocated,
            remaining_tokens=remaining,
            compression_ratio=compression_ratio,
        )

        return ContextBudgetAllocation(
            system_prompt=system_prompt,
            reserved_response=reserved_response,
            history=history,
            file_focus=file_focus,
            retrieved_chunks=retrieved_chunks,
            tool_outputs=tool_outputs,
            scratchpad=scratchpad,
            total_allocated=allocated,
            telemetry=telemetry,
        )


class ContextBudgetManager:
    """
    Stateless manager for calculating allocations and executing history trimming.
    """

    @staticmethod
    def calculate_budget(
        config: ContextBudgetConfig,
        model_name: str,
        strategy: IBudgetStrategy,
        history_original_tokens: int = 0,
        history_compressed_tokens: int = 0,
    ) -> ContextBudgetAllocation:
        tokenizer = TokenizerRegistry.get_tokenizer(model_name)
        return strategy.allocate(
            config,
            tokenizer,
            history_original_tokens,
            history_compressed_tokens,
        )

    @staticmethod
    def compress_history(
        history_messages: List[Dict[str, str]], budget: int, model_name: str
    ) -> tuple[List[Dict[str, str]], int]:
        tokenizer = TokenizerRegistry.get_tokenizer(model_name)

        original_total_tokens = sum(
            tokenizer.count_tokens(msg.get("content", ""))
            for msg in history_messages
        )

        result = []
        current_tokens = 0
        for msg in reversed(history_messages):
            tokens = tokenizer.count_tokens(msg.get("content", ""))
            if current_tokens + tokens <= budget:
                result.insert(0, msg)
                current_tokens += tokens
            else:
                break

        return result, original_total_tokens


class ContextIsolationWrapper:
    """
    Wraps retrieved code chunks securely using configurable isolation tags.
    """

    @staticmethod
    def wrap_chunk(chunk: RetrievedCodeChunk) -> str:
        from config import settings

        start_tag = settings.context_isolation_start_tag
        end_tag = settings.context_isolation_end_tag

        if start_tag.endswith(">"):
            base_tag = start_tag[:-1]
            custom_start = f'{base_tag} file="{chunk.file_path}" lines="{chunk.start_line}-{chunk.end_line}">'
        else:
            custom_start = start_tag

        return f"{custom_start}\n{chunk.content}\n{end_tag}"


class DatabaseConfigurator:
    """
    Configures database connections for high concurrency and isolation settings.
    """

    @staticmethod
    def configure_connection(connection: Any, dialect_name: str) -> None:
        from config import settings

        if dialect_name == "sqlite":
            cursor = connection.cursor()
            try:
                if settings.sqlite_use_wal:
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute(
                    f"PRAGMA busy_timeout={settings.sqlite_busy_timeout}"
                )
                cursor.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            finally:
                cursor.close()
        elif dialect_name == "postgresql":
            pass
