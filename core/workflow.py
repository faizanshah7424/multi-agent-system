import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.memory import SharedMemory
from core.logging import get_logger
from core.registry import AgentRegistry
from core.schemas import PlannerPlan, PlanStep

logger = get_logger("WorkflowEngine")


class TaskStep(BaseModel):
    """Data model for tracking a single step within a workflow."""

    step_id: int
    name: str
    description: str
    assigned_agent: str
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    dependencies: List[int] = Field(default_factory=list)
    priority: str = "medium"


class WorkflowPlan(BaseModel):
    """Plan model containing the overall project steps."""

    project_title: str
    steps: List[TaskStep]


class WorkflowEngine:
    """
    Orchestration engine that plans tasks, assigns subtasks to specialized agents,
    tracks progress, captures step results, and manages execution errors.
    """

    def __init__(self, memory: SharedMemory):
        self.memory = memory

        # Dynamically instantiate registered agents using the AgentRegistry
        self.registry = AgentRegistry()
        self.agents = {}
        for metadata in self.registry.list_agents():
            try:
                self.agents[metadata.name] = self.registry.create_agent(
                    metadata.name, self.memory
                )
            except Exception as e:
                logger.error(
                    f"Failed to dynamically instantiate registered agent '{metadata.name}': {str(e)}"
                )

    def validate_plan_graph(self, plan: PlannerPlan) -> List[str]:
        """
        Validates the step configuration, assigned agents, dependencies, and cycle existence (DAG check).
        """
        errors = []
        registered_agents = {agent.name for agent in self.registry.list_agents()}
        step_ids = [step.step_id for step in plan.steps]

        # 1. Unique step IDs
        if len(step_ids) != len(set(step_ids)):
            errors.append("Step IDs must be unique.")

        # 2. Check each step
        step_map = {step.step_id: step for step in plan.steps}
        for step in plan.steps:
            # Check assigned agent
            if step.assigned_agent not in registered_agents:
                errors.append(
                    f"Step {step.step_id}: Assigned agent '{step.assigned_agent}' is not registered in the system registry."
                )

            # Check dependencies
            for dep in step.dependencies:
                if dep not in step_map:
                    errors.append(
                        f"Step {step.step_id}: Dependency {dep} is not a valid step ID in the plan."
                    )
                elif dep == step.step_id:
                    errors.append(f"Step {step.step_id}: Cannot depend on itself.")

        # 3. Cycle detection (DAG check) using DFS
        if not errors:
            adj = {step_id: [] for step_id in step_ids}
            for step in plan.steps:
                for dep in step.dependencies:
                    adj[dep].append(step.step_id)

            visited = {}  # state: 0=unvisited, 1=visiting, 2=visited

            def dfs(u):
                visited[u] = 1
                for v in adj[u]:
                    if visited.get(v, 0) == 1:
                        return True
                    elif visited.get(v, 0) == 0:
                        if dfs(v):
                            return True
                visited[u] = 2
                return False

            for step_id in step_ids:
                if visited.get(step_id, 0) == 0:
                    if dfs(step_id):
                        errors.append(
                            "The workflow plan contains dependency cycles (not a valid DAG)."
                        )
                        break

        return errors

    def execute_workflow(self, task: str) -> Dict[str, Any]:
        """
        Executes a task end-to-end: plans steps, runs agents, and updates states.

        Args:
            task: Task description to execute.

        Returns:
            The final dictionary content of the memory session.
        """
        import time
        from core.logging import set_correlation_context
        from core.metrics import metrics_collector

        start_time = time.time()
        session_id = self.memory.session_id

        # Configure root workflow correlation context
        set_correlation_context(
            task_id=session_id, workflow_id=session_id, agent_name="system"
        )

        self.memory.update_status("running")
        self.memory.add_log(
            "workflow", f"Starting workflow execution for task: '{task}'"
        )

        # Step 1: Planning
        set_correlation_context(
            task_id=session_id, workflow_id=session_id, agent_name="planner"
        )
        planner = self.agents["planner"]
        try:
            plan_data = planner.run(task)
        except Exception as e:
            err = f"Planning failed: {str(e)}"
            logger.error(err)
            self.memory.add_log("workflow", err, level="ERROR")
            self.memory.update_status("failed")
            metrics_collector.record_workflow_run(
                time.time() - start_time, success=False
            )
            return self.memory.show()

        # Schema & Graph Validation
        try:
            validated_plan = PlannerPlan(**plan_data)
            validation_errors = self.validate_plan_graph(validated_plan)
            if validation_errors:
                err_msg = (
                    f"Workflow plan validation failed with {len(validation_errors)} error(s):\n"
                    + "\n".join(f"- {e}" for e in validation_errors)
                )
                logger.error(err_msg)
                self.memory.add_log("workflow", err_msg, level="ERROR")
                self.memory.update_status("failed")
                metrics_collector.record_workflow_run(
                    time.time() - start_time, success=False
                )
                return self.memory.show()
        except Exception as ve:
            err_msg = f"Workflow plan schema validation failed: {str(ve)}"
            logger.error(err_msg)
            self.memory.add_log("workflow", err_msg, level="ERROR")
            self.memory.update_status("failed")
            metrics_collector.record_workflow_run(
                time.time() - start_time, success=False
            )
            return self.memory.show()

        steps = plan_data.get("steps", [])
        if not steps:
            err = "Planning failed: No execution steps generated by the Planner."
            self.memory.add_log("workflow", err, level="ERROR")
            self.memory.update_status("failed")
            metrics_collector.record_workflow_run(
                time.time() - start_time, success=False
            )
            return self.memory.show()

        # Convert steps to TaskStep model dictionaries and write to memory
        serialized_steps = []
        for s in steps:
            step_model = TaskStep(
                step_id=s.get("step_id", 0),
                name=s.get("title", s.get("name", "Unnamed Step")),
                description=s.get("description", ""),
                assigned_agent=s.get("assigned_agent", "developer"),
                dependencies=s.get("dependencies", []),
                priority=s.get("priority", "medium"),
            )
            serialized_steps.append(step_model.model_dump())

        self.memory.set("workflow_steps", serialized_steps)
        self.memory.add_log(
            "workflow",
            f"Plan generated: {plan_data.get('project_title', 'System Plan')}. Total steps: {len(steps)}",
        )

        # Step 2: Step-by-Step execution
        for step_dict in serialized_steps:
            step_id = step_dict["step_id"]
            step_name = step_dict["name"]
            agent_name = step_dict["assigned_agent"]
            description = step_dict["description"]

            # Update log correlation to target active step agent
            set_correlation_context(
                task_id=session_id, workflow_id=session_id, agent_name=agent_name
            )

            self.memory.add_log(
                "workflow",
                f"Beginning Step {step_id}: '{step_name}' -> Assigned to {agent_name}",
            )
            self._update_step(
                step_id,
                status="running",
                started_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            )

            # Select the assigned agent
            agent = self.agents.get(agent_name)
            if not agent:
                logger.warning(
                    f"Agent '{agent_name}' not found. Defaulting to Tool Agent."
                )
                agent = self.agents["tool_agent"]
                agent_name = "tool_agent"
                set_correlation_context(
                    task_id=session_id, workflow_id=session_id, agent_name=agent_name
                )

            try:
                agent_prompt = (
                    f"Overall Goal: {task}\n"
                    f"Your specific subtask: {description}\n"
                    "Carry out this subtask using your tools and context."
                )

                # Execute agent run
                result = agent.run(agent_prompt)

                # Mark step as completed
                self._update_step(
                    step_id,
                    status="completed",
                    result=result,
                    completed_at=datetime.now(timezone.utc)
                    .replace(tzinfo=None)
                    .isoformat(),
                )
                self.memory.add_log(
                    "workflow", f"Step {step_id} completed successfully."
                )
                metrics_collector.record_agent_run(success=True)

            except Exception as e:
                err_msg = f"Step {step_id} failed: {str(e)}"
                logger.error(err_msg, exc_info=True)
                self._update_step(
                    step_id,
                    status="failed",
                    result=err_msg,
                    completed_at=datetime.now(timezone.utc)
                    .replace(tzinfo=None)
                    .isoformat(),
                )
                self.memory.add_log("workflow", err_msg, level="ERROR")
                self.memory.update_status("failed")
                metrics_collector.record_agent_run(success=False)
                metrics_collector.record_workflow_run(
                    time.time() - start_time, success=False
                )
                return self.memory.show()

        # All steps completed successfully
        set_correlation_context(
            task_id=session_id, workflow_id=session_id, agent_name="system"
        )
        self.memory.update_status("completed")
        self.memory.add_log("workflow", "All workflow steps completed successfully.")
        metrics_collector.record_workflow_run(time.time() - start_time, success=True)
        return self.memory.show()

    def _update_step(
        self,
        step_id: int,
        status: str,
        result: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> None:
        """
        Updates step attributes inside memory.
        """
        steps = self.memory.get("workflow_steps", [])
        for step in steps:
            if step["step_id"] == step_id:
                step["status"] = status
                if result is not None:
                    step["result"] = result
                if started_at is not None:
                    step["started_at"] = started_at
                if completed_at is not None:
                    step["completed_at"] = completed_at
                break
        self.memory.set("workflow_steps", steps)
