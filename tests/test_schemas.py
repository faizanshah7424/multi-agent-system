import unittest
from pydantic import ValidationError

from core.schemas import (
    PlanStep, PlannerPlan, AgentAction, ToolRequest, ToolResponse,
    VectorMemoryConfig, DAGWorkflowPlan, MultiAgentCollaborationConfig, HumanApprovalWorkflow
)
from core.workflow import WorkflowEngine, TaskStep
from core.memory import SharedMemory
from core.registry import AgentRegistry, AgentMetadata

class TestSchemasAndWorkflowValidation(unittest.TestCase):
    def setUp(self):
        # Setup clean AgentRegistry for testing
        self.registry = AgentRegistry()
        self.registry._registry.clear()
        
        # Register standard mock agents for dependency verification
        for agent_name in ["researcher", "developer", "reviewer", "planner"]:
            meta = AgentMetadata(
                name=agent_name,
                role=f"Mock {agent_name.capitalize()}",
                description="Mock agent description"
            )
            # Register a dummy class
            self.registry.register(meta, object)

        # Setup workflow engine with dummy memory
        self.memory = SharedMemory("test_validation_session")
        self.engine = WorkflowEngine(self.memory)

    def test_planner_schemas(self):
        # Valid plan
        step1 = PlanStep(
            step_id=1,
            title="Research requirements",
            assigned_agent="researcher",
            description="Gather task specifications",
            dependencies=[],
            priority="high"
        )
        step2 = PlanStep(
            step_id=2,
            title="Implement API",
            assigned_agent="developer",
            description="Develop core FastAPI routes",
            dependencies=[1],
            priority="high"
        )
        
        plan = PlannerPlan(
            project_title="FastAPI Integration",
            steps=[step1, step2]
        )
        
        self.assertEqual(plan.project_title, "FastAPI Integration")
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].step_id, 1)
        self.assertEqual(plan.steps[1].dependencies, [1])

        # Invalid field types
        with self.assertRaises(ValidationError):
            PlanStep(
                step_id="not_an_int",
                title="Bad Step",
                assigned_agent="developer",
                description="Failed type parsing"
            )

    def test_agent_action_schema(self):
        # Valid tool call
        action1 = AgentAction(
            thought="I need to scan the root folder.",
            action="call_tool",
            tool="dir_scanner",
            arguments={"path": "."}
        )
        self.assertEqual(action1.action, "call_tool")
        self.assertEqual(action1.tool, "dir_scanner")
        
        # Valid final response
        action2 = AgentAction(
            thought="I have finished generating the implementation plan.",
            action="respond",
            final_answer="Here is the final python file script code."
        )
        self.assertEqual(action2.action, "respond")
        self.assertIsNotNone(action2.final_answer)

    def test_tool_schemas(self):
        # Valid request
        req = ToolRequest(
            tool_name="web_search",
            arguments={"query": "Gemini native structured outputs"}
        )
        self.assertEqual(req.tool_name, "web_search")
        
        # Valid response
        res = ToolResponse(
            tool_name="web_search",
            status="success",
            result="Found documentation."
        )
        self.assertEqual(res.status, "success")
        self.assertIsNone(res.error)

    def test_workflow_validation_valid_dag(self):
        # 1. Valid DAG Plan: 1 -> 2 -> 3
        plan = PlannerPlan(
            project_title="Valid DAG Plan",
            steps=[
                PlanStep(
                    step_id=1,
                    title="Task A",
                    assigned_agent="researcher",
                    description="Desc A",
                    dependencies=[],
                    priority="high"
                ),
                PlanStep(
                    step_id=2,
                    title="Task B",
                    assigned_agent="developer",
                    description="Desc B",
                    dependencies=[1],
                    priority="medium"
                ),
                PlanStep(
                    step_id=3,
                    title="Task C",
                    assigned_agent="reviewer",
                    description="Desc C",
                    dependencies=[2],
                    priority="low"
                )
            ]
        )
        errors = self.engine.validate_plan_graph(plan)
        self.assertEqual(len(errors), 0, f"Expected valid DAG, got errors: {errors}")

    def test_workflow_validation_cycle_detection(self):
        # 2. Cycle: 1 -> 2 -> 3 -> 1
        plan = PlannerPlan(
            project_title="Cyclic Plan",
            steps=[
                PlanStep(
                    step_id=1,
                    title="Task A",
                    assigned_agent="researcher",
                    description="Desc A",
                    dependencies=[3],
                    priority="high"
                ),
                PlanStep(
                    step_id=2,
                    title="Task B",
                    assigned_agent="developer",
                    description="Desc B",
                    dependencies=[1],
                    priority="medium"
                ),
                PlanStep(
                    step_id=3,
                    title="Task C",
                    assigned_agent="reviewer",
                    description="Desc C",
                    dependencies=[2],
                    priority="low"
                )
            ]
        )
        errors = self.engine.validate_plan_graph(plan)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("cycle" in e.lower() for e in errors))

    def test_workflow_validation_missing_dependency(self):
        # 3. Missing dependency: Step 2 depends on step 5, but step 5 is not in the plan
        plan = PlannerPlan(
            project_title="Missing Dependency Plan",
            steps=[
                PlanStep(
                    step_id=1,
                    title="Task A",
                    assigned_agent="researcher",
                    description="Desc A",
                    dependencies=[],
                    priority="high"
                ),
                PlanStep(
                    step_id=2,
                    title="Task B",
                    assigned_agent="developer",
                    description="Desc B",
                    dependencies=[5],
                    priority="medium"
                )
            ]
        )
        errors = self.engine.validate_plan_graph(plan)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("dependency 5" in e.lower() for e in errors))

    def test_workflow_validation_unregistered_agent(self):
        # 4. Unregistered agent: Assign task to 'alien_agent'
        plan = PlannerPlan(
            project_title="Invalid Agent Plan",
            steps=[
                PlanStep(
                    step_id=1,
                    title="Task A",
                    assigned_agent="alien_agent",
                    description="Desc A",
                    dependencies=[],
                    priority="high"
                )
            ]
        )
        errors = self.engine.validate_plan_graph(plan)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("alien_agent" in e.lower() for e in errors))

    def test_future_compatibility_schemas(self):
        # Vector memory validation
        vector_cfg = VectorMemoryConfig(
            collection_name="long_term_memories",
            dimension=768,
            embedding_model="text-embedding-004",
            distance_metric="cosine"
        )
        self.assertEqual(vector_cfg.dimension, 768)

        # Human approval validation
        approval = HumanApprovalWorkflow(
            step_id=3,
            status="approved",
            approved_by="senior_engineer",
            comments="Code styling and correctness checked."
        )
        self.assertEqual(approval.status, "approved")

if __name__ == "__main__":
    unittest.main()
