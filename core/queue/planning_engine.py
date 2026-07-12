from core.di import DIContainer
from core.models.interface import IModelProvider, ModelParameters
from core.models.providers import calculate_usd_cost
from core.registry.interface import IPromptLibrary
from core.queue.scheduler import PlanDAG, IDAGScheduler


class PlanningEngine:
    """
    Planning Engine utilizing PromptLibrary and ModelProvider to generate
    and validate topological task DAG execution plans.
    """

    def __init__(self) -> None:
        pass

    def generate_plan(self, user_request: str, repo_report: str) -> PlanDAG:
        """
        Loads the planner prompt, queries the model provider for a structured PlanDAG,
        and validates the generated execution tree against topological dependency constraints.
        """
        # 1. Retrieve dependencies from DIContainer
        model_provider = DIContainer.get(IModelProvider)
        prompt_library = DIContainer.get(IPromptLibrary)
        scheduler = DIContainer.get(IDAGScheduler)

        # 2. Format the prompt using versioned template
        prompt = prompt_library.get_prompt(
            "planner_v1", {"user_request": user_request, "tech_stack": repo_report}
        )

        system_instruction = (
            "You are the master Planner Agent. Analyze the codebase details and the user request, "
            "and produce a logical task execution PlanDAG containing the required steps and dependencies. "
            "All step IDs must be unique integers. Dependencies must refer only to other step IDs in the list."
        )

        params = ModelParameters(temperature=0.1, max_tokens=4096, retries=2)

        # 3. Generate structured output conforming to PlanDAG schema
        plan_dag = model_provider.generate_structured(
            prompt=prompt,
            schema=PlanDAG,
            system_instruction=system_instruction,
            params=params,
        )

        # 4. Validate the generated DAG
        errors = scheduler.validate_dag(plan_dag)
        if errors:
            raise ValueError(
                f"Generated execution plan failed DAG validation: {'; '.join(errors)}"
            )

        return plan_dag
