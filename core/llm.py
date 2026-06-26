import os
from typing import Optional, Any, Dict, List
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings
from core.logging import get_logger

logger = get_logger("LLM")

# Initialize the Gemini GenAI Client using settings
api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY is not set in environment or settings. API calls may fail.")

client = genai.Client(api_key=api_key)

class GeminiWrapper:
    """
    Centralized Wrapper for Gemini API interactions.
    Provides robust retry mechanism, logging, and configuration management.
    """
    
    def __init__(self, default_model: Optional[str] = None):
        self.default_model = default_model or settings.default_model

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=2, min=4, max=45),
        retry=retry_if_exception_type(APIError),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"Gemini API call failed. Retrying... (Attempt {retry_state.attempt_number})"
        )
    )
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
        response_schema: Optional[Any] = None,
    ) -> str:
        """
        Generate content using Gemini model with retry logic.
        
        Args:
            prompt: User or task prompt to send.
            model: The Gemini model name override.
            system_instruction: Context/instruction to set the agent's behavior.
            temperature: Sampling temperature (0.0 to 2.0).
            json_mode: Whether to enforce JSON output.
            response_schema: Optional Pydantic model to enforce structured output schema natively.
            
        Returns:
            The generated response text.
        """
        target_model = model or self.default_model
        
        # Check LLM Cache first
        from core.cache import llm_cache
        import time
        schema_str = response_schema.__name__ if hasattr(response_schema, "__name__") else str(response_schema) if response_schema else None
        cached_res = llm_cache.get(prompt, system_instruction, target_model, schema_str)
        if cached_res is not None:
            logger.info(f"LLM prompt cache hit for: {prompt[:50]}...")
            return cached_res

        # Build generation configuration
        config_args = {}
        if system_instruction is not None:
            config_args["system_instruction"] = system_instruction
        if temperature is not None:
            config_args["temperature"] = temperature
        if response_schema is not None:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = response_schema
        elif json_mode:
            config_args["response_mime_type"] = "application/json"
            
        config = types.GenerateContentConfig(**config_args) if config_args else None
        
        try:
            logger.debug(f"Calling model '{target_model}' (JSON/Schema: {json_mode or (response_schema is not None)})...")
            start_time = time.time()
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config
            )
            execution_time_ms = (time.time() - start_time) * 1000
            
            if not response.text:
                logger.error("Received empty response from Gemini API.")
                raise ValueError("Empty response received from Gemini API.")
                
            # Extract usage metadata
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            if response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count or 0
                completion_tokens = response.usage_metadata.candidates_token_count or 0
                total_tokens = response.usage_metadata.total_token_count or 0
                
            # Log metrics to MetricsCollector
            try:
                from core.metrics import metrics_collector
                metrics_collector.record_llm_call(
                    model_name=target_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    execution_time_ms=execution_time_ms
                )
            except Exception as me:
                logger.debug(f"Failed to record LLM metrics: {str(me)}")

            # Save in cache
            llm_cache.set(
                prompt=prompt,
                system_instruction=system_instruction,
                model=target_model,
                value=response.text,
                schema=schema_str
            )
            
            return response.text
            
        except APIError as e:
            logger.error(f"Gemini API Error (status_code={e.code}): {e.message}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during Gemini generation: {str(e)}")
            raise e

    def generate_structured(
        self,
        prompt: str,
        response_schema: Any,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        retries: int = 1
    ) -> Any:
        """
        Generates content and validates it against a Pydantic model response_schema.
        If validation fails, retries up to `retries` times by appending error feedback.
        """
        target_model = model or self.default_model
        current_prompt = prompt
        
        for attempt in range(retries + 1):
            try:
                response_text = self.generate(
                    prompt=current_prompt,
                    model=target_model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    response_schema=response_schema
                )
                
                # Validate using Pydantic model methods
                if hasattr(response_schema, "model_validate_json"):
                    return response_schema.model_validate_json(response_text)
                else:
                    import json
                    return response_schema(**json.loads(response_text))
                    
            except Exception as e:
                logger.warning(
                    f"Structured output schema validation failed (Attempt {attempt+1}/{retries+1}) for {response_schema.__name__ if hasattr(response_schema, '__name__') else type(response_schema)}: {str(e)}"
                )
                if attempt < retries:
                    logger.info("Retrying structured generation with feedback...")
                    current_prompt = (
                        f"{prompt}\n\n"
                        f"[SYSTEM ALERT: Your previous response failed schema validation with error: {str(e)}]\n"
                        f"Please regenerate the response ensuring complete adherence to the specified JSON schema."
                    )
                else:
                    logger.error(f"Structured output generation permanently failed after {retries+1} attempts.")
                    raise e

# Package level singleton instance for global/backward compatibility usage
_global_wrapper = GeminiWrapper()

def ask_llm(
    prompt: str,
    model: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    json_mode: bool = False
) -> str:
    """
    Backward-compatible and simple entry point for LLM generation.
    """
    return _global_wrapper.generate(
        prompt=prompt,
        model=model,
        system_instruction=system_instruction,
        temperature=temperature,
        json_mode=json_mode
    )

def ask_llm_structured(
    prompt: str,
    response_schema: Any,
    model: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    retries: int = 1
) -> Any:
    """
    Generate content and validate it strictly against a Pydantic model response_schema.
    """
    return _global_wrapper.generate_structured(
        prompt=prompt,
        response_schema=response_schema,
        model=model,
        system_instruction=system_instruction,
        temperature=temperature,
        retries=retries
    )

def get_embedding(text: str, model: str = "text-embedding-004") -> List[float]:
    """
    Generate vector embeddings using the Gemini GenAI Client.
    """
    try:
        response = client.models.embed_content(
            model=model,
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.error(f"Failed to generate embedding via Gemini API: {str(e)}")
        raise e