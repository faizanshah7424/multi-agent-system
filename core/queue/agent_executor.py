import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.di import DIContainer
from core.models.interface import IModelProvider, ModelParameters
from core.models.profiles import AgentProfileRegistry
from core.registry.interface import IPromptLibrary
from core.queue.scheduler import PlanStep
from core.sandbox.interface import ISandbox
from core.queue.execution_runtime import IAgentExecutor
from core.broker.interface import IEventBroker
from core.logging import get_logger

logger = get_logger("AgentExecutor")


class AgentDecision(BaseModel):
    """
    Schema representing a single ReAct step decision by the executing agent.
    """

    thought: str = Field(..., description="Your current reasoning and plan.")
    action: str = Field(
        ...,
        description="Action to take: 'execute_command', 'read_file', 'write_file', or 'respond'.",
    )
    command: Optional[List[str]] = Field(
        default=None, description="Tokens of command to run in the sandbox."
    )
    file_path: Optional[str] = Field(
        default=None, description="Path of target file relative to workspace."
    )
    content: Optional[str] = Field(
        default=None, description="Content to write or update."
    )
    final_answer: Optional[str] = Field(
        default=None, description="Final response when task is completed."
    )


class AgentExecutor(IAgentExecutor):
    """
    Concrete Agent Executor implementing ReAct execution loops using DI bindings.
    """

    def execute_step(
        self, task_id: str, step: PlanStep, workspace_path: str, sandbox: ISandbox
    ) -> bool:
        model_provider = DIContainer.get(IModelProvider)
        prompt_library = DIContainer.get(IPromptLibrary)

        # 1. Resolve agent profile
        try:
            profile_reg = AgentProfileRegistry()
            profile = profile_reg.get_profile(step.assigned_agent)
        except Exception:
            # Safe fallback if registry/json is missing or corrupt
            profile = None

        # Determine prompt template
        template_name = (
            profile.prompt_template_name if profile else f"{step.assigned_agent}_v1"
        )

        # 2. Format prompt dynamically mapping required variables
        var_mappings = {
            "task_description": step.description,
            "target_files": ", ".join(step.files) if step.files else "None",
            "conventions": "Write clean code, follow standard formatting, and run pytest verification.",
            "query": step.description,
            "code_context": f"Sandbox workspace absolute path: {workspace_path}",
            "original_code": f"Code files inside: {workspace_path}",
            "proposed_changes": step.description,
            "repo_path": workspace_path,
            "index_status": "Successfully indexed",
            "specifications": step.description,
            "tech_stack": "FastAPI, SQL, Docker, Python 3",
            "user_request": step.description,
        }

        system_instruction = prompt_library.get_prompt(template_name, var_mappings)

        # 3. Initialize ReAct loop parameters and DI components
        max_iterations = 5
        params = ModelParameters(
            temperature=profile.temperature if profile else 0.2,
            max_tokens=profile.max_tokens if profile else 4096,
        )

        from core.context.prompt_builder import PromptBuilder
        from core.context.retrieval import RetrievalPipeline
        from core.schemas import ContextBudgetConfig
        from config import settings

        prompt_builder = DIContainer.get(PromptBuilder)
        retrieval_pipeline = DIContainer.get(RetrievalPipeline)

        history_thoughts_actions: List[str] = []
        last_tool_output: str = ""

        logger.info(
            f"Starting ReAct loop for step {step.step_id} ({step.assigned_agent})"
        )

        for iteration in range(max_iterations):
            # 1. Dynamically retrieve relevant codebase context chunks
            retrieval_query = step.description
            if history_thoughts_actions:
                latest_thought = [t for t in history_thoughts_actions if t.startswith("Thought:")]
                if latest_thought:
                    retrieval_query = f"{step.description} {latest_thought[-1]}"

            retrieved_chunks = retrieval_pipeline.retrieve(
                task_id=task_id,
                query=retrieval_query,
                workspace_path=workspace_path
            )

            # 2. Build structured prompt in mandatory order respecting token budgets
            budget_config = ContextBudgetConfig()
            model_name = getattr(profile, "model_name", settings.default_model) if profile else settings.default_model

            constraints = (
                "You must respond in a format matching the AgentDecision schema.\n"
                "Write clean code, follow standard formatting, and run pytest verification."
            )

            compiled_prompt = prompt_builder.build_prompt(
                system_instructions=system_instruction,
                history=history_thoughts_actions,
                retrieved_chunks=retrieved_chunks,
                user_request=step.description,
                tool_outputs=last_tool_output,
                constraints=constraints,
                config=budget_config,
                model_name=model_name
            )

            try:
                # Query LLM for next decision
                decision: AgentDecision = model_provider.generate_structured(
                    prompt=compiled_prompt,
                    schema=AgentDecision,
                    system_instruction=system_instruction,
                    params=params,
                )

            except Exception as e:
                logger.error(
                    f"ReAct LLM query failed at iteration {iteration}: {str(e)}"
                )
                return False

            logger.info(f"Iteration {iteration} Thought: {decision.thought}")
            history_thoughts_actions.append(f"Thought: {decision.thought}")

            # Publish event to broker
            try:
                broker = DIContainer.get(IEventBroker)
            except Exception:
                broker = None
            if broker:
                broker.publish(
                    "agent_reasoning",
                    {
                        "task_id": task_id,
                        "step_id": step.step_id,
                        "iteration": iteration,
                        "thought": decision.thought,
                        "action": decision.action,
                        "target": decision.file_path
                        or (decision.command and " ".join(decision.command))
                        or "",
                    },
                )

            # 4. Route Actions
            history_thoughts_actions.append(f"Action: {decision.action} " + (decision.file_path or (decision.command and " ".join(decision.command)) or ""))

            if decision.action == "respond":
                logger.info(f"Agent resolved step: {decision.final_answer}")
                return True

            elif decision.action == "execute_command":
                if not decision.command:
                    last_tool_output = "Error: execute_command chosen but command tokens were missing."
                    continue
                logger.info(f"Executing sandbox command: {' '.join(decision.command)}")
                res = sandbox.execute(decision.command)
                last_tool_output = (
                    f"Command executed: {' '.join(decision.command)}\n"
                    f"Exit Code: {res.exit_code}\n"
                    f"Stdout: {res.stdout}\n"
                    f"Stderr: {res.stderr}"
                )
                if res.exit_code != 0:
                    logger.warning(f"Sandbox command failed with code {res.exit_code}")

            elif decision.action == "read_file":
                if not decision.file_path:
                    last_tool_output = "Error: read_file chosen but file_path was missing."
                    continue
                target_path = Path(workspace_path) / decision.file_path
                if not target_path.exists():
                    last_tool_output = f"Result of read_file {decision.file_path}: File not found."
                    continue
                try:
                    content = target_path.read_text(encoding="utf-8")
                    last_tool_output = f"Result of read_file {decision.file_path}:\n{content}"
                except Exception as e:
                    last_tool_output = f"Result of read_file {decision.file_path}: Error {str(e)}"

            elif decision.action == "write_file":
                if not decision.file_path or decision.content is None:
                    last_tool_output = "Error: write_file chosen but file_path or content was missing."
                    continue
                target_path = Path(workspace_path) / decision.file_path
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_text(decision.content, encoding="utf-8")
                    last_tool_output = f"Result of write_file {decision.file_path}: Success"
                    logger.info(f"Wrote file inside workspace: {decision.file_path}")
                except Exception as e:
                    last_tool_output = f"Result of write_file {decision.file_path}: Error {str(e)}"

            else:
                last_tool_output = f"Error: Unknown action type '{decision.action}' chosen."

        logger.error(
            f"Agent failed to resolve task within {max_iterations} iterations."
        )
        return False
