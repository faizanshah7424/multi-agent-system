import unittest
from unittest.mock import MagicMock
from core.di import DIContainer
from config import settings
from core.schemas import (
    ContextBudgetConfig,
    RetrievedCodeChunk,
)
from core.queue.scheduler import PlanStep
from core.context.prompt_builder import PromptBuilder
from core.context.retrieval import RetrievalPipeline
from core.queue.agent_executor import AgentExecutor, AgentDecision



class TestPromptBuilderAndRetrievalIntegration(unittest.TestCase):
    def setUp(self) -> None:
        from core.di_setup import bootstrap_di
        bootstrap_di()
        self.prompt_builder = DIContainer.get(PromptBuilder)
        self.retrieval_pipeline = DIContainer.get(RetrievalPipeline)
        # Reset global settings to default to avoid state leakage from other tests
        settings.context_isolation_start_tag = "<source_context>"
        settings.context_isolation_end_tag = "</source_context>"


    def test_di_registration(self) -> None:
        # Check that PromptBuilder and RetrievalPipeline are in the container
        self.assertTrue(isinstance(self.prompt_builder, PromptBuilder))
        self.assertTrue(isinstance(self.retrieval_pipeline, RetrievalPipeline))

    def test_prompt_builder_assembly_order(self) -> None:
        config = ContextBudgetConfig()
        chunks = [
            RetrievedCodeChunk(
                file_path="core/database.py",
                content="def test(): pass",
                score=0.9,
                start_line=1,
                end_line=2,
            )
        ]

        prompt = self.prompt_builder.build_prompt(
            system_instructions="SYSTEM_INSTRUCTION_TEXT",
            history=["Thought 1", "Action 1"],
            retrieved_chunks=chunks,
            user_request="USER_REQUEST_TEXT",
            tool_outputs="TOOL_OUTPUT_TEXT",
            constraints="CONSTRAINTS_TEXT",
            config=config,
            model_name="gpt-4o",
        )

        # Verify exact order of headings
        idx_sys = prompt.find("=== SYSTEM INSTRUCTIONS ===")
        idx_hist = prompt.find("=== CONVERSATION HISTORY ===")
        idx_ret = prompt.find("=== RETRIEVED SOURCE CONTEXT ===")
        idx_req = prompt.find("=== CURRENT USER REQUEST ===")
        idx_tool = prompt.find("=== TOOL OUTPUTS ===")
        idx_const = prompt.find("=== EXECUTION CONSTRAINTS ===")

        # Assert sections exist
        self.assertNotEqual(idx_sys, -1)
        self.assertNotEqual(idx_hist, -1)
        self.assertNotEqual(idx_ret, -1)
        self.assertNotEqual(idx_req, -1)
        self.assertNotEqual(idx_tool, -1)
        self.assertNotEqual(idx_const, -1)

        # Assert mandatory sequence ordering
        self.assertTrue(idx_sys < idx_hist < idx_ret < idx_req < idx_tool < idx_const)

    def test_context_prioritization_and_deduplication(self) -> None:
        config = ContextBudgetConfig()
        
        # 1. Duplicate chunk (same file and line)
        # 2. Lower score chunk
        # 3. High score chunk
        chunks = [
            RetrievedCodeChunk(
                file_path="file.py", content="content 1", score=0.5, start_line=1, end_line=5
            ),
            RetrievedCodeChunk(
                file_path="file.py", content="content 1", score=0.5, start_line=1, end_line=5
            ),
            RetrievedCodeChunk(
                file_path="file2.py", content="content 2", score=0.9, start_line=10, end_line=15
            ),
        ]

        prompt = self.prompt_builder.build_prompt(
            system_instructions="sys",
            history=[],
            retrieved_chunks=chunks,
            user_request="req",
            tool_outputs="",
            constraints="",
            config=config,
            model_name="gpt-4o",
        )

        # Verify that only one copy of file.py line 1 exists
        self.assertEqual(prompt.count('file="file.py"'), 1)
        # Verify that file2.py (higher score) appears before file.py
        idx_file2 = prompt.find('file="file2.py"')
        idx_file1 = prompt.find('file="file.py"')
        self.assertTrue(idx_file2 < idx_file1)

    def test_context_budget_trimming(self) -> None:
        # Define config with extremely small retrieved chunks budget (e.g., 20 tokens)
        config = ContextBudgetConfig(
            retrieved_chunks_pct=0.0001, # Allocation will be extremely small (0 or 1 token)
            total_budget=1000
        )

        chunks = [
            RetrievedCodeChunk(
                file_path="large_chunk.py",
                content="def long_method():\n" + "    pass\n" * 100,
                score=0.9,
                start_line=1,
                end_line=100,
            )
        ]

        prompt = self.prompt_builder.build_prompt(
            system_instructions="SYSTEM_STAYS",
            history=[],
            retrieved_chunks=chunks,
            user_request="USER_REQUEST_STAYS",
            tool_outputs="",
            constraints="",
            config=config,
            model_name="gpt-4o",
        )

        # The large chunk must be dropped entirely because it exceeds budget
        self.assertNotIn("large_chunk.py", prompt)
        # System instructions and user request must remain intact
        self.assertIn("SYSTEM_STAYS", prompt)
        self.assertIn("USER_REQUEST_STAYS", prompt)

    def test_empty_retrieval_handling(self) -> None:
        config = ContextBudgetConfig()
        prompt = self.prompt_builder.build_prompt(
            system_instructions="sys",
            history=[],
            retrieved_chunks=[],
            user_request="req",
            tool_outputs="",
            constraints="",
            config=config,
            model_name="gpt-4o",
        )

        # Section should be omitted
        self.assertNotIn("=== RETRIEVED SOURCE CONTEXT ===", prompt)

    def test_isolation_wrapper_xml_generation(self) -> None:
        config = ContextBudgetConfig()
        chunks = [
            RetrievedCodeChunk(
                file_path="core/context/budget.py",
                content="class ContextBudgetManager:",
                score=0.95,
                start_line=120,
                end_line=121,
                symbol_name="ContextBudgetManager",
            )
        ]

        prompt = self.prompt_builder.build_prompt(
            system_instructions="sys",
            history=[],
            retrieved_chunks=chunks,
            user_request="req",
            tool_outputs="",
            constraints="",
            config=config,
            model_name="gpt-4o",
        )

        # Verify XML isolation wrap structure
        self.assertIn('<source_context file="core/context/budget.py" symbol="ContextBudgetManager" lines="120-121" sha256="', prompt)
        self.assertIn("class ContextBudgetManager:", prompt)
        self.assertIn("</source_context>", prompt)

    def test_agent_executor_integration(self) -> None:
        from core.queue.execution_runtime import IAgentExecutor
        executor = DIContainer.get(IAgentExecutor)

        task_id = "test_run_pipeline"
        
        step = PlanStep(
            step_id=1,
            assigned_agent="developer",
            description="Test query details",
            dependencies=[],
        )



        # Mock Model Provider generate_structured
        from core.models.interface import IModelProvider
        mock_model = MagicMock()
        mock_decision = AgentDecision(
            thought="I will respond directly.",
            action="respond",
            final_answer="Done",
        )
        mock_model.generate_structured.return_value = mock_decision
        DIContainer.register(IModelProvider, mock_model)


        sandbox = MagicMock()
        
        # Execute agent step
        success = executor.execute_step(task_id, step, "E:/multi-agent-system", sandbox)
        self.assertTrue(success)
        
        # Verify that prompt builder was queried
        mock_model.generate_structured.assert_called()
