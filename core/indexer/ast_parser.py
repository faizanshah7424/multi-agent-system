import ast
import re
from pathlib import Path
from typing import List, Protocol, Tuple, Set
from core.indexer.interface import SymbolDefinition


class ILanguageParser(Protocol):
    """
    Protocol for parsing programming language files to extract symbol metadata and imports.
    """

    def parse(
        self, file_path: Path, content: str
    ) -> Tuple[List[SymbolDefinition], List[str]]:
        """
        Parses file contents. Returns SymbolDefinitions and raw import module strings.
        """
        ...


class PythonLanguageParser:
    """
    AST-based parser for Python source files.
    """

    def parse(
        self, file_path: Path, content: str
    ) -> Tuple[List[SymbolDefinition], List[str]]:
        symbols: List[SymbolDefinition] = []
        imports: List[str] = []

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            # Skip unparseable python files
            return [], []

        rel_path = str(file_path).replace("\\", "/")

        for node in ast.walk(tree):
            # 1. Parse Class Definitions
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                symbols.append(
                    SymbolDefinition(
                        name=node.name,
                        symbol_type="class",
                        file_path=rel_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        imports=[],
                    )
                )

            # 2. Parse Function & Method Definitions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Distinguish global functions from class methods
                doc = ast.get_docstring(node)
                sym_type = "function"

                symbols.append(
                    SymbolDefinition(
                        name=node.name,
                        symbol_type=sym_type,
                        file_path=rel_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        imports=[],
                    )
                )

            # 3. Parse Import Nodes
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return symbols, list(set(imports))


class JavaScriptLanguageParser:
    """
    Regex-based parser for JavaScript and TypeScript source files.
    """

    def parse(
        self, file_path: Path, content: str
    ) -> Tuple[List[SymbolDefinition], List[str]]:
        symbols: List[SymbolDefinition] = []
        imports: List[str] = []
        rel_path = str(file_path).replace("\\", "/")

        # 1. Capture Import matches: import x from 'y' or require('y')
        import_regex = re.compile(
            r"(?:import\s+(?:[\w*\s{},]*\s+from\s+)?['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))"
        )
        for match in import_regex.finditer(content):
            val = match.group(1) or match.group(2)
            if val:
                # Exclude absolute/external module packages (e.g. 'react', 'next')
                imports.append(val)

        lines = content.splitlines()

        # 2. Capture Class matches: class ClassName
        class_regex = re.compile(r"\bclass\s+(\w+)\b")
        # 3. Capture Function matches: function funcName or const/let name = (...) =>
        func_regex = re.compile(
            r"\bfunction\s+(\w+)\b|\b(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[\w$]+)\s*=>"
        )

        for idx, line in enumerate(lines):
            line_no = idx + 1

            # Class match
            c_match = class_regex.search(line)
            if c_match:
                symbols.append(
                    SymbolDefinition(
                        name=c_match.group(1),
                        symbol_type="class",
                        file_path=rel_path,
                        start_line=line_no,
                        end_line=line_no,
                        docstring=None,
                        imports=[],
                    )
                )
                continue

            # Function match
            f_match = func_regex.search(line)
            if f_match:
                name = f_match.group(1) or f_match.group(2)
                if name:
                    symbols.append(
                        SymbolDefinition(
                            name=name,
                            symbol_type="function",
                            file_path=rel_path,
                            start_line=line_no,
                            end_line=line_no,
                            docstring=None,
                            imports=[],
                        )
                    )

        return symbols, list(set(imports))


class ASTParser:
    """
    Orchestrator selecting the appropriate language parser and resolving imports
    against the physical repository paths.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.py_parser = PythonLanguageParser()
        self.js_parser = JavaScriptLanguageParser()

    def parse_file(self, file_path: Path) -> Tuple[List[SymbolDefinition], List[str]]:
        """Parses a single file, extracting symbols and resolving imports to repo relative paths."""
        if not file_path.exists():
            return [], []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return [], []

        # Ensure path is relative to repo root for symbol definition paths
        rel_file_path = file_path.relative_to(self.repo_path)

        ext = file_path.suffix.lower()
        if ext == ".py":
            symbols, raw_imports = self.py_parser.parse(rel_file_path, content)
            resolved_imports = self._resolve_python_imports(file_path, raw_imports)
            return symbols, resolved_imports
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            symbols, raw_imports = self.js_parser.parse(rel_file_path, content)
            resolved_imports = self._resolve_js_imports(file_path, raw_imports)
            return symbols, resolved_imports

        return [], []

    def _resolve_python_imports(
        self, current_file: Path, imports: List[str]
    ) -> List[str]:
        resolved: Set[str] = set()
        for imp in imports:
            # Convert import dots to directory slashes
            parts = imp.split(".")

            # 1. Absolute import check (relative to repo root)
            abs_path = self.repo_path / "/".join(parts)
            py_file = abs_path.with_suffix(".py")
            init_file = abs_path / "__init__.py"

            if py_file.exists():
                resolved.add(
                    str(py_file.relative_to(self.repo_path)).replace("\\", "/")
                )
            elif init_file.exists():
                resolved.add(
                    str(init_file.relative_to(self.repo_path)).replace("\\", "/")
                )

            # 2. Relative import check (relative to current file's folder)
            else:
                rel_path = current_file.parent / "/".join(parts)
                py_rel = rel_path.with_suffix(".py")
                init_rel = rel_path / "__init__.py"

                if py_rel.exists():
                    resolved.add(
                        str(py_rel.relative_to(self.repo_path)).replace("\\", "/")
                    )
                elif init_rel.exists():
                    resolved.add(
                        str(init_rel.relative_to(self.repo_path)).replace("\\", "/")
                    )

        return list(resolved)

    def _resolve_js_imports(self, current_file: Path, imports: List[str]) -> List[str]:
        resolved: Set[str] = set()
        for imp in imports:
            # Handle standard JS relative imports (starting with ./ or ../)
            if imp.startswith("."):
                target_path = (current_file.parent / imp).resolve()

                # Check different possible file extensions
                for ext in (".ts", ".tsx", ".js", ".jsx"):
                    f_path = target_path.with_suffix(ext)
                    if f_path.exists():
                        resolved.add(
                            str(f_path.relative_to(self.repo_path)).replace("\\", "/")
                        )
                        break

                # Check directory index files
                if target_path.exists() and target_path.is_dir():
                    for ext in (".ts", ".tsx", ".js", ".jsx"):
                        index_f = target_path / f"index{ext}"
                        if index_f.exists():
                            resolved.add(
                                str(index_f.relative_to(self.repo_path)).replace(
                                    "\\", "/"
                                )
                            )
                            break

            # Note: For non-relative import packages (e.g. from 'react'), we omit it as it's not a local repo dependency.
        return list(resolved)
