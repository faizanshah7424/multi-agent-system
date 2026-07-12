from typing import Any, Dict, List
from pathlib import Path


class RepositoryReportGenerator:
    """
    Assembles scanning details, AST dependency maps, conventions, and symbol
    counts into a comprehensive, structured Markdown engineering report.
    """

    def generate_report(
        self,
        scan_data: Dict[str, Any],
        tech_stack: List[str],
        conventions: Dict[str, Any],
        symbol_count: int,
        edges_count: int,
        circular_imports: List[List[str]],
    ) -> str:
        files = scan_data.get("file_paths", [])
        total_size_kb = scan_data.get("total_size_bytes", 0) / 1024.0
        git_meta = scan_data.get("git_metadata", {})

        # Determine entry points
        entry_points = self._determine_entry_points(files)

        # Calculate routing files
        routing_files = [
            f
            for f in files
            if "route" in f or "endpoint" in f or "api/" in f or "urls.py" in f
        ]

        # Calculate auth files
        auth_files = [
            f
            for f in files
            if any(
                k in f.lower() for k in ("auth", "login", "session", "jwt", "apikey")
            )
        ]

        # Calculate database files
        db_files = [
            f
            for f in files
            if any(
                k in f.lower()
                for k in ("database", "models", "schema.prisma", "migrations")
            )
        ]

        # Calculate testing files
        testing_files = [f for f in files if "test" in f or "spec" in f]

        # Risk assessment
        risks = self._calculate_risks(files, circular_imports, testing_files)

        # Insertion and refactoring recommendations
        insertions = self._suggest_insertions(files, tech_stack)
        refactorings = self._suggest_refactorings(files, circular_imports)

        report = []
        report.append("# CodeOrbit AI: Repository Engineering Report")
        report.append(
            f"\n*Generated for branch:* `{git_meta.get('branch', 'unknown')}` | *Remote origin:* `{git_meta.get('remote_url', 'unknown')}`\n"
        )
        report.append("---")

        # Executive Summary
        report.append("\n## Executive Summary")
        report.append(f"- **Total Files Found:** {len(files)}")
        report.append(f"- **Total Repository Size:** {total_size_kb:.2f} KB")
        report.append(
            f"- **Core Programming Languages:** {', '.join(scan_data.get('languages', {}).keys())}"
        )
        report.append(
            f"- **Registered Code Symbols:** {symbol_count} definitions indexed in Code Graph DB."
        )
        report.append(
            f"- **Dependency Relationship Edges:** {edges_count} edges mapped."
        )
        report.append(
            f"- **Active Frameworks & Technologies:** {', '.join(tech_stack)}"
        )

        # Architecture Overview
        report.append("\n## Architecture Overview")
        report.append(
            f"The repository follows a **{conventions.get('folder_organization', 'layered')}** directory structure layout."
        )
        report.append("Detailed layout characteristics:")
        report.append(
            f"- Folder organization style: `{conventions.get('folder_organization')}`"
        )
        report.append(
            f"- API Endpoint routing layer: `{conventions.get('api_organization')}`"
        )
        report.append(f"- Persistence model: `{conventions.get('database_pattern')}`")
        report.append(
            f"- Test suite arrangement: `{conventions.get('testing_structure')}`"
        )

        # Folder Structure Summary
        report.append("\n## Folder Structure")
        root_dirs = sorted(list({f.split("/")[0] for f in files if "/" in f}))
        report.append("Key top-level directories mapped in this repository:")
        for r in root_dirs:
            # Gather nested files count in this dir
            nested_count = sum(1 for f in files if f.startswith(f"{r}/"))
            report.append(f"- `/{r}` ({nested_count} file(s))")

        # Framework Summary
        report.append("\n## Framework Summary")
        report.append(
            "The repository environment integrates the following framework systems:"
        )
        for tech in tech_stack:
            report.append(f"- **{tech}**")

        # Dependency Summary
        report.append("\n## Dependency Summary")
        report.append(f"- Total file import/dependency links: {edges_count}")
        if circular_imports:
            report.append(
                f"- **Warning:** {len(circular_imports)} circular dependency cycles detected in imports graph."
            )
        else:
            report.append("- No circular dependency cycles found.")

        # Entry Points
        report.append("\n## Entry Points")
        if entry_points:
            for ep in entry_points:
                report.append(f"- `/{ep}`")
        else:
            report.append("- No standard entry points detected.")

        # Routing Summary
        report.append("\n## Routing Summary")
        if routing_files:
            report.append("Detected endpoint and routing files:")
            for rf in routing_files[:10]:
                report.append(f"- `/{rf}`")
            if len(routing_files) > 10:
                report.append(f"- ...and {len(routing_files) - 10} more files.")
        else:
            report.append("- No routing/API routes files discovered.")

        # Authentication Summary
        report.append("\n## Authentication Summary")
        if auth_files:
            report.append("Authentication and session management files:")
            for af in auth_files[:8]:
                report.append(f"- `/{af}`")
        else:
            report.append(
                "- No authentication management components detected in codebase."
            )

        # Database Summary
        report.append("\n## Database Summary")
        report.append(
            f"Persistence framework: **{conventions.get('database_pattern')}**"
        )
        if db_files:
            report.append("Associated persistent and migration modules:")
            for dbf in db_files[:8]:
                report.append(f"- `/{dbf}`")
        else:
            report.append("- No database models or migrations detected.")

        # Testing Summary
        report.append("\n## Testing Summary")
        report.append(
            f"Test suite arrangement: **{conventions.get('testing_structure')}**"
        )
        report.append(f"- Total test files discovered: {len(testing_files)}")
        if testing_files:
            report.append("Key test suite paths:")
            for tf in testing_files[:8]:
                report.append(f"- `/{tf}`")

        # Coding Conventions
        report.append("\n## Coding Conventions")
        report.append(
            f"- **Naming casing convention:** `{conventions.get('naming_convention')}`"
        )
        report.append(
            f"- **Folder architecture pattern:** `{conventions.get('folder_organization')}`"
        )
        report.append("- **Class declarations:** Standard PascalCase naming expected.")

        # Extension Points
        report.append("\n## Extension Points")
        report.append("Calculated safe locations to register new features/handlers:")
        if "FastAPI" in tech_stack:
            report.append(
                "- Adding router endpoints under `api/routes/` or registers in FastAPI `APIRouter` instances."
            )
        if "Next.js" in tech_stack:
            report.append(
                "- App router folders under `app/` or pages files under `pages/` directory."
            )

        # High-Risk Areas
        report.append("\n## High-Risk Areas")
        for risk in risks:
            report.append(f"- {risk}")

        # Suggested Feature Insertion Locations
        report.append("\n## Suggested Feature Insertion Locations")
        for ins in insertions:
            report.append(f"- {ins}")

        # Recommended Refactoring Opportunities
        report.append("\n## Recommended Refactoring Opportunities")
        for ref in refactorings:
            report.append(f"- {ref}")

        return "\n".join(report)

    def _determine_entry_points(self, files: List[str]) -> List[str]:
        entries = []
        for f in files:
            if f in (
                "main.py",
                "app.py",
                "wsgi.py",
                "manage.py",
                "index.js",
                "index.ts",
                "server.js",
                "app.ts",
            ):
                entries.append(f)
            elif "pages/index" in f or "app/page" in f:
                entries.append(f)
        return entries

    def _calculate_risks(
        self, files: List[str], circular_imports: List[List[str]], tests: List[str]
    ) -> List[str]:
        risks = []
        if circular_imports:
            risks.append(
                f"**Circular dependencies:** {len(circular_imports)} cycles could cause import locks at runtime."
            )
        if not tests:
            risks.append(
                "**Missing Tests:** Codebase contains no active test suite directories or test specs."
            )
        elif len(tests) < len(files) * 0.05:
            risks.append(
                "**Low Test Coverage:** Low ratio of test files to implementation source modules."
            )

        # Check if there are large files (> 500 lines)
        # We can flag them, but since we don't read them all here, we can skip or flag based on file list
        return risks or ["No high-risk structural anomalies detected."]

    def _suggest_insertions(self, files: List[str], tech_stack: List[str]) -> List[str]:
        suggestions = []
        if "FastAPI" in tech_stack:
            suggestions.append(
                "Add endpoint handlers under api/routes/ and declare them in APIRouter initialization."
            )
        elif "Django" in tech_stack:
            suggestions.append(
                "Create views in app/views.py and add mappings to app/urls.py."
            )

        if "Next.js" in tech_stack:
            suggestions.append("Create page components inside app/ or pages/ folders.")

        return suggestions or [
            "Add new implementation files under core/ or services/ folder structure."
        ]

    def _suggest_refactorings(
        self, files: List[str], circular_imports: List[List[str]]
    ) -> List[str]:
        suggestions = []
        if circular_imports:
            for cycle in circular_imports[:3]:
                cycle_str = " -> ".join(cycle)
                suggestions.append(f"Decouple import loop: {cycle_str}")
        if len(files) > 200:
            suggestions.append(
                "Large repository detected. Consider modularizing into distinct packages."
            )
        return suggestions or [
            "No immediate refactoring items suggested for codebase structure."
        ]
