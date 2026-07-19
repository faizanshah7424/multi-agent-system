from typing import Any, Dict, List, Protocol, Set, runtime_checkable
from pydantic import BaseModel, Field
from core.models.profiles import AgentProfileRegistry


class PlanStep(BaseModel):
    """
    Schema representing a single scheduled step in an execution DAG.
    """

    step_id: int
    dependencies: List[int] = Field(default_factory=list)
    assigned_agent: str
    status: str = "pending"
    description: str = Field(default="", description="Task detail description.")
    files: List[str] = Field(
        default_factory=list, description="Files affected by this step."
    )


class PlanDAG(BaseModel):
    """
    Data model encapsulating the set of PlanSteps that form the directed acyclic graph.
    """

    steps: List[PlanStep]


class ExecutionStage(BaseModel):
    """
    Schema representing a set of steps that can be executed concurrently in a DAG stage.
    """

    stage_id: int
    independent_nodes: List[int] = Field(default_factory=list)
    dependency_count: int = 0
    downstream_nodes: List[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """
    Schema representing the ordered list of execution stages for a DAG.
    """

    stages: List[ExecutionStage]


@runtime_checkable
class IDAGScheduler(Protocol):
    """
    Interface for resolving task sequencing and parallel step scheduling.
    """

    def validate_dag(self, plan: PlanDAG) -> List[str]:
        """
        Runs DFS cycle-detection and reference checks to validate plan safety.
        """
        ...

    def get_execution_order(self, plan: PlanDAG) -> List[int]:
        """
        Resolves steps using a topological sort (Kahn's or DFS).
        """
        ...

    def build_execution_plan(self, plan: PlanDAG) -> List[ExecutionStage]:
        """
        Builds a layered execution plan grouping independent steps into stages.
        """
        ...


class DAGScheduler(IDAGScheduler):
    """
    Concrete implementation of IDAGScheduler.
    Performs validation checks and resolves topological execution orders.
    """

    def validate_dag(self, plan: PlanDAG) -> List[str]:
        errors: List[str] = []
        step_ids = [s.step_id for s in plan.steps]

        # 1. Unique step IDs
        if len(step_ids) != len(set(step_ids)):
            errors.append("Step IDs must be unique.")

        step_map = {s.step_id: s for s in plan.steps}

        # Load valid agents from registry configuration
        try:
            profile_reg = AgentProfileRegistry()
            valid_agents = set(profile_reg.list_profiles())
        except Exception:
            valid_agents = {
                "planner",
                "researcher",
                "developer",
                "reviewer",
                "repository_engineer",
                "product_builder",
            }

        for step in plan.steps:
            # 2. Check assigned agent validity
            if step.assigned_agent.lower() not in valid_agents:
                errors.append(
                    f"Step {step.step_id}: Assigned agent '{step.assigned_agent}' is not a registered agent profile."
                )

            # 3. Check dependency references
            for dep in step.dependencies:
                if dep not in step_map:
                    errors.append(
                        f"Step {step.step_id} has invalid dependency on non-existent step {dep}."
                    )
                elif dep == step.step_id:
                    errors.append(f"Step {step.step_id} cannot depend on itself.")

        # 4. Cycle detection (DFS back-edge trace)
        if not errors:
            adj: Dict[int, List[int]] = {s.step_id: [] for s in plan.steps}
            for step in plan.steps:
                for dep in step.dependencies:
                    adj[dep].append(step.step_id)

            visited: Dict[int, int] = {}  # 0: unvisited, 1: visiting, 2: visited

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

            for s_id in step_ids:
                if visited.get(s_id, 0) == 0:
                    if has_cycle(s_id):
                        errors.append(
                            "PlanDAG contains circular dependencies (is not a valid DAG)."
                        )
                        break

        return errors

    def get_execution_order(self, plan: PlanDAG) -> List[int]:
        """
        Resolves steps using Kahn's algorithm for topological sorting.
        """
        errors = self.validate_dag(plan)
        if errors:
            raise ValueError(
                f"Cannot resolve execution order. Invalid DAG: {'; '.join(errors)}"
            )

        step_ids = [s.step_id for s in plan.steps]
        step_map = {s.step_id: s for s in plan.steps}

        # Build adjacency list and in-degree counts
        adj: Dict[int, List[int]] = {s_id: [] for s_id in step_ids}
        in_degree: Dict[int, int] = {s_id: 0 for s_id in step_ids}

        for step in plan.steps:
            for dep in step.dependencies:
                adj[dep].append(step.step_id)
                in_degree[step.step_id] += 1

        # Queue nodes with in-degree 0
        queue = [s_id for s_id in step_ids if in_degree[s_id] == 0]
        # Sort queue to ensure deterministic behavior (lower step IDs run first when independent)
        queue.sort()

        order = []
        while queue:
            u = queue.pop(0)
            order.append(u)
            for v in adj.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
            # Re-sort remaining to maintain deterministic order
            queue.sort()

        if len(order) != len(step_ids):
            raise ValueError(
                "PlanDAG contains circular dependencies (is not a valid DAG)."
            )

        return order

    def build_execution_plan(self, plan: PlanDAG) -> List[ExecutionStage]:
        """
        Groups independent nodes in the DAG into execution stages, returning a list of ExecutionStage.
        Each stage contains:
        - stage_id: int (1-indexed stage sequence)
        - independent_nodes: List[int] (sorted step_ids in this stage)
        - dependency_count: int (total direct dependency references in this stage)
        - downstream_nodes: List[int] (sorted unique step_ids depending directly on this stage's nodes)
        """
        # Validate the DAG first
        errors = self.validate_dag(plan)
        if errors:
            raise ValueError(
                f"Cannot build execution plan. Invalid DAG: {'; '.join(errors)}"
            )

        step_ids = [s.step_id for s in plan.steps]
        step_map = {s.step_id: s for s in plan.steps}

        # Build downstream adjacency list
        adj_downstream: Dict[int, List[int]] = {s_id: [] for s_id in step_ids}
        for step in plan.steps:
            for dep in step.dependencies:
                adj_downstream[dep].append(step.step_id)

        # Compute topological layers using a modified Kahn's algorithm
        in_degree = {s.step_id: len(s.dependencies) for s in plan.steps}
        queue = [s_id for s_id in step_ids if in_degree[s_id] == 0]
        queue.sort()

        layers = {s_id: 1 for s_id in step_ids}

        while queue:
            u = queue.pop(0)
            for v in adj_downstream.get(u, []):
                layers[v] = max(layers[v], layers[u] + 1)
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
            queue.sort()

        # Group step_ids by layer
        layer_to_nodes: Dict[int, List[int]] = {}
        for s_id, layer_val in layers.items():
            layer_to_nodes.setdefault(layer_val, []).append(s_id)

        stages: List[ExecutionStage] = []
        for l_val in sorted(layer_to_nodes.keys()):
            nodes = sorted(layer_to_nodes[l_val])
            
            # Compute total dependency count for nodes in this stage
            dep_count = sum(len(step_map[n].dependencies) for n in nodes)

            # Compute sorted unique downstream nodes
            downstream = sorted(list(set(
                v for n in nodes for v in adj_downstream.get(n, [])
            )))

            stages.append(
                ExecutionStage(
                    stage_id=l_val,
                    independent_nodes=nodes,
                    dependency_count=dep_count,
                    downstream_nodes=downstream,
                )
            )

        return stages

