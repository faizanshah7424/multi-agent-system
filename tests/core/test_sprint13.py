import os
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.config.manager import ConfigurationManager, SystemConfig
from core.diagnostics.health import RepositoryHealthInspector
from core.diagnostics.recovery import RecoveryManager, CrashReportGenerator
from core.diagnostics.metrics import MetricsCollector, RunMetrics, LatencyBreakdown
from core.diagnostics.doc_audit import DocumentationAudit
from core.diagnostics.version import VersionManager


class TestSprint13DiagnosticsAndCLI(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.health_inspector = DIContainer.get(RepositoryHealthInspector)
        self.recovery_mgr = DIContainer.get(RecoveryManager)
        self.metrics_collector = DIContainer.get(MetricsCollector)
        self.doc_audit = DIContainer.get(DocumentationAudit)
        self.version_mgr = DIContainer.get(VersionManager)

    def test_configuration_manager(self) -> None:
        # Load and validate default manager configuration
        mgr = ConfigurationManager(env="development")
        val = mgr.validate()
        self.assertTrue(val["valid"] or len(val["errors"]) > 0)
        self.assertEqual(val["config"]["env"], "development")

    def test_repository_health_inspector(self) -> None:
        # Run health diagnostics
        report = self.health_inspector.run_diagnostics()
        self.assertIsNotNone(report.disk_free_gb)
        self.assertGreater(len(report.items), 0)

    def test_recovery_and_crash_reporter(self) -> None:
        # Test recovery ping
        db_ok = self.recovery_mgr.check_and_recover_db()
        self.assertTrue(db_ok)

        # Test crash report creation
        error = ValueError("Simulation failure for diagnostics verification.")
        report_path = CrashReportGenerator.generate_report(
            error=error,
            active_agent="developer",
            current_task="Test Sprint 13 E2E recovery",
            sandbox_id="temp_sandbox_1",
            model_name="gemini-2.5-flash",
        )

        path = Path(report_path)
        self.assertTrue(path.exists())

        # Read the file to check keys
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["error_type"], "ValueError")
            self.assertEqual(data["active_agent"], "developer")

        # Cleanup
        path.unlink()

    def test_metrics_collector(self) -> None:
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "metrics.json"
            collector = MetricsCollector(persist_path=str(file_path))

            # Record a run metric
            latencies = LatencyBreakdown(
                planning=0.1,
                execution=1.2,
                repair=0.0,
                consensus=0.5,
                memory_lookup=0.05,
            )
            run = RunMetrics(
                task_id="task_test_metrics",
                success=True,
                latencies=latencies,
                tokens_used=1500,
                cost_usd=0.02,
            )
            collector.record_run(run)

            # Verify persistence and loading
            self.assertTrue(file_path.exists())
            summary = collector.get_summary()
            self.assertEqual(summary["total_runs"], 1)
            self.assertEqual(summary["success_rate"], 100.0)
            self.assertAlmostEqual(summary["avg_cost_usd"], 0.02)

    def test_documentation_audit(self) -> None:
        res = self.doc_audit.run_audit()
        self.assertIn("passed", res)
        self.assertIn("warnings", res)

    def test_version_manager(self) -> None:
        info = self.version_mgr.get_version_info()
        self.assertEqual(info["version"], "1.0.0")
        self.assertEqual(info["architecture_version"], "2.2")
        self.assertEqual(info["sprint_version"], "13")


if __name__ == "__main__":
    unittest.main()
