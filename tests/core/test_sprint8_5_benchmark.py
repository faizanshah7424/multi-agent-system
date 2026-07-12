import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.benchmark.interface import IBenchmarkManager
from core.benchmark.manager import BenchmarkManager
from core.benchmark.injector import FailureInjectionEngine
from core.benchmark.schemas import InjectableBug
from core.queue.scheduler import PlanDAG
from core.queue.execution_runtime import IPlanExecutor


class MockPlanExecutor(IPlanExecutor):
    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed

    def execute_plan(self, task_id: str, plan: PlanDAG) -> bool:
        return self.succeed


class TestBenchmarkFramework(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.manager = DIContainer.get(IBenchmarkManager)
        self.injector = FailureInjectionEngine()

        # Override PlanExecutor with a mock to prevent E2E database lockups
        self.mock_executor = MockPlanExecutor(succeed=True)
        DIContainer.register(IPlanExecutor, self.mock_executor)

    def test_di_registration(self) -> None:
        self.assertTrue(isinstance(self.manager, BenchmarkManager))

    def test_list_projects(self) -> None:
        res = self.manager.list_projects()
        self.assertEqual(res["projects_count"], 7)
        project_names = [p["name"] for p in res["projects"]]
        self.assertIn("python_lib", project_names)
        self.assertIn("python_cli", project_names)
        self.assertIn("fastapi_api", project_names)
        self.assertIn("nextjs_ts", project_names)
        self.assertIn("react_web", project_names)
        self.assertIn("hospital_sys", project_names)
        self.assertIn("ecommerce_sys", project_names)

    def test_bug_injection_and_reversion(self) -> None:
        bug = InjectableBug(
            bug_id="test_bug",
            file_path="utils.py",
            target_content="return x + y",
            bug_content="return x +",
            category="SYNTAX_ERROR",
        )

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            target_file = temp_path / "utils.py"
            target_file.write_text(
                "def add(x, y):\n    return x + y\n", encoding="utf-8"
            )

            # 1. Inject Bug
            injected = self.injector.inject_bug(str(temp_path), bug)
            self.assertTrue(injected)
            self.assertIn("return x +", target_file.read_text(encoding="utf-8"))

            # 2. Revert Bug
            reverted = self.injector.revert_bug(str(temp_path), bug)
            self.assertTrue(reverted)
            self.assertIn("return x + y", target_file.read_text(encoding="utf-8"))

    def test_e2e_benchmark_execution_and_reports(self) -> None:
        # Run benchmark
        report = self.manager.run_benchmark("python_lib", "syntax_bug")

        # Assert report structure
        self.assertEqual(report["status"], "SUCCESS")
        self.assertEqual(report["project_name"], "python_lib")
        self.assertEqual(report["metrics"]["detection_accuracy"], 1.0)
        self.assertGreater(report["scores"]["Overall Engineering Score"], 0.8)

        # Assert versioned markdown reports generated
        docs_dir = Path(__file__).parent.parent.parent / "docs"
        reports_dir = docs_dir / "reports"

        self.assertTrue((docs_dir / "BENCHMARK_SUITE.md").exists())
        self.assertTrue((reports_dir / "benchmark_results.md").exists())
        self.assertTrue((reports_dir / "benchmark_scorecard.md").exists())
        self.assertTrue((reports_dir / "benchmark_history.md").exists())
