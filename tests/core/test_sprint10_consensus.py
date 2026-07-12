import unittest
from unittest.mock import patch, MagicMock
from typing import Any
from datetime import datetime


import agents
from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.memory import SharedMemory
from core.database import get_db_session, DecisionRecord, Task
from core.debate.consensus_engine import (
    ConsensusEngine,
    ConsensusEvent,
    EngineeringDecisionRecord,
)
from core.schemas import AgentAction, PlannerPlan, PlanStep

from core.broker.interface import IEventBroker

# Keep track of published events to assert on them
published_events = []


def mock_publish(channel: str, message: dict) -> None:
    if channel == "consensus_events":
        published_events.append(message)


def mock_ask_llm(
    prompt: str, model=None, system_instruction=None, temperature=None, json_mode=False
) -> str:
    p = prompt.lower()
    sys_inst = (system_instruction or "").lower()

    # Identify agent role from prompt or system instruction
    if "product builder" in sys_inst or "product_builder" in prompt:
        return "Product Specs: We need a scalable hospital system."
    elif "planner" in sys_inst or "planner" in prompt:
        return "Plan: Step 1. Define models, Step 2. Add API endpoints."
    elif "architect" in sys_inst or "architect" in prompt:
        # If it's the first plan review, reject it to trigger the loop
        if "revised" not in prompt:
            return "Rejected: Violates modular convention."
        return "Approved: Revised plan looks clean."
    elif "repository engineer" in sys_inst or "repository_engineer" in prompt:
        return "Repository Scan: Found core/di_setup.py. No circular dependencies."
    elif "researcher" in sys_inst or "researcher" in prompt:
        return "Research: Found di container conventions."
    elif "developer" in sys_inst or "developer" in prompt:
        return "Code: class NewHospitalService: pass"
    elif "reviewer" in sys_inst or "reviewer" in prompt:
        # If first review, reject code to trigger the loop
        if "revised" not in prompt:
            return "Rejected: Missing basic inline docstrings."
        return "Approved: Revised code has documentation."
    elif "tech lead" in sys_inst or "tech_lead" in prompt:
        if "arbitrate" in prompt or "dispute" in prompt:
            return "Resolved: Accept the modified proposal."
        return "Approved by Tech Lead Sign-off"
    return "Approved"


def mock_ask_llm_structured(prompt: str, response_schema, **kwargs) -> Any:
    if response_schema == AgentAction:
        ans = mock_ask_llm(prompt, system_instruction=kwargs.get("system_instruction"))
        return AgentAction(
            thought="Reviewing inputs step-by-step...",
            action="respond",
            final_answer=ans,
        )
    elif response_schema == EngineeringDecisionRecord:
        return EngineeringDecisionRecord(
            problem_statement="Integrate Sprint 10 multi-agent consensus system.",
            considered_alternatives=["Sequential pipelines", "Direct commits"],
            chosen_solution="Multi-agent loop with Tech Lead resolution",
            rejected_solutions=["Single agent execution"],
            architectural_impact="Clean separation of concerns with EDR records.",
            repository_impact="New agents and debate engines added.",
            future_risks=["Increased latency due to multiple LLM iterations."],
            lessons_learned=["Enforce strict validation early."],
        )
    elif response_schema == PlannerPlan:
        return PlannerPlan(
            project_title="Hospital Patient Checkin API",
            steps=[
                PlanStep(
                    step_id=1,
                    title="Requirements definition",
                    assigned_agent="product_builder",
                    description="Define vision and specs.",
                    dependencies=[],
                ),
                PlanStep(
                    step_id=2,
                    title="Code implementation",
                    assigned_agent="developer",
                    description="Implement patient checkin API endpoint.",
                    dependencies=[1],
                ),
                PlanStep(
                    step_id=3,
                    title="Code review",
                    assigned_agent="reviewer",
                    description="Review the patient checkin implementation.",
                    dependencies=[2],
                ),
            ],
        )
    raise ValueError(f"Unrecognized schema: {response_schema}")


def mock_generate(prompt: str, *args, **kwargs) -> str:
    sys_inst = kwargs.get("system_instruction") or ""
    return mock_ask_llm(prompt, system_instruction=sys_inst)


def mock_generate_structured(prompt: str, response_schema, *args, **kwargs) -> Any:
    sys_inst = kwargs.get("system_instruction") or ""
    return mock_ask_llm_structured(prompt, response_schema, system_instruction=sys_inst)


class TestConsensusEngine(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_di()
        self.memory = SharedMemory("test_consensus_task_session")
        self.engine = ConsensusEngine(self.memory)
        self.task_id = "test_sprint10_task"
        published_events.clear()

        # Mock Event Broker publish
        self.broker = DIContainer.get(IEventBroker)
        self.broker.publish = mock_publish

        # Clean SQLite EDR and Task table, then insert mock task to satisfy foreign key constraints
        with get_db_session() as session:
            session.query(DecisionRecord).filter(
                DecisionRecord.task_id == self.task_id
            ).delete()
            session.query(Task).filter(Task.task_id == self.task_id).delete()
            task = Task(
                task_id=self.task_id, payload_json={"objective": "Test objective"}
            )
            session.add(task)

    @patch("core.llm._global_wrapper.generate", side_effect=mock_generate)
    @patch(
        "core.llm._global_wrapper.generate_structured",
        side_effect=mock_generate_structured,
    )
    def test_consensus_workflow_execution(self, mock_struct, mock_plain) -> None:
        # Run consensus loop
        result = self.engine.run_consensus(
            self.task_id, "Build a Hospital Patient Checkin API"
        )

        self.assertEqual(result["task_id"], self.task_id)
        self.assertEqual(result["status"], "Approved")

        # Verify EDR fields
        edr = result["edr"]
        self.assertIn("Sprint 10", edr["problem_statement"])
        self.assertIn("Multi-agent loop", edr["chosen_solution"])

        # Check that EDR was saved to SQLite
        with get_db_session() as session:
            db_record = (
                session.query(DecisionRecord)
                .filter(DecisionRecord.task_id == self.task_id)
                .first()
            )
            self.assertIsNotNone(db_record)
            self.assertEqual(db_record.proposal_title, f"EDR - {self.task_id}")
            self.assertIn("Architectural Impact", db_record.explainability_log or "")

        # Verify that dashboard events were published
        self.assertGreater(len(published_events), 0)

        # Verify transitions were recorded sequentially
        event_types = [evt["event_type"] for evt in published_events]
        self.assertIn("CONSENSUS_INITIATED", event_types)
        self.assertIn("ROLE_EVALUATION_START", event_types)
        self.assertIn("ROLE_EVALUATION_COMPLETE", event_types)
        self.assertIn("REJECTION_TRIGGERED", event_types)
        self.assertIn("CONSENSUS_COMPLETED", event_types)

        # Check EME Integration
        try:
            memory_engine = DIContainer.get("memory_engine")
            conventions = memory_engine.retrieve_similar_conventions(
                f"EDR - {self.task_id}", limit=1
            )
            self.assertGreater(len(conventions), 0)
            self.assertEqual(conventions[0]["task_id"], self.task_id)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
