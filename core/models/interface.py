from typing import (
    Any,
    Dict,
    Iterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class ModelParameters(BaseModel):
    """
    Standard generation tuning parameters for LLMs.
    """

    temperature: float = Field(0.0, description="Sampling temperature.")
    max_tokens: int = Field(4096, description="Limit on generation length.")
    response_format: Optional[Dict[str, Any]] = Field(
        None, description="Optional structural validation schema specification."
    )
    timeout: Optional[float] = Field(
        30.0, description="Timeout in seconds for LLM request."
    )
    retries: int = Field(
        3, description="Number of retry attempts on network/API failure."
    )


@runtime_checkable
class IModelProvider(Protocol):
    """
    Provider-agnostic interface standardizing core LLM generation operations.
    """

    def generate(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> str:
        """
        Sends standard text generation queries.

        Args:
            prompt: User-facing prompt instruction.
            system_instruction: System instruction or persona parameters.
            params: Standard parameters configuration.

        Returns:
            The raw generated string response.
        """
        ...

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str,
        params: ModelParameters,
    ) -> T:
        """
        Sends generation queries and guarantees outcome compliance against a Pydantic schema.

        Args:
            prompt: User-facing prompt instruction.
            schema: Target Pydantic model type structure constraint.
            system_instruction: System instruction or persona parameters.
            params: Standard parameters configuration.

        Returns:
            An instantiated Pydantic model matching schema definition.
        """
        ...

    def generate_stream(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> Iterator[str]:
        """
        Streams back generation chunks string-by-string.
        """
        ...
