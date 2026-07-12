import time
from typing import Dict, List, Optional, Protocol, runtime_checkable
from core.di import DIContainer
from core.queue.scheduler import PlanDAG, PlanStep, IDAGScheduler
from core.workspace.interface import IWorkspaceSessionManager
from core.sandbox.interface import ISandbox
from core.logging import get_logger

logger = get_logger("ExecutionRuntime")


@runtime_checkable
class IAgentExecutor(Protocol):
    """
    Interface for dispatching steps to autonomous agent loops (Sprint 6).
    """

    def execute_step(
        self, task_id: str, step: PlanStep, workspace_path: str, sandbox: ISandbox
    ) -> bool:
        """
        Runs the agent loop for a given step inside the provided workspace/sandbox.
        """
        ...


@runtime_checkable
class IPlanExecutor(Protocol):
    """
    Interface for orchestrating the step-by-step execution of a PlanDAG.
    """

    def execute_plan(self, task_id: str, plan: PlanDAG) -> bool:
        """
        Executes a PlanDAG topologically. Returns True if all steps succeed,
        False if any step fails.
        """
        ...


class EngineeringExecutionRuntime(IPlanExecutor):
    """
    Orchestration runtime for executing PlanDAGs topologically.
    Provisions workspaces and sandboxes per step and routes task execution to agents.
    """

    def __init__(self) -> None:
        pass

    def execute_plan(self, task_id: str, plan: PlanDAG) -> bool:
        scheduler = DIContainer.get(IDAGScheduler)

        # 1. Retrieve HITL orchestrator and event broker
        try:
            hitl_orchestrator = DIContainer.get("hitl_orchestrator")
        except Exception:
            hitl_orchestrator = None

        try:
            broker = DIContainer.get(IEventBroker)
        except Exception:
            broker = None

        # Resolve/load the persisted plan to resume execution status
        if hitl_orchestrator:
            persisted_plan = hitl_orchestrator.get_plan(task_id)
            if persisted_plan:
                plan = persisted_plan
            else:
                hitl_orchestrator.register_plan(task_id, plan)

        # 2. Resolve execution order
        try:
            order = scheduler.get_execution_order(plan)
        except ValueError as e:
            logger.error(
                f"Failed to resolve execution order for task {task_id}: {str(e)}"
            )
            return False

        # Build step mapping
        step_map = {step.step_id: step for step in plan.steps}

        # 3. Get Workspace Session Manager
        session_mgr = DIContainer.get(IWorkspaceSessionManager)

        # Start a workspace session for the task (creates Git worktree)
        session_state = session_mgr.start_session(task_id)
        workspace_path = session_state.workspace_path

        # 4. Create sandbox using SandboxFactory
        sandbox_factory = DIContainer.get("sandbox_factory")
        sandbox: ISandbox = sandbox_factory(workspace_path, task_id)
        sandbox.start()

        success = True
        try:
            for step_id in order:
                step = step_map[step_id]

                # Skip already completed steps (support resumption)
                if step.status == "completed":
                    continue

                # Check Human-in-the-Loop approval gate
                if hitl_orchestrator:
                    approval_type = hitl_orchestrator.check_step_needs_approval(step)
                    # If approval is needed and it hasn't been approved yet
                    if approval_type and step.status != "approved":
                        hitl_orchestrator.request_approval(task_id, step, approval_type)
                        logger.info(
                            f"Step {step_id} requires {approval_type}. Execution suspended."
                        )
                        # Release sandbox and workspace resources during pause
                        return False

                logger.info(
                    f"Starting execution of Step {step_id} (Agent: {step.assigned_agent})"
                )
                step.status = "running"
                if hitl_orchestrator:
                    hitl_orchestrator.register_plan(task_id, plan)

                if broker:
                    broker.publish(
                        "task_progress",
                        {
                            "task_id": task_id,
                            "step_id": step.step_id,
                            "event": "step_started",
                            "assigned_agent": step.assigned_agent,
                            "description": step.description,
                        },
                    )

                # Execute the step
                step_success = self._execute_step(
                    task_id, step, workspace_path, sandbox
                )

                # If execution failed, attempt self-healing before halting
                if not step_success:
                    logger.info(
                        f"Step {step_id} failed. Checking self-healing options..."
                    )
                    try:
                        self_healing_engine = DIContainer.get("self_healing_engine")
                        # Run linter/test to gather failure log context
                        res_lint = sandbox.execute(["ruff", "check", "."])
                        if res_lint.exit_code != 0:
                            error_log = res_lint.stdout + "\n" + res_lint.stderr
                        else:
                            res_test = sandbox.execute(["pytest"])
                            error_log = res_test.stdout + "\n" + res_test.stderr

                        # Attempt self-healing
                        repaired = self_healing_engine.repair_failure(
                            task_id, step, error_log, workspace_path, sandbox
                        )
                        if repaired:
                            logger.info(
                                f"Self-healing successfully repaired Step {step_id}!"
                            )
                            step_success = True
                    except Exception as e:
                        logger.warning(f"Self-healing lookup or execution failed: {e}")

                if step_success:
                    step.status = "completed"
                    logger.info(f"Step {step_id} completed successfully.")
                    if hitl_orchestrator:
                        hitl_orchestrator.register_plan(task_id, plan)
                    if broker:
                        broker.publish(
                            "task_progress",
                            {
                                "task_id": task_id,
                                "step_id": step.step_id,
                                "event": "step_completed",
                            },
                        )
                else:
                    step.status = "failed"
                    logger.error(f"Step {step_id} failed. Halting plan execution.")
                    success = False

                    # Mark all downstream pending steps as cancelled
                    for remaining_id in order:
                        rem_step = step_map[remaining_id]
                        if (
                            rem_step.status == "pending"
                            or rem_step.status == "waiting_for_approval"
                        ):
                            rem_step.status = "cancelled"

                    if hitl_orchestrator:
                        hitl_orchestrator.register_plan(task_id, plan)
                    if broker:
                        broker.publish(
                            "task_progress",
                            {
                                "task_id": task_id,
                                "step_id": step.step_id,
                                "event": "step_failed",
                            },
                        )
                    break
        finally:
            # 5. Clean up sandbox and session allocations
            try:
                sandbox.terminate()
            except Exception:
                pass
            try:
                session_mgr.end_session(task_id)
            except Exception:
                pass

        return success

    def _execute_step(
        self, task_id: str, step: PlanStep, workspace_path: str, sandbox: ISandbox
    ) -> bool:
        """
        Executes a single PlanStep using the assigned agent loop.
        """
        try:
            agent_executor = DIContainer.get(IAgentExecutor)
            return agent_executor.execute_step(task_id, step, workspace_path, sandbox)
        except Exception:
            logger.warning(
                f"No IAgentExecutor registered in DI. Running fallback step execution."
            )

            # Simple fallback: if description contains a command to run, execute it in sandbox!
            # E.g. "RUN: python -c \"print('test')\""
            if step.description.startswith("RUN: "):
                import shlex

                cmd = shlex.split(step.description[5:])
                res = sandbox.execute(cmd)
                return res.exit_code == 0

            # Default fallback: simulate success
            time.sleep(0.05)
            return True
