import unittest
from typing import List, Type, TypeVar, Iterator
from pydantic import BaseModel

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.models.interface import IModelProvider, ModelParameters
from core.queue.scheduler import IDAGScheduler, PlanStep, PlanDAG, DAGScheduler
from core.queue.planning_engine import PlanningEngine

T = TypeVar("T", bound=BaseModel)


class MockModelProvider(IModelProvider):
    """
    Mock model provider returning a pre-defined PlanDAG for test validation.
    """

    def __init__(self, plan_to_return: PlanDAG) -> None:
        self.plan_to_return = plan_to_return
        self.last_prompt = None
        self.last_system_instruction = None

    def generate(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> str:
        return ""

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str,
        params: ModelParameters,
    ) -> T:
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction
        return self.plan_to_return

    def generate_stream(
        self, prompt: str, system_instruction: str, params: ModelParameters
    ) -> Iterator[str]:
        yield ""


class TestPlanningAndScheduler(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.scheduler = DIContainer.get(IDAGScheduler)
        self.planning_engine = DIContainer.get("planning_engine")

    def test_di_registrations(self) -> None:
        self.assertTrue(isinstance(self.scheduler, DAGScheduler))
        self.assertTrue(isinstance(self.planning_engine, PlanningEngine))

    def test_dag_validation_success(self) -> None:
        # Step 1 -> Step 2 -> Step 3
        s1 = PlanStep(step_id=1, dependencies=[], assigned_agent="developer")
        s2 = PlanStep(step_id=2, dependencies=[1], assigned_agent="reviewer")
        s3 = PlanStep(step_id=3, dependencies=[2], assigned_agent="developer")
        dag = PlanDAG(steps=[s1, s2, s3])

        errors = self.scheduler.validate_dag(dag)
        self.assertEqual(len(errors), 0)

    def test_dag_validation_duplicate_ids(self) -> None:
        # Duplicate Step ID: 1
        s1 = PlanStep(step_id=1, dependencies=[], assigned_agent="developer")
        s2 = PlanStep(step_id=1, dependencies=[], assigned_agent="reviewer")
        dag = PlanDAG(steps=[s1, s2])

        errors = self.scheduler.validate_dag(dag)
        self.assertTrue(any("unique" in e.lower() for e in errors))

    def test_dag_validation_missing_dependency(self) -> None:
        # Step 1 depends on non-existent step 5
        s1 = PlanStep(step_id=1, dependencies=[5], assigned_agent="developer")
        dag = PlanDAG(steps=[s1])

        errors = self.scheduler.validate_dag(dag)
        self.assertTrue(
            any(
                "non-existent" in e.lower() or "invalid dependency" in e.lower()
                for e in errors
            )
        )

    def test_dag_validation_invalid_agent(self) -> None:
        # Step 1 assigned to an unknown agent
        s1 = PlanStep(step_id=1, dependencies=[], assigned_agent="unknown_agent")
        dag = PlanDAG(steps=[s1])

        errors = self.scheduler.validate_dag(dag)
        self.assertTrue(any("registered agent profile" in e.lower() for e in errors))

    def test_dag_validation_cycle(self) -> None:
        # Cycle: 1 depends on 2, 2 depends on 1
        s1 = PlanStep(step_id=1, dependencies=[2], assigned_agent="developer")
        s2 = PlanStep(step_id=2, dependencies=[1], assigned_agent="reviewer")
        dag = PlanDAG(steps=[s1, s2])

        errors = self.scheduler.validate_dag(dag)
        self.assertTrue(
            any(
                "circular dependencies" in e.lower() or "cycle" in e.lower()
                for e in errors
            )
        )

    def test_topological_sort_execution_order(self) -> None:
        # Branching graph:
        # 1 has no deps
        # 2 depends on 1
        # 3 depends on 1
        # 4 depends on 2 and 3
        s1 = PlanStep(step_id=1, dependencies=[], assigned_agent="developer")
        s2 = PlanStep(step_id=2, dependencies=[1], assigned_agent="reviewer")
        s3 = PlanStep(step_id=3, dependencies=[1], assigned_agent="developer")
        s4 = PlanStep(step_id=4, dependencies=[2, 3], assigned_agent="developer")
        dag = PlanDAG(steps=[s1, s2, s3, s4])

        order = self.scheduler.get_execution_order(dag)

        # 1 must run first
        self.assertEqual(order[0], 1)
        # 4 must run last
        self.assertEqual(order[-1], 4)
        # 2 and 3 must run before 4
        self.assertTrue(order.index(2) > order.index(1))
        self.assertTrue(order.index(3) > order.index(1))
        self.assertTrue(order.index(4) > order.index(2))
        self.assertTrue(order.index(4) > order.index(3))

    def test_topological_sort_cycle_error(self) -> None:
        # Cycle: 1 -> 2 -> 3 -> 1
        s1 = PlanStep(step_id=1, dependencies=[3], assigned_agent="developer")
        s2 = PlanStep(step_id=2, dependencies=[1], assigned_agent="reviewer")
        s3 = PlanStep(step_id=3, dependencies=[2], assigned_agent="developer")
        dag = PlanDAG(steps=[s1, s2, s3])

        with self.assertRaises(ValueError):
            self.scheduler.get_execution_order(dag)

    def test_planning_engine_structured_generation(self) -> None:
        # 1. Setup target PlanDAG
        s1 = PlanStep(
            step_id=10,
            dependencies=[],
            assigned_agent="developer",
            description="Step 10 description",
        )
        expected_plan = PlanDAG(steps=[s1])

        # 2. Register mock provider inside the DI Container to prevent external calls
        mock_provider = MockModelProvider(expected_plan)
        DIContainer.register(IModelProvider, mock_provider)

        # 3. Trigger planner execution
        user_req = "Write a login endpoint"
        repo_details = "Python FastAPI codebase"
        generated_dag = self.planning_engine.generate_plan(user_req, repo_details)

        # 4. Verify outcomes
        self.assertEqual(len(generated_dag.steps), 1)
        self.assertEqual(generated_dag.steps[0].step_id, 10)
        self.assertEqual(generated_dag.steps[0].description, "Step 10 description")

        # Verify prompt variables substitution
        self.assertIn("Write a login endpoint", mock_provider.last_prompt)
        self.assertIn("Python FastAPI codebase", mock_provider.last_prompt)
        self.assertIn("Planner Agent", mock_provider.last_system_instruction)
