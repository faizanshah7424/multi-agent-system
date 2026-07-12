import json
from typing import Any, Dict, List, Optional
from core.llm import ask_llm, ask_llm_structured
from core.memory import SharedMemory
from core.schemas import AgentAction
from tools.base import BaseTool
from core.logging import get_logger


class BaseAgent:
    """
    Base class for all agents.
    Equips agents with thinking (LLM generation) and execution loops using registered tools.
    """

    def __init__(
        self,
        role: str,
        memory: SharedMemory,
        model: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
    ):
        self.role = role
        self.memory = memory
        self.model = model
        self.tools = tools or []
        self.tool_map = {t.name: t for t in self.tools}
        self.logger = get_logger(self.role.replace(" ", ""))

    def think(self, task: str) -> str:
        """
        Legacy/Simple query format. Formats a prompt and returns direct text.
        """
        prompt = f"""
        You are {self.role}

        Task:
        {task}
        """
        return ask_llm(prompt, model=self.model)

    def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """
        Executes a registered tool by name with safety checks.
        """
        if name not in self.tool_map:
            error_msg = (
                f"Error: Tool '{name}' is not registered/available for this agent."
            )
            self.memory.add_log(self.role, error_msg, level="ERROR")
            return error_msg

        tool = self.tool_map[name]
        self.memory.add_log(self.role, f"Calling tool '{name}' with arguments: {args}")

        try:
            result = tool.run(**args)
            return str(result)
        except Exception as e:
            err = f"Error executing tool '{name}': {str(e)}"
            self.logger.error(err)
            return err

    def run_task(self, task_description: str, max_iterations: int = 5) -> str:
        """
        Executes a task using a ReAct-style loop: Think -> Act -> Observe.
        Enforces native structured outputs to guarantee deterministic tool/answer responses.
        """
        self.memory.add_log(self.role, f"Running task: {task_description}")

        # Build description of tools
        tools_desc = ""
        if self.tools:
            tools_desc_lines = []
            for t in self.tools:
                schema_info = t.args_schema.model_json_schema() if t.args_schema else {}
                tools_desc_lines.append(
                    f"- {t.name}: {t.description}\n  Schema: {json.dumps(schema_info)}"
                )
            tools_desc = "\n".join(tools_desc_lines)
        else:
            tools_desc = "None"

        system_instruction = f"""You are the {self.role}.
You have access to the following tools:
{tools_desc}

You must solve the user's task step-by-step.
To interact, you MUST respond in format matching the specified AgentAction schema.
For a tool call: set action='call_tool', and provide 'tool' and 'arguments' fields.
For final response: set action='respond', and provide 'final_answer' field.

CRITICAL RULES:
1. You can only call tools listed above. If you don't need tools, return your "final_answer".
2. Maintain state across steps by reviewing the action history.
"""

        history: List[str] = [f"Initial Task: {task_description}"]

        for i in range(max_iterations):
            history_str = "\n\n".join(history)
            prompt = f"{history_str}\n\nWhat is your next action?"

            try:
                # Query LLM using structured output schema constraint
                response_data = ask_llm_structured(
                    prompt=prompt,
                    model=self.model,
                    response_schema=AgentAction,
                    system_instruction=system_instruction,
                    retries=1,
                )

                thought = response_data.thought
                action = response_data.action
                tool_name = response_data.tool
                tool_args = response_data.arguments or {}
                final_answer = response_data.final_answer

                self.memory.add_log(self.role, f"Thought (Step {i+1}): {thought}")

                if action == "respond" or final_answer is not None:
                    self.memory.add_log(self.role, f"Task completed successfully.")
                    return str(
                        final_answer or "Task execution finished without final_answer."
                    )

                if action == "call_tool" and tool_name:
                    result = self.call_tool(tool_name, tool_args)
                    # Truncate long results for prompt readability
                    trunc_result = (
                        result[:1000] + "\n...[truncated]"
                        if len(result) > 1000
                        else result
                    )

                    history.append(
                        f"Step {i+1} Action:\nCalled tool '{tool_name}' with {tool_args}\n"
                        f"Step {i+1} Observation:\n{trunc_result}"
                    )
                else:
                    err_msg = f"Error: AgentAction specified action '{action}' but missing required parameters (tool_name='{tool_name}')."
                    self.memory.add_log(self.role, err_msg, level="WARNING")
                    history.append(f"Step {i+1} Action failed: {err_msg}")

            except Exception as e:
                err = f"Unexpected error in agent execution step: {str(e)}"
                self.logger.error(err)
                self.memory.add_log(self.role, err, level="ERROR")
                return f"Agent failure: {str(e)}"

        return f"Error: Agent exceeded maximum iterations ({max_iterations}) without resolving the task."
