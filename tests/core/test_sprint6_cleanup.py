import logging
import unittest
from unittest.mock import MagicMock
from core.cleanup import CleanupCoordinator


class TestCleanupCoordinator(unittest.TestCase):
    def setUp(self) -> None:
        # Purge any stagnant records in CleanupCoordinator
        CleanupCoordinator._registry.clear()

    def test_resource_registration_and_lifo_execution(self) -> None:
        task_id = "test_cleanup_task"
        call_order = []

        # Register resource callbacks
        CleanupCoordinator.register_resource(
            task_id=task_id,
            resource_type="mock_res_1",
            resource_identifier="id_1",
            cleanup_callable=lambda: call_order.append(1)
        )

        CleanupCoordinator.register_resource(
            task_id=task_id,
            resource_type="mock_res_2",
            resource_identifier="id_2",
            cleanup_callable=lambda: call_order.append(2)
        )

        # Trigger cleanup
        CleanupCoordinator.execute_cleanup(task_id)

        # Verify LIFO execution: resource 2 must be cleaned up before resource 1
        self.assertEqual(call_order, [2, 1])

        # Verify that task record is removed from registry after execution
        self.assertNotIn(task_id, CleanupCoordinator._registry)

    def test_exception_isolation(self) -> None:
        task_id = "test_error_task"
        call_order = []

        # Callback 1 will raise an exception
        def failing_cleanup():
            raise RuntimeError("Cleanup failure simulator")

        CleanupCoordinator.register_resource(
            task_id=task_id,
            resource_type="faulty_res",
            resource_identifier="err_id",
            cleanup_callable=failing_cleanup
        )

        # Callback 2 will execute successfully
        CleanupCoordinator.register_resource(
            task_id=task_id,
            resource_type="safe_res",
            resource_identifier="ok_id",
            cleanup_callable=lambda: call_order.append("success")
        )

        # Trigger cleanup: must not raise/throw exception
        try:
            CleanupCoordinator.execute_cleanup(task_id)
        except Exception as e:
            self.fail(f"execute_cleanup threw an exception: {e}")

        # Verify that Callback 2 executed despite Callback 1 raising an exception
        self.assertEqual(call_order, ["success"])

    def test_orphan_detection_runs_safely(self) -> None:
        try:
            orphans = CleanupCoordinator.detect_orphans()
            self.assertIn("orphan_containers", orphans)
            self.assertIn("orphan_workspaces", orphans)
            self.assertIn("stale_temp_dirs", orphans)
        except Exception as e:
            self.fail(f"detect_orphans raised an exception: {e}")
