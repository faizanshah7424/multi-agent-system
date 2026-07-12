from pathlib import Path
from typing import List, Dict, Set

from core.database import get_db_session
from core.indexer.interface import ICodeIndexer, SymbolDefinition
from core.indexer.graph_db import CodeGraphDB, DBCodeEdge
from core.indexer.ast_parser import ASTParser
from core.indexer.repository_scanner import RepositoryScanner

class CodeIndexer(ICodeIndexer):
    """
    Concrete implementation of the ICodeIndexer interface.
    Manages parsing and persistence of repository symbols and call references.
    """
    def __init__(self) -> None:
        self.db = CodeGraphDB()

    def index_repository(self, repo_path: str) -> None:
        """
        Crawls a workspace, parses ASTs, and inserts symbols & import edges into CodeGraphDB.
        """
        repo_dir = Path(repo_path).resolve()
        scanner = RepositoryScanner(str(repo_dir))
        parser = ASTParser(str(repo_dir))
        
        # 1. Scan files
        scan_res = scanner.scan()
        files = scan_res.get("file_paths", [])

        # 2. Reset database tables
        self.db.clear_symbols()

        # 3. Parse ASTs and insert records
        for rel_file in files:
            abs_file = repo_dir / rel_file
            
            # Parse code symbols and import targets
            symbols, imports = parser.parse_file(abs_file)
            
            if symbols:
                self.db.insert_symbols(symbols)
                
            for imp in imports:
                self.db.insert_edges(
                    source_file=rel_file,
                    target_file=imp,
                    relation_type="import"
                )

    def find_symbol(self, name: str) -> List[SymbolDefinition]:
        """
        Retrieves all SymbolDefinitions matching an identifier.
        """
        return self.db.query_symbols(name)

    def get_references(self, symbol_name: str) -> List[str]:
        """
        Finds all files importing the module where the symbol is defined.
        """
        # Find which files define the symbol
        definitions = self.find_symbol(symbol_name)
        if not definitions:
            return []

        referencing_files = set()
        for df in definitions:
            # Query all files that have a directed import edge pointing to this file
            sources = self.db.query_edges_by_target(df.file_path)
            for src in sources:
                referencing_files.add(src)

        return sorted(list(referencing_files))

    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Runs DFS cycle-detection across all import edges to trace circular loops.
        """
        # 1. Load all edges and build adjacency list
        adj: Dict[str, List[str]] = {}
        with get_db_session() as session:
            edges = session.query(DBCodeEdge).filter(DBCodeEdge.relation_type == "import").all()
            for edge in edges:
                adj.setdefault(edge.source_file, []).append(edge.target_file)

        visited: Set[str] = set()
        stack: List[str] = []
        stack_set: Set[str] = set()
        raw_cycles: List[List[str]] = []

        def dfs(node: str) -> None:
            if node in stack_set:
                # Cycle detected
                cycle_start_idx = stack.index(node)
                cycle = stack[cycle_start_idx:] + [node]
                raw_cycles.append(cycle)
                return
            if node in visited:
                return

            visited.add(node)
            stack.append(node)
            stack_set.add(node)

            for neighbor in adj.get(node, []):
                dfs(neighbor)

            stack.pop()
            stack_set.remove(node)

        # Run DFS for all nodes in the adjacency list
        for node in adj.keys():
            if node not in visited:
                dfs(node)

        # 3. Deduplicate circular shifts of the same cycle
        unique_cycles: Set[tuple] = set()
        for cycle in raw_cycles:
            # Normalize: find the lexicographically smallest path representation
            cycle_nodes = cycle[:-1] # Remove the repeat node at the end
            if not cycle_nodes:
                continue
            
            min_node = min(cycle_nodes)
            min_idx = cycle_nodes.index(min_node)
            normalized_cycle = cycle_nodes[min_idx:] + cycle_nodes[:min_idx]
            unique_cycles.add(tuple(normalized_cycle))

        return [list(c) + [c[0]] for c in unique_cycles]
