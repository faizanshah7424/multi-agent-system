from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Usage(BaseModel):
    """
    Tracks token counts for the session.
    """
    prompt_tokens: int = Field(0, description="Tokens consumed by input.")
    completion_tokens: int = Field(0, description="Tokens consumed by output.")
    total_tokens: int = Field(0, description="Total tokens used.")

class Cost(BaseModel):
    """
    Tracks estimated financial costs in USD.
    """
    input_cost_usd: float = Field(0.0, description="Input cost.")
    output_cost_usd: float = Field(0.0, description="Output cost.")
    total_cost_usd: float = Field(0.0, description="Total USD cost.")

class ToolCall(BaseModel):
    """
    Describes an LLM tool call invocation.
    """
    call_id: str = Field(..., description="Unique call ID.")
    name: str = Field(..., description="Tool name.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Input arguments.")

class ToolResult(BaseModel):
    """
    Captures the execution output of a tool call.
    """
    call_id: str = Field(..., description="Unique call ID.")
    output: str = Field(..., description="Execution outcome text.")
    is_error: bool = Field(False, description="True if execution threw an exception.")

class Message(BaseModel):
    """
    Represents a single message in the conversation.
    """
    role: str = Field(..., description="Role: system, user, assistant, or tool.")
    content: str = Field("", description="Message content.")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Optional tool calls.")
    tool_results: Optional[List[ToolResult]] = Field(None, description="Optional tool execution results.")

class SessionMetadata(BaseModel):
    """
    Metadata describing the session parameters.
    """
    session_id: str = Field(..., description="Unique session UUID.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp.")
    model_name: str = Field(..., description="LLM name used.")
    provider_name: str = Field(..., description="Provider name (e.g., Gemini).")
    temperature: float = Field(0.0, description="Sampling temperature.")
    max_tokens: int = Field(4096, description="Max generated tokens.")

class Conversation(BaseModel):
    """
    Standard communication protocol encapsulating an LLM chat session.
    """
    session_id: str = Field(..., description="Unique session ID.")
    messages: List[Message] = Field(default_factory=list, description="Ordered conversation messages.")
    metadata: SessionMetadata = Field(..., description="Session metadata context.")
    total_usage: Usage = Field(default_factory=Usage, description="Aggregate token usage.")
    total_cost: Cost = Field(default_factory=Cost, description="Aggregate financial cost.")
