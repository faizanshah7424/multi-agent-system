import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models.interface import IModelProvider, ModelParameters
from core.llm import client
from google.genai import types
from google.genai.errors import APIError
from config import settings

T = TypeVar("T", bound=BaseModel)


class ModelCapabilities(BaseModel):
    """
    Defines capabilities and context limits of a model.
    """

    model_name: str
    max_context_window: int = Field(
        1000000, description="Tokens limit of context window."
    )
    supports_structured_json: bool = Field(
        True, description="True if schema validation is native."
    )
    supports_streaming: bool = Field(
        True, description="True if stream chunks are supported."
    )
    input_cost_per_million: float = Field(
        0.0, description="Cost in USD per 1M input tokens."
    )
    output_cost_per_million: float = Field(
        0.0, description="Cost in USD per 1M output tokens."
    )


# Global list of callback hooks triggered on token usage tracking
on_usage_tracked: List[Callable[[str, int, int, float], None]] = []


def calculate_usd_cost(
    model_name: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Calculates USD cost based on token counts and settings model pricing."""
    pricing = settings.model_pricing.get(model_name, {"input": 0.0, "output": 0.0})
    input_cost = prompt_tokens * pricing.get("input", 0.0)
    output_cost = completion_tokens * pricing.get("output", 0.0)
    return input_cost + output_cost


class GeminiProvider(IModelProvider):
    """
    Concrete implementation of IModelProvider for Google Gemini models.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self.model_name = model_name

    def _execute_with_retry(self, fn: Callable[[], Any], retries: int) -> Any:
        delay = 1.0
        for attempt in range(retries + 1):
            try:
                return fn()
            except APIError as e:
                if attempt == retries:
                    raise e
                time.sleep(delay)
                delay *= 2.0
            except Exception as e:
                if attempt == retries:
                    raise e
                time.sleep(delay)
                delay *= 2.0

    def generate(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> str:
        # Build GenAI Config
        http_opts = {"timeout": params.timeout} if params.timeout else None
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=params.temperature,
            max_output_tokens=params.max_tokens,
            http_options=http_opts,
        )

        def call_api():
            return client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

        response = self._execute_with_retry(call_api, params.retries)

        # Track Tokens and Costs
        p_toks = (
            response.usage_metadata.prompt_token_count or 0
            if response.usage_metadata
            else 0
        )
        c_toks = (
            response.usage_metadata.candidates_token_count or 0
            if response.usage_metadata
            else 0
        )
        cost = calculate_usd_cost(self.model_name, p_toks, c_toks)

        # Trigger hooks
        for hook in on_usage_tracked:
            try:
                hook(self.model_name, p_toks, c_toks, cost)
            except Exception:
                pass

        return response.text or ""

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str,
        params: ModelParameters,
    ) -> T:
        http_opts = {"timeout": params.timeout} if params.timeout else None
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=params.temperature,
            max_output_tokens=params.max_tokens,
            response_mime_type="application/json",
            response_schema=schema,
            http_options=http_opts,
        )

        def call_api():
            return client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

        response = self._execute_with_retry(call_api, params.retries)

        # Track Tokens and Costs
        p_toks = (
            response.usage_metadata.prompt_token_count or 0
            if response.usage_metadata
            else 0
        )
        c_toks = (
            response.usage_metadata.candidates_token_count or 0
            if response.usage_metadata
            else 0
        )
        cost = calculate_usd_cost(self.model_name, p_toks, c_toks)

        for hook in on_usage_tracked:
            try:
                hook(self.model_name, p_toks, c_toks, cost)
            except Exception:
                pass

        text = response.text or "{}"
        if hasattr(schema, "model_validate_json"):
            return schema.model_validate_json(text)
        else:
            import json

            return schema(**json.loads(text))

    def generate_stream(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> Iterator[str]:
        http_opts = {"timeout": params.timeout} if params.timeout else None
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=params.temperature,
            max_output_tokens=params.max_tokens,
            http_options=http_opts,
        )

        response_stream = client.models.generate_content_stream(
            model=self.model_name, contents=prompt, config=config
        )

        for chunk in response_stream:
            yield chunk.text or ""


import urllib.request
import urllib.error
import json
import re
import os
from core.di import DIContainer
from core.security.secret_manager import SecretManager


def _post_http_request(
    url: str, headers: dict, data: dict, timeout: float = 30.0
) -> dict:
    req = urllib.request.Request(
        url=url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        raise RuntimeError(f"API Error {e.code}: {err_msg}")
    except Exception as e:
        raise RuntimeError(f"Connection failed: {e}")


class OpenAIProvider(IModelProvider):
    """
    Concrete implementation of IModelProvider for OpenAI GPT models.
    """

    def __init__(self, model_name: str = "gpt-4o") -> None:
        self.model_name = model_name

    def _get_api_key(self) -> str:
        try:
            return DIContainer.get(SecretManager).get_secret("OPENAI_API_KEY")
        except Exception:
            return os.getenv("OPENAI_API_KEY", "")

    def generate(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> str:
        api_key = self._get_api_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
        }
        res = _post_http_request(
            "https://api.openai.com/v1/chat/completions",
            headers,
            data,
            params.timeout or 30.0,
        )

        # Token and cost tracking
        usage = res.get("usage", {})
        p_toks = usage.get("prompt_tokens", 0)
        c_toks = usage.get("completion_tokens", 0)
        cost = calculate_usd_cost(self.model_name, p_toks, c_toks)
        for hook in on_usage_tracked:
            try:
                hook(self.model_name, p_toks, c_toks, cost)
            except Exception:
                pass

        return res["choices"][0]["message"]["content"] or ""

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str,
        params: ModelParameters,
    ) -> T:
        api_key = self._get_api_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
            "response_format": {"type": "json_object"},
        }
        res = _post_http_request(
            "https://api.openai.com/v1/chat/completions",
            headers,
            data,
            params.timeout or 30.0,
        )

        usage = res.get("usage", {})
        p_toks = usage.get("prompt_tokens", 0)
        c_toks = usage.get("completion_tokens", 0)
        cost = calculate_usd_cost(self.model_name, p_toks, c_toks)
        for hook in on_usage_tracked:
            try:
                hook(self.model_name, p_toks, c_toks, cost)
            except Exception:
                pass

        text = res["choices"][0]["message"]["content"] or "{}"
        if hasattr(schema, "model_validate_json"):
            return schema.model_validate_json(text)
        else:
            return schema(**json.loads(text))

    def generate_stream(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> Iterator[str]:
        res = self.generate(prompt, system_instruction, params)
        yield res


class AnthropicProvider(IModelProvider):
    """
    Concrete implementation of IModelProvider for Anthropic Claude models.
    """

    def __init__(self, model_name: str = "claude-3-5-sonnet") -> None:
        self.model_name = model_name

    def _get_api_key(self) -> str:
        try:
            return DIContainer.get(SecretManager).get_secret("ANTHROPIC_API_KEY")
        except Exception:
            return os.getenv("ANTHROPIC_API_KEY", "")

    def generate(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> str:
        api_key = self._get_api_key()
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "system": system_instruction,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": params.max_tokens,
            "temperature": params.temperature,
        }
        res = _post_http_request(
            "https://api.anthropic.com/v1/messages",
            headers,
            data,
            params.timeout or 30.0,
        )

        # Token and cost tracking
        usage = res.get("usage", {})
        p_toks = usage.get("input_tokens", 0)
        c_toks = usage.get("output_tokens", 0)
        cost = calculate_usd_cost(self.model_name, p_toks, c_toks)
        for hook in on_usage_tracked:
            try:
                hook(self.model_name, p_toks, c_toks, cost)
            except Exception:
                pass

        content_list = res.get("content", [])
        if content_list:
            return content_list[0].get("text", "")
        return ""

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str,
        params: ModelParameters,
    ) -> T:
        prompt_with_schema = f"{prompt}\n\nYou must return only a valid JSON object matching this schema definition (no markup, no markdown formatting): {schema.model_json_schema()}"
        res_text = self.generate(prompt_with_schema, system_instruction, params)
        clean_text = re.sub(r"```json\s*|```", "", res_text).strip()
        if hasattr(schema, "model_validate_json"):
            return schema.model_validate_json(clean_text)
        else:
            return schema(**json.loads(clean_text))

    def generate_stream(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> Iterator[str]:
        res = self.generate(prompt, system_instruction, params)
        yield res


class FailoverModelProvider(IModelProvider):
    """
    Model Provider wrapper enabling automatic retry policies and cascading failovers
    across multiple underlying model API platforms (Gemini -> OpenAI -> Anthropic).
    """

    def __init__(self, providers: List[IModelProvider]) -> None:
        self.providers = providers

    def generate(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> str:
        last_error = None
        for provider in self.providers:
            try:
                return provider.generate(prompt, system_instruction, params)
            except Exception as e:
                last_error = e
        raise last_error or RuntimeError("All failover model providers failed.")

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str,
        params: ModelParameters,
    ) -> T:
        last_error = None
        for provider in self.providers:
            try:
                return provider.generate_structured(
                    prompt, schema, system_instruction, params
                )
            except Exception as e:
                last_error = e
        raise last_error or RuntimeError(
            "All failover model providers failed structured generation."
        )

    def generate_stream(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> Iterator[str]:
        last_error = None
        for provider in self.providers:
            try:
                return provider.generate_stream(prompt, system_instruction, params)
            except Exception as e:
                last_error = e
        raise last_error or RuntimeError(
            "All failover model providers failed streaming generation."
        )


class ModelProviderRegistry:
    """
    Registry for model providers and capabilities metadata.
    """

    _providers: Dict[str, IModelProvider] = {}
    _capabilities: Dict[str, ModelCapabilities] = {}

    @classmethod
    def register(
        cls, name: str, provider: IModelProvider, capabilities: ModelCapabilities
    ) -> None:
        cls._providers[name] = provider
        cls._capabilities[name] = capabilities

    @classmethod
    def get_provider(cls, name: str) -> IModelProvider:
        if name not in cls._providers:
            raise KeyError(f"Provider '{name}' is not registered.")
        return cls._providers[name]

    @classmethod
    def get_capabilities(cls, name: str) -> ModelCapabilities:
        if name not in cls._capabilities:
            raise KeyError(f"Capabilities for provider '{name}' are not registered.")
        return cls._capabilities[name]

    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()
        cls._capabilities.clear()
