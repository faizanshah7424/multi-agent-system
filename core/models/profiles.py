import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class AgentProfile(BaseModel):
    """
    Configuration-driven schema representing an agent's permissions,
    allowed tools, prompt guidelines, and tuning settings.
    """
    role: str = Field(..., description="Agent role name.")
    permissions: List[str] = Field(default_factory=list, description="Actions permitted: read_only, write, admin.")
    allowed_tools: List[str] = Field(default_factory=list, description="Explicit tools this agent can execute.")
    prompt_template_name: str = Field(..., description="Target name within PromptLibrary.")
    model: str = Field(..., description="Target LLM model name.")
    temperature: float = Field(0.0, description="LLM generation temperature.")
    max_tokens: int = Field(4096, description="LLM max output tokens limit.")

class AgentProfileRegistry:
    """
    Loads agent profiles from config file on disk and manages their definitions.
    """
    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path:
            self.config_path = Path(config_path).resolve()
        else:
            self.config_path = Path(__file__).parent.parent / "config" / "agent_profiles.json"
            
        self._profiles: Dict[str, AgentProfile] = {}
        self.load_profiles()

    def load_profiles(self) -> None:
        """
        Loads and parses profile JSON files.
        """
        if not self.config_path.exists():
            # If not exists, fall back to defaults
            return
            
        try:
            content = self.config_path.read_text(encoding="utf-8")
            data = json.loads(content)
            for key, val in data.items():
                self._profiles[key] = AgentProfile(**val)
        except Exception as e:
            # Raise configuration formatting errors
            raise ValueError(f"Failed to load agent profiles config: {str(e)}")

    def get_profile(self, key: str) -> AgentProfile:
        """Retrieves profile configuration by agent key."""
        if key not in self._profiles:
            raise KeyError(f"Agent profile '{key}' not found in configuration.")
        return self._profiles[key]

    def list_profiles(self) -> List[str]:
        """Lists all registered profile keys."""
        return list(self._profiles.keys())
