import json
from typing import Any, Dict, List
from agents.base_agent import BaseAgent
from config import settings
from core.llm import ask_llm_structured
from core.registry import register_agent
from core.schemas import PlannerPlan

@register_agent(
    name="planner",
    role="Project Planner",
    description="Analyzes goals and breaks them into structured steps.",
    capabilities=["planning", "sequencing"],
    tools=[]
)
class PlannerAgent(BaseAgent):
    """
    Agent responsible for analyzing tasks and breaking them down into a structured execution plan.
    """
    def __init__(self, role: str, memory: Any):
        super().__init__(
            role=role,
            memory=memory,
            model=settings.planner_model
        )

    def run(self, task: str) -> Dict[str, Any]:
        """
        Generates a structured project plan with sequential steps.
        
        Args:
            task: The overall objective.
            
        Returns:
            A dictionary containing the structured plan.
        """
        self.memory.add_log(self.role, f"Planning project steps for task: '{task}'")
        
        system_instruction = """You are the Project Planner.
Your job is to break down a software/content development task into a sequence of actionable steps.
Each step must be assigned to the most appropriate agent:
- 'researcher': For scanning directories, reading code, or gathering requirements/web info.
- 'developer': For writing or editing code, scripts, or APIs.
- 'reviewer': For reviewing code, checking styling, or inspecting logs.

You must respond in format matching the specified plan schema.
"""

        prompt = f"Create a structured execution plan for this objective:\n{task}"
        
        try:
            # Query the LLM with structured output schema constraint
            plan_obj = ask_llm_structured(
                prompt=prompt,
                model=self.model,
                response_schema=PlannerPlan,
                system_instruction=system_instruction,
                retries=1
            )
            
            plan_data = plan_obj.model_dump()
            
            # Save the raw text plan to memory (legacy compatibility)
            pretty_plan = f"Plan: {plan_data.get('project_title', 'System Plan')}\n"
            for step in plan_data.get("steps", []):
                pretty_plan += f"{step.get('step_id')}. [{step.get('assigned_agent').upper()}] {step.get('title')}: {step.get('description')} (Dependencies: {step.get('dependencies')}, Priority: {step.get('priority')})\n"
                
            self.memory.set("plan", pretty_plan)
            self.memory.set("structured_plan", plan_data)
            
            self.memory.add_log(self.role, "Project plan created successfully with native structured outputs.")
            return plan_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate project plan: {str(e)}")
            fallback_plan = {
                "project_title": "Fallback Execution Plan",
                "steps": [
                    {
                        "step_id": 1,
                        "title": "Initial Research",
                        "description": f"Gather details regarding the task: {task}",
                        "assigned_agent": "researcher",
                        "dependencies": [],
                        "priority": "high"
                    },
                    {
                        "step_id": 2,
                        "title": "Implementation",
                        "description": "Develop and write the required code or files.",
                        "assigned_agent": "developer",
                        "dependencies": [1],
                        "priority": "high"
                    },
                    {
                        "step_id": 3,
                        "title": "Code Review",
                        "description": "Validate the code and check for issues.",
                        "assigned_agent": "reviewer",
                        "dependencies": [2],
                        "priority": "medium"
                    }
                ]
            }
            self.memory.set("plan", "Fallback Plan: Research -> Develop -> Review")
            self.memory.set("structured_plan", fallback_plan)
            return fallback_plan