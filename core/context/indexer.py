import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
from tree_sitter import Language, Parser

# Language grammar imports
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava

# Load language mappings
LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
    "typescript": Language(tstypescript.language_typescript()),
    "tsx": Language(tstypescript.language_tsx()),
    "go": Language(tsgo.language()),
    "java": Language(tsjava.language()),
}


@dataclass(frozen=True)
class SourceSymbol:
    """
    Immutable representation of an extracted syntax symbol.
    """

    language: str
    name: str
    kind: str
    filepath: str
    start_line: int
    end_line: int
    signature: str
    parent: Optional[str]
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TreeSitterIndexer:
    """
    Parser indexing service using Tree-sitter AST to parse codebase files
    and extract structures (classes, functions, methods, interfaces, enums).
    """

    def __init__(self) -> None:
        self.parsers: Dict[str, Parser] = {}
        for lang_name, lang_obj in LANGUAGES.items():
            self.parsers[lang_name] = Parser(lang_obj)


    def detect_language(self, filepath: str) -> Optional[str]:
        ext = Path(filepath).suffix.lower()
        if ext == ".py":
            return "python"
        elif ext == ".js" or ext == ".jsx":
            return "javascript"
        elif ext == ".ts":
            return "typescript"
        elif ext == ".tsx":
            return "tsx"
        elif ext == ".go":
            return "go"
        elif ext == ".java":
            return "java"
        return None

    def extract_symbols(
        self, filepath: str, content: str
    ) -> List[SourceSymbol]:
        lang_name = self.detect_language(filepath)
        if not lang_name or lang_name not in self.parsers:
            return []

        parser = self.parsers[lang_name]
        source_bytes = content.encode("utf-8", errors="ignore")
        tree = parser.parse(source_bytes)

        checksum = hashlib.sha256(source_bytes).hexdigest()[:16]
        symbols: List[SourceSymbol] = []

        # Target AST node types for symbol extraction
        target_types = {
            "class_definition",
            "function_definition",
            "class_declaration",
            "function_declaration",
            "method_definition",
            "interface_declaration",
            "method_declaration",
            "type_declaration",
            "enum_declaration",
            "constructor_declaration",
            "struct_specifier",
        }

        def get_node_name(n) -> str:
            name_node = n.child_by_field_name("name")
            if name_node:
                return name_node.text.decode("utf-8", errors="ignore").strip()
            for child in n.children:
                if child.type == "identifier":
                    return (
                        child.text.decode("utf-8", errors="ignore").strip()
                    )
            return "anonymous"

        def get_docstring(n) -> str:
            if lang_name == "python":
                body = n.child_by_field_name("body")
                if body and body.children:
                    first_child = body.children[0]
                    if first_child.type == "expression_statement":
                        string_child = first_child.children[0]
                        if string_child.type == "string":
                            txt = (
                                string_child.text.decode(
                                    "utf-8", errors="ignore"
                                ).strip()
                            )
                            if txt.startswith('"""') or txt.startswith(
                                "'''"
                            ):
                                return txt[3:-3].strip()
                            elif txt.startswith('"') or txt.startswith("'"):
                                return txt[1:-1].strip()
            return ""

        def traverse(
            node,
            parent_name: Optional[str] = None,
            parent_kind: Optional[str] = None,
        ) -> None:
            current_parent = parent_name
            current_parent_kind = parent_kind
            if node.type in target_types:
                name = get_node_name(node)
                kind = node.type.split("_")[0]

                if lang_name == "go" and node.type == "method_declaration":
                    kind = "method"

                if kind == "class":
                    pass
                elif "function" in node.type:
                    if parent_kind == "class":
                        kind = "method"
                    else:
                        kind = "function"
                elif "method" in node.type:
                    kind = "method"
                elif "interface" in node.type:
                    kind = "interface"
                elif "struct" in node.type:
                    kind = "struct"
                elif "enum" in node.type:
                    kind = "enum"

                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                node_text = node.text.decode("utf-8", errors="ignore")
                signature = (
                    node_text.splitlines()[0].strip() if node_text else ""
                )

                doc = get_docstring(node)

                symbols.append(
                    SourceSymbol(
                        language=lang_name,
                        name=name,
                        kind=kind,
                        filepath=filepath,
                        start_line=start_line,
                        end_line=end_line,
                        signature=signature,
                        parent=parent_name,
                        checksum=checksum,
                        metadata={"docstring": doc} if doc else {},
                    )
                )
                current_parent = name
                current_parent_kind = kind

            for child in node.children:
                traverse(child, current_parent, current_parent_kind)

        traverse(tree.root_node)
        return symbols

