import re
from pathlib import Path
from typing import Dict, List, Set
from core.registry.interface import IPromptLibrary

class PromptLibrary(IPromptLibrary):
    """
    Concrete implementation of IPromptLibrary.
    Loads markdown prompt templates from disk, performs variable substitution,
    and validates parameter inputs.
    """
    def __init__(self, prompts_dir: str) -> None:
        self.prompts_dir = Path(prompts_dir).resolve()

    def get_prompt(self, name: str, variables: Dict[str, str]) -> str:
        """
        Loads the template file, validates variables, formats it, and returns the result.
        """
        # Resolve prompt file path, e.g. name = "planner/v1" -> planner/v1.md
        prompt_path = (self.prompts_dir / f"{name}.md").resolve()
        if not prompt_path.exists():
            # Try alternate flat filename style, e.g. planner_v1.md
            flat_name = name.replace("/", "_")
            prompt_path = (self.prompts_dir / f"{flat_name}.md").resolve()
            
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template '{name}' not found under: {self.prompts_dir}")

        template = prompt_path.read_text(encoding="utf-8", errors="replace")
        
        # Validate that all required variables are supplied
        required_vars = self.extract_placeholders(template)
        missing_vars = required_vars - set(variables.keys())
        if missing_vars:
            raise ValueError(
                f"Missing required variables for prompt '{name}': {', '.join(missing_vars)}"
            )

        # Substitute variables
        formatted = template
        for key, val in variables.items():
            formatted = formatted.replace(f"{{{{{key}}}}}", val)
            
        return formatted

    def extract_placeholders(self, template: str) -> Set[str]:
        """
        Regex to find all {{placeholder}} occurrences in template text.
        """
        pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
        return set(pattern.findall(template))
