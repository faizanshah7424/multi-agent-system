import os
import sqlite3
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.context.indexer import TreeSitterIndexer, SourceSymbol
from core.context.retrieval import RetrievalPipeline, get_db_connection
from core.schemas import RetrievedCodeChunk


class TestTreeSitterIndexing(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.indexer = DIContainer.get(TreeSitterIndexer)
        self.pipeline = DIContainer.get(RetrievalPipeline)

    def test_di_registration(self) -> None:
        self.assertTrue(isinstance(self.indexer, TreeSitterIndexer))
        self.assertTrue(isinstance(self.pipeline, RetrievalPipeline))
        self.assertIs(self.pipeline.indexer, self.indexer)

    def test_language_detection(self) -> None:
        self.assertEqual(self.indexer.detect_language("src/main.py"), "python")
        self.assertEqual(self.indexer.detect_language("index.js"), "javascript")
        self.assertEqual(self.indexer.detect_language("types.ts"), "typescript")
        self.assertEqual(self.indexer.detect_language("app.tsx"), "tsx")
        self.assertEqual(self.indexer.detect_language("main.go"), "go")
        self.assertEqual(self.indexer.detect_language("App.java"), "java")
        self.assertIsNone(self.indexer.detect_language("README.md"))

    def test_python_symbol_extraction(self) -> None:
        code = """class MyCalculator:
    \"\"\"Calculates sums\"\"\"
    def add(self, x, y):
        return x + y

def root_level_function():
    pass
"""
        symbols = self.indexer.extract_symbols("calc.py", code)
        
        # Check extraction count (1 class, 1 method, 1 function)
        self.assertEqual(len(symbols), 3)
        
        # Verify MyCalculator class details
        cls_sym = [s for s in symbols if s.name == "MyCalculator"][0]
        self.assertEqual(cls_sym.kind, "class")
        self.assertEqual(cls_sym.start_line, 1)
        self.assertEqual(cls_sym.end_line, 4)
        self.assertEqual(cls_sym.signature, "class MyCalculator:")

        self.assertEqual(cls_sym.metadata.get("docstring"), "Calculates sums")

        # Verify add method details
        method_sym = [s for s in symbols if s.name == "add"][0]
        self.assertEqual(method_sym.kind, "method")
        self.assertEqual(method_sym.parent, "MyCalculator")
        self.assertEqual(method_sym.start_line, 3)
        self.assertEqual(method_sym.end_line, 4)


        # Verify root_level_function
        func_sym = [s for s in symbols if s.name == "root_level_function"][0]
        self.assertEqual(func_sym.kind, "function")
        self.assertIsNone(func_sym.parent)

    def test_javascript_symbol_extraction(self) -> None:
        code = """class UserService {
    getUser(id) {
        return { id: id, name: "test" };
    }
}

function healthCheck() {
    return "OK";
}
"""
        symbols = self.indexer.extract_symbols("user.js", code)
        self.assertEqual(len(symbols), 3)

        cls_sym = [s for s in symbols if s.name == "UserService"][0]
        self.assertEqual(cls_sym.kind, "class")

        method_sym = [s for s in symbols if s.name == "getUser"][0]
        self.assertEqual(method_sym.kind, "method")
        self.assertEqual(method_sym.parent, "UserService")

        func_sym = [s for s in symbols if s.name == "healthCheck"][0]
        self.assertEqual(func_sym.kind, "function")

    def test_go_symbol_extraction(self) -> None:
        code = """package main

type Config struct {
    Port int
}

func (c *Config) GetPort() int {
    return c.Port
}

func main() {
}
"""
        symbols = self.indexer.extract_symbols("main.go", code)
        # Should detect struct, method, function
        self.assertTrue(len(symbols) >= 2)

        func_sym = [s for s in symbols if s.name == "main"][0]
        self.assertEqual(func_sym.kind, "function")

        method_sym = [s for s in symbols if s.name == "GetPort"][0]
        self.assertEqual(method_sym.kind, "method")

    def test_java_symbol_extraction(self) -> None:
        code = """public class MainApp {
    public static void main(String[] args) {
        System.out.println("hello");
    }
}
"""
        symbols = self.indexer.extract_symbols("MainApp.java", code)
        self.assertEqual(len(symbols), 2)

        cls_sym = [s for s in symbols if s.name == "MainApp"][0]
        self.assertEqual(cls_sym.kind, "class")

        method_sym = [s for s in symbols if s.name == "main"][0]
        self.assertEqual(method_sym.kind, "method")

    def test_incremental_indexing(self) -> None:
        task_id = "test_incr_task"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "app.py"
            file1.write_text("def run():\n    pass", encoding="utf-8")
            
            # 1. Clean Index
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM retrieval_code_symbols WHERE task_id = ?", (task_id,))
            conn.commit()
            conn.close()

            # 2. Run Indexing first time
            self.pipeline.index_workspace(task_id, temp_dir)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT symbol_name, checksum FROM retrieval_code_symbols WHERE task_id = ?", (task_id,))
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "run")
            first_checksum = rows[0][1]
            conn.close()

            # 3. Modify file (app.py content changed)
            file1.write_text("def run():\n    print('hello')\ndef stop():\n    pass", encoding="utf-8")
            self.pipeline.index_workspace(task_id, temp_dir)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT symbol_name, checksum FROM retrieval_code_symbols WHERE task_id = ? ORDER BY symbol_name", (task_id,))
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][0], "run")
            self.assertEqual(rows[1][0], "stop")
            self.assertNotEqual(rows[0][1], first_checksum)
            conn.close()

            # 4. Delete file (Removed file cleanup)
            file1.unlink()
            self.pipeline.index_workspace(task_id, temp_dir)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT symbol_name FROM retrieval_code_symbols WHERE task_id = ?", (task_id,))
            rows = cursor.fetchall()
            # Symbols should be cleared
            self.assertEqual(len(rows), 0)
            conn.close()

    def test_database_indexing(self) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Check required indexes exist
        self.assertIn("idx_retrieval_lang_name", indexes)
        self.assertIn("idx_retrieval_filepath", indexes)
        self.assertIn("idx_retrieval_kind", indexes)
        self.assertIn("idx_retrieval_checksum", indexes)
