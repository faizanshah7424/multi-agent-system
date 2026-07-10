import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class RepositoryContext(BaseModel):
    frameworks: List[str] = Field(default_factory=list)
    architecture: str = "Clean Hexagonal / Decoupled Multi-Agent design"
    coding_style: str = "Strict static type annotations, Pydantic V2 schemas"
    db_models: List[str] = Field(default_factory=list)
    api_endpoints: List[str] = Field(default_factory=list)
    reusable_components: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    frontend_pages: List[str] = Field(default_factory=list)
    tests: List[str] = Field(default_factory=list)

class RepositoryContextDetector:
    """
    Scans the repository structure, discovers databases, APIs, UIs, styles, and architectures.
    """
    def build_context(self, repo_path: str = ".") -> RepositoryContext:
        ctx = RepositoryContext()
        ctx.frameworks = ["FastAPI", "Next.js", "React"]

        for root, dirs, files in os.walk(repo_path):
            if any(p in root for p in ["venv", ".git", "node_modules", ".next", "__pycache__", "brain"]):
                continue
            for f in files:
                rel_path = os.path.join(root, f).replace("\\", "/")
                if f.endswith(".py"):
                    if "test_" in f:
                        ctx.tests.append(rel_path)
                    elif "routes" in f or "app.py" in f:
                        ctx.api_endpoints.append(rel_path)
                    elif "database" in f or "models" in f:
                        ctx.db_models.append(rel_path)
                    elif "workflow" in f or "worker" in f or "queue" in f:
                        ctx.services.append(rel_path)
                elif f.endswith(".tsx") or f.endswith(".ts"):
                    if "View" in f or "page" in f:
                        ctx.frontend_pages.append(rel_path)

        # Limits to keep it light
        ctx.tests = ctx.tests[:15]
        ctx.api_endpoints = ctx.api_endpoints[:10]
        ctx.db_models = ctx.db_models[:10]
        ctx.services = ctx.services[:10]
        ctx.frontend_pages = ctx.frontend_pages[:15]
        ctx.reusable_components = [
            "core/database.py", "core/logging.py",
            "core/auth/security.py", "core/auth/dependencies.py"
        ]

        return ctx
