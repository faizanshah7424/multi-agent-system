import unittest
from unittest.mock import MagicMock
from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.memory import SharedMemory
from core.workflow import WorkflowEngine, TaskStep
from core.planning.planning_models import PlannerExecutionPlan, PlanningTask
from core.planning.planner import IPlanner, Planner
from core.planning.decomposer import ITaskDecomposer, TaskDecomposer
from core.planning.task_graph import TaskGraph


class TestAutonomousPlanningEngine(unittest.TestCase):
    def setUp(self) -> None:
        from config import settings
        DIContainer.clear()
        self._backup_sqlite_path = settings.sqlite_path
        settings.sqlite_path = ":memory:"
        bootstrap_di()

    def tearDown(self) -> None:
        from config import settings
        settings.sqlite_path = self._backup_sqlite_path

    def test_di_registration(self) -> None:
        """
        Verify IPlanner and ITaskDecomposer are correctly registered and resolved.
        """
        planner = DIContainer.get(IPlanner)
        decomposer = DIContainer.get(ITaskDecomposer)

        self.assertIsInstance(planner, Planner)
        self.assertIsInstance(decomposer, TaskDecomposer)

    def test_planning_and_dependency_inference(self) -> None:
        """
        Verify that natural language planning resolves correct task dependencies.
        """
        planner = Planner()
        plan = planner.plan("Create a user registration API with SQLite and unit tests")

        self.assertIsInstance(plan, PlannerExecutionPlan)
        self.assertGreater(len(plan.tasks), 0)
        self.assertIn("user registration", plan.project_title.lower() or plan.tasks[0].name.lower())

        # Check sequential dependency inference
        # Schema config (1) -> Implement API (2) -> Write tests (3) -> Verify/Deploy (4)
        tasks_map = {t.task_id: t for t in plan.tasks}
        
        self.assertIn(1, tasks_map)
        self.assertIn(2, tasks_map)
        self.assertIn(3, tasks_map)
        self.assertIn(4, tasks_map)

        self.assertEqual(tasks_map[2].dependencies, [1])
        self.assertEqual(tasks_map[3].dependencies, [2])
        self.assertEqual(tasks_map[4].dependencies, [3])

    def test_complexity_estimation(self) -> None:
        """
        Verify that complexity estimation accurately calculates Low, Medium, High classifications.
        """
        decomposer = TaskDecomposer()

        task_low = PlanningTask(
            task_id=1,
            name="Simple task",
            description="Short desc",
            assigned_agent="developer",
            dependencies=[],
            files=[]
        )
        task_high = PlanningTask(
            task_id=2,
            name="Complex task",
            description="A very long description that requires many steps and utilizes multiple files to complete this engineering objective properly.",
            assigned_agent="developer",
            dependencies=[1, 2, 3],
            files=["file1.py", "file2.py", "file3.py"]
        )

        self.assertEqual(decomposer.estimate_complexity(task_low), "Low")
        self.assertIn(decomposer.estimate_complexity(task_high), ("High", "Very High"))

    def test_validation_cycle_detection(self) -> None:
        """
        Verify that TaskGraph successfully detects cycles and invalid task mappings.
        """
        # Empty workflow check
        graph_empty = TaskGraph([])
        self.assertIn("empty workflow", "; ".join(graph_empty.validate()))

        # Valid DAG tasks
        tasks = [
            PlanningTask(task_id=1, name="A", description="A", assigned_agent="developer", dependencies=[]),
            PlanningTask(task_id=2, name="B", description="B", assigned_agent="developer", dependencies=[1]),
        ]
        graph_valid = TaskGraph(tasks)
        self.assertEqual(len(graph_valid.validate()), 0)

        # Cycle: A -> B -> A
        tasks_cycle = [
            PlanningTask(task_id=1, name="A", description="A", assigned_agent="developer", dependencies=[2]),
            PlanningTask(task_id=2, name="B", description="B", assigned_agent="developer", dependencies=[1]),
        ]
        graph_cycle = TaskGraph(tasks_cycle)
        self.assertIn("dependency cycles", "; ".join(graph_cycle.validate()))

        # Non-existent task dependency reference
        tasks_invalid_ref = [
            PlanningTask(task_id=1, name="A", description="A", assigned_agent="developer", dependencies=[99]),
        ]
        graph_invalid_ref = TaskGraph(tasks_invalid_ref)
        self.assertIn("non-existent task", "; ".join(graph_invalid_ref.validate()))

    def test_confidence_scoring(self) -> None:
        """
        Verify planner confidence scoring logic bounds scores between 0.1 and 1.0.
        """
        planner = Planner()
        plan = planner.plan("Refactor core loops")
        self.assertTrue(0.1 <= plan.confidence_score <= 1.0)

    def test_telemetry_generation(self) -> None:
        """
        Verify planning execution records telemetry metrics.
        """
        planner = Planner()
        plan = planner.plan("Optimize memory usage")

        tel = plan.telemetry
        self.assertIn("planning_duration", tel)
        self.assertIn("task_count", tel)
        self.assertIn("dependency_count", tel)
        self.assertIn("parallelism_score", tel)
        self.assertIn("planner_confidence", tel)

        self.assertEqual(tel["task_count"], len(plan.tasks))

    def test_workflow_engine_backward_compatibility(self) -> None:
        """
        Verify that WorkflowEngine executes pre-planned execution plans and raw objective strings.
        """
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        memory = SharedMemory(session_id=session_id)
        engine = WorkflowEngine(memory=memory)

        # Mock subtask agent runs by pre-registering mocks for all expected agent roles
        mock_agent = MagicMock()
        mock_agent.run.return_value = "Success"
        for name in ["developer", "reviewer", "researcher", "tool_agent", "planner", "repository_engineer"]:
            engine.agents[name] = mock_agent

        # 1. Execute using natural language objective (new Planner plans it automatically)
        engine.execute_workflow("Refactor cache endpoints")
        self.assertEqual(engine.memory.state.status, "completed")

        # 2. Execute using an already generated PlannerExecutionPlan
        planner = Planner()
        plan = planner.plan("Create REST API")
        
        # Reset memory for clean test
        memory.set("workflow_steps", [])
        memory.update_status("pending")

        engine.execute_workflow(plan)
        self.assertEqual(engine.memory.state.status, "completed")
        self.assertGreater(len(memory.get("workflow_steps", [])), 0)
