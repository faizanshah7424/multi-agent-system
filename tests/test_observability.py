import os
import tempfile
import unittest
import shutil
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Set temporary directory for persistence during tests
if not os.environ.get("PERSIST_DIR"):
    import tempfile
    os.environ["PERSIST_DIR"] = tempfile.mkdtemp()

temp_dir = os.environ["PERSIST_DIR"]

from config import settings
settings.persist_dir = temp_dir

from fastapi.testclient import TestClient
from api.app import app
from core.metrics import metrics_collector, calculate_cost
from core.cache import llm_cache, tool_cache
from core.logging import set_correlation_context, get_correlation_context

class TestObservabilityLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        from core.database import engine
        engine.dispose()

    def setUp(self):
        metrics_collector.clear()
        llm_cache.invalidate()
        tool_cache.invalidate()

    def test_pricing_calculation(self):
        # Test standard pricing
        cost_flash = calculate_cost("gemini-2.5-flash", 1000, 2000)
        # 1000 * (0.075 / 1M) + 2000 * (0.30 / 1M)
        expected_flash = (1000 * 0.075 / 1_000_000) + (2000 * 0.30 / 1_000_000)
        self.assertAlmostEqual(cost_flash, expected_flash)

        # Test model prefix fallback (e.g. gemini-2.5-pro-latest)
        cost_pro = calculate_cost("gemini-2.5-pro-latest", 1000, 2000)
        expected_pro = (1000 * 1.25 / 1_000_000) + (2000 * 5.00 / 1_000_000)
        self.assertAlmostEqual(cost_pro, expected_pro)

        # Test unknown model fallback (should fallback to flash pricing)
        cost_unknown = calculate_cost("gemini-unknown-model", 1000, 2000)
        self.assertAlmostEqual(cost_unknown, expected_flash)

    def test_configurable_pricing(self):
        # Override pricing in settings
        with patch.dict(settings.model_pricing, {"custom-model": {"input": 1.0 / 1_000_000, "output": 2.0 / 1_000_000}}):
            cost_custom = calculate_cost("custom-model", 1000, 2000)
            expected_custom = (1000 * 1.0 / 1_000_000) + (2000 * 2.0 / 1_000_000)
            self.assertAlmostEqual(cost_custom, expected_custom)

    def test_metrics_collection_counters(self):
        self.assertEqual(metrics_collector.requests, 0)
        metrics_collector.record_request()
        self.assertEqual(metrics_collector.requests, 1)

        self.assertEqual(metrics_collector.agent_executions, 0)
        metrics_collector.record_agent_run(success=True)
        metrics_collector.record_agent_run(success=False)
        self.assertEqual(metrics_collector.agent_executions, 2)
        self.assertEqual(metrics_collector.failures, 1)

        self.assertEqual(metrics_collector.workflow_executions, 0)
        metrics_collector.record_workflow_run(duration_s=1.5, success=True)
        metrics_collector.record_workflow_run(duration_s=3.0, success=False)
        self.assertEqual(metrics_collector.workflow_executions, 2)
        self.assertEqual(metrics_collector.failures, 2)  # 1 from agent, 1 from workflow

        metrics_collector.record_retry()
        self.assertEqual(metrics_collector.retries, 1)

        metrics_collector.record_tool_run()
        self.assertEqual(metrics_collector.tool_executions, 1)

    def test_llm_call_metrics_accounting(self):
        # Configure correlation variables
        set_correlation_context(
            task_id="task_123",
            workflow_id="wf_456",
            agent_name="researcher",
            execution_id="exec_789",
            request_id="req_999",
            session_id="session_abc"
        )

        metrics_collector.record_llm_call(
            model_name="gemini-2.5-flash",
            prompt_tokens=500,
            completion_tokens=250,
            total_tokens=750,
            execution_time_ms=120.0
        )

        # Audit costs
        costs = metrics_collector.get_costs()
        expected_cost = calculate_cost("gemini-2.5-flash", 500, 250)
        self.assertAlmostEqual(costs["total_system_cost_usd"], expected_cost)
        self.assertAlmostEqual(costs["cost_per_agent_usd"]["researcher"], expected_cost)
        self.assertAlmostEqual(costs["cost_per_task_usd"]["task_123"], expected_cost)
        self.assertAlmostEqual(costs["cost_per_workflow_usd"]["wf_456"], expected_cost)
        self.assertAlmostEqual(costs["cost_per_request_usd"]["req_999"], expected_cost)

        # Audit tokens
        tokens = metrics_collector.get_tokens()
        self.assertEqual(tokens["total_prompt_tokens"], 500)
        self.assertEqual(tokens["total_completion_tokens"], 250)
        self.assertEqual(tokens["total_tokens"], 750)
        self.assertEqual(tokens["tokens_by_agent"]["researcher"], 750)
        self.assertEqual(tokens["tokens_by_task"]["task_123"], 750)
        self.assertEqual(tokens["tokens_by_workflow"]["wf_456"], 750)
        self.assertEqual(tokens["tokens_by_session"]["session_abc"], 750)

    def test_llm_cache(self):
        # Put into cache
        llm_cache.set("Hello", "Be helpful", "gemini-2.5-flash", "Response text", schema="SchemaStr", ttl=60.0)
        
        # Retrieval
        val = llm_cache.get("Hello", "Be helpful", "gemini-2.5-flash", "SchemaStr")
        self.assertEqual(val, "Response text")
        
        # Miss checks
        val_miss = llm_cache.get("Hello2", "Be helpful", "gemini-2.5-flash", "SchemaStr")
        self.assertIsNone(val_miss)

        metrics = llm_cache.get_metrics()
        self.assertEqual(metrics["hits"], 1)
        self.assertEqual(metrics["misses"], 1)
        self.assertAlmostEqual(metrics["hit_rate"], 0.5)

        # Invalidation
        llm_cache.invalidate()
        self.assertEqual(llm_cache._cache, {})

    def test_llm_cache_ttl(self):
        # Cache with 0.01s TTL
        llm_cache.set("Hello", "Be helpful", "gemini-2.5-flash", "Response text", ttl=0.01)
        time.sleep(0.02)
        val = llm_cache.get("Hello", "Be helpful", "gemini-2.5-flash")
        self.assertIsNone(val) # Expired

    def test_tool_cache(self):
        # Read-only tool should cache
        tool_cache.set("web_search", {"query": "test"}, "Search results")
        val = tool_cache.get("web_search", {"query": "test"})
        self.assertEqual(val, "Search results")

        # Non read-only tool should not cache
        tool_cache.set("file_writer", {"path": "a.txt"}, "success")
        val_writer = tool_cache.get("file_writer", {"path": "a.txt"})
        self.assertIsNone(val_writer)

        metrics = tool_cache.get_metrics()
        self.assertEqual(metrics["hits"], 1)
        self.assertEqual(metrics["misses"], 1)
        self.assertEqual(metrics["size"], 1)

    def test_performance_metrics(self):
        metrics_collector.record_workflow_run(duration_s=1.0)
        metrics_collector.record_workflow_run(duration_s=2.0)
        metrics_collector.record_workflow_run(duration_s=3.0)
        metrics_collector.record_queue_wait(duration_s=0.5)
        metrics_collector.record_request_duration(duration_s=0.2)

        perf = metrics_collector.get_performance()
        self.assertAlmostEqual(perf["average_workflow_latency_seconds"], 2.0)
        self.assertGreater(perf["p95_workflow_latency_seconds"], 2.0)
        self.assertAlmostEqual(perf["average_queue_wait_time_seconds"], 0.5)
        self.assertAlmostEqual(perf["average_request_latency_seconds"], 0.2)
        
        # Memory usage is best-effort depending on psutil presence
        try:
            import psutil
            self.assertGreater(perf["memory_usage_bytes"], 0)
        except ImportError:
            self.assertEqual(perf["memory_usage_bytes"], 0)

    def test_api_metrics_routes(self):
        # Populate some data
        metrics_collector.record_request()
        metrics_collector.record_llm_call("gemini-2.5-flash", 100, 200, 300, 50.0)

        # GET /metrics
        res = self.client.get("/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["requests_count"], 2)  # 1 from manual, 1 from this API request via middleware
        self.assertIn("performance", data)
        self.assertIn("costs", data)
        self.assertIn("tokens", data)

        # GET /metrics/costs
        res = self.client.get("/metrics/costs")
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_system_cost_usd", res.json())

        # GET /metrics/tokens
        res = self.client.get("/metrics/tokens")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total_tokens"], 300)

        # GET /metrics/performance
        res = self.client.get("/metrics/performance")
        self.assertEqual(res.status_code, 200)
        self.assertIn("memory_usage_bytes", res.json())

        # GET /metrics/cache
        res = self.client.get("/metrics/cache")
        self.assertEqual(res.status_code, 200)
        self.assertIn("llm_cache", res.json())
        self.assertIn("tool_cache", res.json())

    def test_api_middleware_trace_headers(self):
        response = self.client.get("/metrics", headers={"x-request-id": "my_req_id", "x-session-id": "my_sess_id"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-request-id"), "my_req_id")
        self.assertEqual(response.headers.get("x-session-id"), "my_sess_id")

if __name__ == "__main__":
    unittest.main()
