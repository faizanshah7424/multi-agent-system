import os
from pathlib import Path
from typing import Dict, List, Set, Any

class RepositoryScanner:
    """
    Crawls codebases to map files, directories, configuration files,
    programming languages, and read-only Git metadata.
    """
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        # Exclude directories that are dependency caches or internal toolings
        self.ignored_dirs = {
            ".git", "node_modules", "venv", ".venv", "__pycache__", 
            ".next", ".pytest_cache", ".ruff_cache", "brain", "dist", "build"
        }

    def scan(self) -> Dict[str, Any]:
        file_paths: List[str] = []
        languages: Dict[str, int] = {}
        configs: List[str] = []
        total_size = 0

        for root, dirs, files in os.walk(self.repo_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(self.repo_path)).replace("\\", "/")
                file_paths.append(rel_path)
                
                # Update file size
                try:
                    total_size += full_path.stat().st_size
                except Exception:
                    pass
                
                # Language detection via file suffix
                suffix = full_path.suffix.lower()
                if suffix:
                    lang = self._suffix_to_lang(suffix)
                    if lang:
                        languages[lang] = languages.get(lang, 0) + 1
                        
                # Capture configuration files
                if file in (
                    "package.json", "requirements.txt", "pyproject.toml", 
                    "docker-compose.yml", "Dockerfile", "tsconfig.json", 
                    "tailwind.config.js", "schema.prisma", "alembic.ini",
                    "setup.py", "Pipfile", "webpack.config.js"
                ):
                    configs.append(rel_path)

        git_meta = self._read_git_metadata()

        return {
            "file_paths": file_paths,
            "languages": languages,
            "config_files": configs,
            "total_size_bytes": total_size,
            "git_metadata": git_meta
        }

    def _suffix_to_lang(self, suffix: str) -> Optional[str]:
        mapping = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "React JS",
            ".ts": "TypeScript",
            ".tsx": "React TS",
            ".css": "CSS",
            ".html": "HTML",
            ".json": "JSON",
            ".md": "Markdown",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".sql": "SQL",
            ".prisma": "Prisma",
            ".ini": "Config",
            ".toml": "TOML"
        }
        return mapping.get(suffix)

    def _read_git_metadata(self) -> Dict[str, Any]:
        meta = {"branch": "unknown", "remote_url": "unknown"}
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            return meta

        # 1. Read Active Branch from HEAD file
        head_file = git_dir / "HEAD"
        if head_file.exists():
            try:
                head_content = head_file.read_text(encoding="utf-8").strip()
                if head_content.startswith("ref:"):
                    meta["branch"] = head_content.split("/")[-1]
                else:
                    meta["branch"] = head_content[:8]  # Detached HEAD commit hash
            except Exception:
                pass

        # 2. Extract Remote Origin URL from Git Config file
        config_file = git_dir / "config"
        if config_file.exists():
            try:
                config_content = config_file.read_text(encoding="utf-8")
                # Simple extraction of URL from [remote "origin"] section
                in_origin = False
                for line in config_content.splitlines():
                    line_strip = line.strip()
                    if line_strip.startswith('[remote "origin"]'):
                        in_origin = True
                    elif in_origin and line_strip.startswith("["):
                        in_origin = False
                    elif in_origin and line_strip.startswith("url ="):
                        meta["remote_url"] = line_strip.split("=")[-1].strip()
                        break
            except Exception:
                pass

        return meta

class MetadataDetector:
    """
    Extensible technology detector that reads config listings and directories
    to verify frameworks, databases, and configuration setups.
    """
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def detect_technologies(self, scan_result: Dict[str, Any]) -> List[str]:
        detected: Set[str] = set()
        configs = set(scan_result.get("config_files", []))
        files = set(scan_result.get("file_paths", []))
        
        # Check Next.js / React / Node / Prisma / Tailwind from config files
        package_json_path = self.repo_path / "package.json"
        package_content = ""
        if package_json_path.exists():
            try:
                package_content = package_json_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
                
        # 1. Next.js
        if "next.config.js" in configs or "next.config.ts" in configs or "next" in package_content:
            detected.add("Next.js")
            detected.add("React")
            
        # 2. React
        if "react" in package_content:
            detected.add("React")

        # 3. TypeScript
        if "tsconfig.json" in configs or any(f.endswith(".ts") or f.endswith(".tsx") for f in files):
            detected.add("TypeScript")
            
        # 4. JavaScript / Python
        if any(f.endswith(".py") for f in files):
            detected.add("Python")
        if any(f.endswith(".js") or f.endswith(".jsx") for f in files):
            detected.add("JavaScript")

        # 5. Tailwind CSS
        if "tailwind.config.js" in configs or "tailwind.config.ts" in configs or "tailwindcss" in package_content:
            detected.add("Tailwind CSS")

        # 6. Prisma
        if "schema.prisma" in configs or "prisma" in package_content or any("prisma" in f for f in files):
            detected.add("Prisma")

        # 7. Docker
        if "Dockerfile" in configs or "docker-compose.yml" in configs:
            detected.add("Docker")
        if "docker-compose.yml" in configs:
            detected.add("Docker Compose")

        # 8. GitHub Actions
        if any(f.startswith(".github/workflows/") for f in files):
            detected.add("GitHub Actions")

        # Check Python configurations (FastAPI, Django, Flask, SQLAlchemy)
        requirements_path = self.repo_path / "requirements.txt"
        req_content = ""
        if requirements_path.exists():
            try:
                req_content = requirements_path.read_text(encoding="utf-8", errors="replace").lower()
            except Exception:
                pass
                
        pyproject_path = self.repo_path / "pyproject.toml"
        pyproj_content = ""
        if pyproject_path.exists():
            try:
                pyproj_content = pyproject_path.read_text(encoding="utf-8", errors="replace").lower()
            except Exception:
                pass

        combined_python_deps = req_content + "\n" + pyproj_content

        # 9. FastAPI
        if "fastapi" in combined_python_deps:
            detected.add("FastAPI")

        # 10. Django
        if "django" in combined_python_deps or "manage.py" in files:
            detected.add("Django")

        # 11. Flask
        if "flask" in combined_python_deps:
            detected.add("Flask")

        # 12. SQLAlchemy
        if "sqlalchemy" in combined_python_deps:
            detected.add("SQLAlchemy")

        # 13. Databases (SQLite, PostgreSQL)
        if "sqlite3" in combined_python_deps or any(f.endswith(".db") or f.endswith(".sqlite") for f in files):
            detected.add("SQLite")
        if "psycopg2" in combined_python_deps or "postgresql" in combined_python_deps:
            detected.add("PostgreSQL")

        return sorted(list(detected))

class ConventionDetector:
    """
    Analyzes codebase files layout and naming patterns to deduce
    coding conventions, directory layers, and routing styles.
    """
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def detect_conventions(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        files = scan_result.get("file_paths", [])
        
        # 1. Naming casing detection
        snake_count = 0
        camel_count = 0
        kebab_count = 0
        pascal_count = 0
        
        for f in files:
            name = Path(f).stem
            if "_" in name and name.islower():
                snake_count += 1
            elif "-" in name and name.islower():
                kebab_count += 1
            elif name[0].isupper() and "_" not in name and "-" not in name:
                pascal_count += 1
            elif name[0].islower() and any(c.isupper() for c in name) and "_" not in name and "-" not in name:
                camel_count += 1

        casing = "mixed"
        max_votes = max(snake_count, camel_count, kebab_count, pascal_count, 1)
        if max_votes > len(files) * 0.4:  # If one case covers > 40%
            if max_votes == snake_count: casing = "snake_case"
            elif max_votes == kebab_count: casing = "kebab-case"
            elif max_votes == pascal_count: casing = "PascalCase"
            elif max_votes == camel_count: casing = "camelCase"

        # 2. Folder organization structure
        # Check if layered architecture (api, core, models) vs feature-based (users, auth)
        layered_keys = {"api", "core", "models", "services", "controllers", "routes", "views", "tests"}
        layered_hits = sum(1 for f in files if any(k in f.split("/") for k in layered_keys))
        
        folder_org = "layered"
        if layered_hits < len(files) * 0.2:
            # Low layered hits suggests a feature-driven or flat folder layout
            folder_org = "feature-driven"

        # 3. API router organization
        api_org = "FastAPI endpoints router"
        if any(f.startswith("app/api/") for f in files):
            api_org = "Next.js App Router"
        elif any(f.startswith("pages/api/") for f in files):
            api_org = "Next.js Pages Router"
        elif any("django" in f for f in files) or "manage.py" in files:
            api_org = "Django views/urls mapping"

        # 4. Testing structure
        test_structure = "root tests directory"
        if any(f.endswith(".test.py") or f.endswith(".test.ts") or f.endswith(".test.js") for f in files):
            test_structure = "inline sibling files (*.test.*)"
        elif any("__tests__" in f for f in files):
            test_structure = "co-located __tests__ directories"

        # 5. Database patterns
        techs = MetadataDetector(str(self.repo_path)).detect_technologies(scan_result)
        db_pattern = "SQLAlchemy ORM models"
        if "Prisma" in techs:
            db_pattern = "Prisma Schema models"
        elif "Django" in techs:
            db_pattern = "Django ORM models"

        return {
            "naming_convention": casing,
            "folder_organization": folder_org,
            "api_organization": api_org,
            "testing_structure": test_structure,
            "database_pattern": db_pattern
        }
