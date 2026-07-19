import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.memory import SharedMemory
from core.logging import get_logger
from core.registry import AgentRegistry
from core.schemas import PlannerPlan, PlanStep
from core.planning.planning_models import PlannerExecutionPlan, PlanningTask
from core.planning.planner import IPlanner

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

    def __init__(
        self,
        memory: SharedMemory,
        planner: Optional[IPlanner] = None,
    ):
        self.memory = memory

        if planner is None:
            try:
                from core.di import DIContainer
                planner = DIContainer.get(IPlanner)
            except Exception:
                from core.planning.planner import Planner
                planner = Planner()
        self.planner = planner

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

    def execute_workflow(self, task: Any) -> Dict[str, Any]:
        """
        Executes a task end-to-end: plans steps, runs agents, and updates states.
        Supports both natural language strings and pre-planned ExecutionPlan models.

        Args:
            task: Task description string or a PlannerExecutionPlan instance.

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
        
        # Check if we received an already generated plan or need to plan it
        is_preplanned = isinstance(task, PlannerExecutionPlan)
        
        if is_preplanned:
            execution_plan = task
            project_title = execution_plan.project_title
            steps = execution_plan.tasks
            execution_stages = execution_plan.execution_stages
            task_str = project_title
            
            self.memory.add_log(
                "workflow", f"Starting workflow execution using pre-planned ExecutionPlan: '{project_title}'"
            )
        else:
            self.memory.add_log(
                "workflow", f"Starting workflow execution for task: '{task}'"
            )
            
            # Step 1: Autonomous Planning
            set_correlation_context(
                task_id=session_id, workflow_id=session_id, agent_name="planner"
            )
            
            try:
                # Try generating plan via new autonomous IPlanner engine
                execution_plan = self.planner.plan(task)
                project_title = execution_plan.project_title
                steps = execution_plan.tasks
                execution_stages = execution_plan.execution_stages
                task_str = task
            except Exception as e:
                # Fallback to the old planner agent for backward compatibility
                logger.warning(f"Autonomous planning engine failed, falling back to agent planner: {e}")
                planner = self.agents.get("planner")
                if not planner:
                    err = f"Planning failed: both autonomous planner and legacy agent are unavailable. Error: {e}"
                    logger.error(err)
                    self.memory.add_log("workflow", err, level="ERROR")
                    self.memory.update_status("failed")
                    metrics_collector.record_workflow_run(
                        time.time() - start_time, success=False
                    )
                    return self.memory.show()
                
                try:
                    plan_data = planner.run(task)
                    validated_plan = PlannerPlan(**plan_data)
                    validation_errors = self.validate_plan_graph(validated_plan)
                    if validation_errors:
                        raise ValueError(f"Legacy plan validation failed: {validation_errors}")
                    
                    project_title = plan_data.get("project_title", "System Plan")
                    raw_steps = plan_data.get("steps", [])
                    steps = []
                    for rs in raw_steps:
                        steps.append(
                            PlanningTask(
                                task_id=rs.get("step_id", 0),
                                name=rs.get("title", rs.get("name", "Unnamed Step")),
                                description=rs.get("description", ""),
                                assigned_agent=rs.get("assigned_agent", "developer"),
                                dependencies=rs.get("dependencies", []),
                                priority=rs.get("priority", "medium"),
                            )
                        )
                    
                    # Compute execution stages via DAGScheduler
                    from core.queue.scheduler import PlanDAG, PlanStep as SchedulerPlanStep, DAGScheduler
                    dag_steps = []
                    for s in steps:
                        dag_steps.append(
                            SchedulerPlanStep(
                                step_id=s.task_id,
                                dependencies=s.dependencies,
                                assigned_agent=s.assigned_agent,
                                description=s.description
                            )
                        )
                    plan_dag = PlanDAG(steps=dag_steps)
                    scheduler = DAGScheduler()
                    execution_stages = scheduler.build_execution_plan(plan_dag)
                    task_str = task
                except Exception as old_e:
                    err = f"Planning failed (both planning systems failed): {str(old_e)}"
                    logger.error(err)
                    self.memory.add_log("workflow", err, level="ERROR")
                    self.memory.update_status("failed")
                    metrics_collector.record_workflow_run(
                        time.time() - start_time, success=False
                    )
                    return self.memory.show()

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
                step_id=s.task_id,
                name=s.name,
                description=s.description,
                assigned_agent=s.assigned_agent,
                dependencies=s.dependencies,
                priority=s.priority,
            )
            serialized_steps.append(step_model.model_dump())

        self.memory.set("workflow_steps", serialized_steps)
        self.memory.add_log(
            "workflow",
            f"Plan generated: {project_title}. Total steps: {len(steps)}",
        )

        self.memory.add_log(
            "workflow",
            f"Generated execution plan with {len(execution_stages)} sequential stages."
        )
        for stage in execution_stages:
            self.memory.add_log(
                "workflow",
                f"Stage {stage.stage_id} holds independent nodes: {stage.independent_nodes} (dependencies count: {stage.dependency_count})"
            )

        # Step 3: Sequential stage-by-stage execution
        step_by_id = {s["step_id"]: s for s in serialized_steps}

        for stage in execution_stages:
            self.memory.add_log(
                "workflow",
                f"Executing Stage {stage.stage_id}..."
            )
            for step_id in stage.independent_nodes:
                step_dict = step_by_id[step_id]
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
                        f"Overall Goal: {task_str}\n"
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
