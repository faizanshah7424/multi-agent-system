from typing import List
from core.planning.planning_models import PlanningTask
from core.queue.scheduler import ExecutionStage, PlanDAG, PlanStep, DAGScheduler


class TaskGraph:
    """
    Graph representation of decomposed planning tasks.
    Enforces validation checks and computes topological execution stages.
    """

    def __init__(self, tasks: List[PlanningTask]) -> None:
        self.tasks = tasks

    def validate(self) -> List[str]:
        """
        Runs validation checks including cycles, duplicate IDs, self-dependencies,
        missing dependency references, and empty plans.
        """
        errors = []

        if not self.tasks:
            errors.append("Execution plan contains no tasks (empty workflow).")
            return errors

        task_ids = [t.task_id for t in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            errors.append("Task IDs must be unique.")

        task_map = {t.task_id: t for t in self.tasks}

        for task in self.tasks:
            # Self-dependency and non-existent task checks
            for dep in task.dependencies:
                if dep not in task_map:
                    errors.append(
                        f"Task {task.task_id} has invalid dependency on non-existent task {dep}."
                    )
                elif dep == task.task_id:
                    errors.append(f"Task {task.task_id} cannot depend on itself.")

        # Cycle detection using Depth-First Search (DFS)
        if not errors:
            adj = {t_id: [] for t_id in task_ids}
            for task in self.tasks:
                for dep in task.dependencies:
                    adj[dep].append(task.task_id)

            visited = {}  # 0: unvisited, 1: visiting, 2: visited

            def has_cycle(u: int) -> bool:
                visited[u] = 1
                for v in adj.get(u, []):
                    if visited.get(v, 0) == 1:
                        return True
                    elif visited.get(v, 0) == 0:
                        if has_cycle(v):
                            return True
                visited[u] = 2
                return False

            for t_id in task_ids:
                if visited.get(t_id, 0) == 0:
                    if has_cycle(t_id):
                        errors.append(
                            "Task graph contains dependency cycles (is not a valid DAG)."
                        )
                        break

        return errors

    def get_execution_stages(self) -> List[ExecutionStage]:
        """
        Resolves execution stages utilizing Kahn's layer grouping algorithm.
        """
        dag_steps = []
        for task in self.tasks:
            dag_steps.append(
                PlanStep(
                    step_id=task.task_id,
                    dependencies=task.dependencies,
                    assigned_agent=task.assigned_agent,
                    description=task.description,
                    files=task.files,
                )
            )

        plan_dag = PlanDAG(steps=dag_steps)
        scheduler = DAGScheduler()
        return scheduler.build_execution_plan(plan_dag)
