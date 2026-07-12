import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from core.registry.interface import ISkillRegistry


class SkillRegistry(ISkillRegistry):
    """
    Concrete implementation of ISkillRegistry.
    Loads and indexes markdown procedural guidelines from disk, parsing frontmatter version/category.
    """

    def __init__(self) -> None:
        # Maps skill name to absolute file path
        self._skills: Dict[str, str] = {}
        # Maps skill name to metadata dict (version, category, description)
        self._metadata: Dict[str, Dict[str, str]] = {}

    def register_skill(self, name: str, skill_markdown_path: str) -> None:
        """
        Reads and registers a skill markdown document, indexing its frontmatter tags.
        """
        path = Path(skill_markdown_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Skill markdown file not found at: {path}")

        content = path.read_text(encoding="utf-8", errors="replace")
        meta = self._parse_frontmatter(content)

        # Override name if specified in frontmatter
        skill_name = meta.get("name") or name

        self._skills[skill_name] = str(path)
        self._metadata[skill_name] = {
            "version": meta.get("version", "1.0.0"),
            "category": meta.get("category", "general"),
            "description": meta.get("description", ""),
        }

    def get_skill_instructions(self, name: str) -> str:
        """
        Reads the markdown content of a skill.
        """
        if name not in self._skills:
            raise KeyError(f"Skill '{name}' is not registered.")

        path = Path(self._skills[name])
        return path.read_text(encoding="utf-8", errors="replace")

    def get_skill_metadata(self, name: str) -> Optional[Dict[str, str]]:
        """Retrieves category, version, and details of a skill."""
        return self._metadata.get(name)

    def list_skills(self) -> List[str]:
        """Lists all registered skill names."""
        return list(self._skills.keys())

    def get_skills_by_category(self, category: str) -> List[str]:
        """Filters registered skill names by category."""
        return [
            name
            for name, meta in self._metadata.items()
            if meta["category"] == category
        ]

    def _parse_frontmatter(self, content: str) -> Dict[str, str]:
        meta = {}
        # Match leading --- YAML block
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            lines = match.group(1).splitlines()
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip('"').strip("'")
        return meta
