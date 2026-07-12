import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.di import DIContainer
from core.indexer.interface import ICodeIndexer, SymbolDefinition
from core.indexer.code_indexer import CodeIndexer
from core.indexer.graph_db import CodeGraphDB
from core.indexer.repository_scanner import (
    RepositoryScanner,
    MetadataDetector,
    ConventionDetector,
)
from core.indexer.report_generator import RepositoryReportGenerator


class TestRepositoryIntelligence(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_path = Path(__file__).parent.parent.parent.resolve()
        self.indexer = CodeIndexer()

    def test_repository_scanner(self) -> None:
        scanner = RepositoryScanner(str(self.repo_path))
        scan_res = scanner.scan()

        self.assertIn("file_paths", scan_res)
        self.assertIn("languages", scan_res)
        self.assertIn("config_files", scan_res)
        self.assertIn("git_metadata", scan_res)

        # Verify language counts include Python
        self.assertIn("Python", scan_res["languages"])
        self.assertGreater(scan_res["languages"]["Python"], 0)

        # Check git metadata reading
        git_meta = scan_res["git_metadata"]
        self.assertIn("branch", git_meta)
        self.assertIn("remote_url", git_meta)

    def test_metadata_detector(self) -> None:
        scanner = RepositoryScanner(str(self.repo_path))
        scan_res = scanner.scan()

        detector = MetadataDetector(str(self.repo_path))
        tech = detector.detect_technologies(scan_res)

        self.assertIn("Python", tech)
        self.assertIn("FastAPI", tech)
        self.assertIn("SQLAlchemy", tech)
        self.assertIn("SQLite", tech)

    def test_convention_detector(self) -> None:
        scanner = RepositoryScanner(str(self.repo_path))
        scan_res = scanner.scan()

        detector = ConventionDetector(str(self.repo_path))
        convs = detector.detect_conventions(scan_res)

        self.assertIn("naming_convention", convs)
        self.assertEqual(convs["folder_organization"], "layered")
        self.assertEqual(convs["api_organization"], "FastAPI endpoints router")
        self.assertEqual(convs["database_pattern"], "SQLAlchemy ORM models")

    def test_code_indexer_and_graph_db(self) -> None:
        # Index our own repository (or subset of files to keep it fast)
        self.indexer.index_repository(str(self.repo_path))

        # Query a symbol we know exists
        symbols = self.indexer.find_symbol("CodeIndexer")
        self.assertGreater(len(symbols), 0)

        symbol = symbols[0]
        self.assertEqual(symbol.name, "CodeIndexer")
        self.assertEqual(symbol.symbol_type, "class")
        self.assertTrue(symbol.file_path.endswith("core/indexer/code_indexer.py"))

        # Query references to another class/function
        references = self.indexer.get_references("CodeIndexer")
        self.assertGreater(len(references), 0)
        # di_setup.py imports CodeIndexer
        self.assertTrue(any("di_setup.py" in r for r in references))

    def test_circular_dependency_detection(self) -> None:
        # Clear DB symbols and insert mock circular edges to verify DFS detection
        db = CodeGraphDB()
        db.clear_symbols()

        # Create cycle: A -> B -> C -> A
        db.insert_edges("file_a.py", "file_b.py", "import")
        db.insert_edges("file_b.py", "file_c.py", "import")
        db.insert_edges("file_c.py", "file_a.py", "import")

        # Add non-cyclic edge: C -> D
        db.insert_edges("file_c.py", "file_d.py", "import")

        cycles = self.indexer.detect_circular_dependencies()
        self.assertEqual(len(cycles), 1)

        cycle = cycles[0]
        # Cycle path should contain files a, b, c and loop back to a
        self.assertIn("file_a.py", cycle)
        self.assertIn("file_b.py", cycle)
        self.assertIn("file_c.py", cycle)
        self.assertEqual(cycle[0], cycle[-1])

    def test_report_generation(self) -> None:
        scanner = RepositoryScanner(str(self.repo_path))
        scan_res = scanner.scan()

        tech_detector = MetadataDetector(str(self.repo_path))
        tech = tech_detector.detect_technologies(scan_res)

        conv_detector = ConventionDetector(str(self.repo_path))
        convs = conv_detector.detect_conventions(scan_res)

        generator = RepositoryReportGenerator()
        report = generator.generate_report(
            scan_data=scan_res,
            tech_stack=tech,
            conventions=convs,
            symbol_count=15,
            edges_count=20,
            circular_imports=[["file_a.py", "file_b.py", "file_a.py"]],
        )

        self.assertIn("# CodeOrbit AI: Repository Engineering Report", report)
        self.assertIn("## Executive Summary", report)
        self.assertIn("## Architecture Overview", report)
        self.assertIn("## Coding Conventions", report)
        self.assertIn("## High-Risk Areas", report)
        self.assertIn("circular dependency cycles detected", report)
