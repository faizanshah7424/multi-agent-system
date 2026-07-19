import unittest
from unittest.mock import MagicMock
from pydantic import ValidationError

from config import settings
from core.schemas import (
    ContextBudgetConfig,
    RetrievedCodeChunk,
    ContextBudgetAllocation,
    ContextTelemetry,
)
from core.context.budget import (
    TokenizerRegistry,
    TiktokenTokenizer,
    GeminiTokenizer,
    BalancedBudgetStrategy,
    ContextBudgetManager,
    ContextIsolationWrapper,
    DatabaseConfigurator,
)


class TestContextBudgetAndOptimization(unittest.TestCase):
    def setUp(self) -> None:
        TokenizerRegistry.clear()

    def test_lazy_tokenizer_registry(self) -> None:
        # Check lazy loading: registry should be empty on start
        self.assertEqual(len(TokenizerRegistry._instances), 0)

        # Retrieve a gemini tokenizer
        gemini_tk = TokenizerRegistry.get_tokenizer("gemini-2.5-flash")
        self.assertTrue(isinstance(gemini_tk, GeminiTokenizer))
        self.assertEqual(len(TokenizerRegistry._instances), 1)

        # Retrieve an openai tokenizer
        openai_tk = TokenizerRegistry.get_tokenizer("gpt-4o")
        self.assertTrue(isinstance(openai_tk, TiktokenTokenizer))
        self.assertEqual(len(TokenizerRegistry._instances), 2)

        # Verify cached instance reuse
        gemini_tk_2 = TokenizerRegistry.get_tokenizer("gemini-2.5-flash")
        self.assertIs(gemini_tk, gemini_tk_2)

    def test_tokenizer_interface_capabilities(self) -> None:
        gemini_tk = TokenizerRegistry.get_tokenizer("gemini-2.5-pro")
        self.assertEqual(gemini_tk.model_name(), "gemini-2.5-pro")
        self.assertEqual(gemini_tk.max_context_window(), 2000000)
        self.assertEqual(gemini_tk.max_output_tokens(), 8192)
        self.assertTrue(gemini_tk.supports_tool_calling())
        self.assertFalse(gemini_tk.supports_reasoning())
        self.assertTrue(gemini_tk.supports_multimodal())

        openai_tk = TokenizerRegistry.get_tokenizer("gpt-4o")
        self.assertEqual(openai_tk.model_name(), "gpt-4o")
        self.assertEqual(openai_tk.max_context_window(), 128000)
        self.assertEqual(openai_tk.max_output_tokens(), 4096)
        self.assertTrue(openai_tk.supports_tool_calling())
        self.assertFalse(openai_tk.supports_reasoning())
        self.assertTrue(openai_tk.supports_multimodal())

    def test_tokenizer_reasoning_capability(self) -> None:
        reasoning_tk = TokenizerRegistry.get_tokenizer("o1-preview")
        self.assertTrue(reasoning_tk.supports_reasoning())

    def test_balanced_budget_strategy_allocation(self) -> None:
        config = ContextBudgetConfig(total_budget=100000)
        strategy = BalancedBudgetStrategy()
        tokenizer = TokenizerRegistry.get_tokenizer("gemini-2.5-flash")

        allocation = strategy.allocate(config, tokenizer, 500, 250)

        # Check calculated boundaries based on percentages
        self.assertEqual(allocation.system_prompt, 5000)      # 5%
        self.assertEqual(allocation.reserved_response, 10000) # 10%
        self.assertEqual(allocation.history, 25000)           # 25%
        self.assertEqual(allocation.file_focus, 25000)        # 25%
        self.assertEqual(allocation.retrieved_chunks, 20000)  # 20%
        self.assertEqual(allocation.tool_outputs, 10000)      # 10%
        self.assertEqual(allocation.scratchpad, 5000)          # 5%
        self.assertEqual(allocation.total_allocated, 100000)

        # Check telemetry
        self.assertEqual(allocation.telemetry.model, "gemini-2.5-flash")
        self.assertEqual(allocation.telemetry.compression_ratio, 2.0)
        self.assertEqual(allocation.telemetry.allocated_tokens, 100000)
        self.assertEqual(allocation.telemetry.remaining_tokens, 0)

    def test_immutable_budget_allocation(self) -> None:
        config = ContextBudgetConfig(total_budget=100000)
        strategy = BalancedBudgetStrategy()
        tokenizer = TokenizerRegistry.get_tokenizer("gpt-4o")

        allocation = strategy.allocate(config, tokenizer, 0, 0)

        # Verify mutation raises ValidationError/TypeError
        with self.assertRaises((ValidationError, TypeError)):
            # Attempts to assign attribute value to frozen pydantic model should fail
            allocation.history = 99999

    def test_stateless_budget_manager_trimming(self) -> None:
        # History messages to trim
        messages = [
            {"role": "user", "content": "Message 1 (short)"},
            {"role": "assistant", "content": "Message 2 (medium length text)"},
            {"role": "user", "content": "Message 3 (longer text block to allocate)"},
        ]
        
        # Total tokens calculated roughly: Message 1 (3), Message 2 (5), Message 3 (7) = 15 tokens.
        # Trim budget set to 10 tokens: should keep only Message 3.
        trimmed_history, original_tokens = ContextBudgetManager.compress_history(
            messages, budget=10, model_name="gpt-4o"
        )

        self.assertEqual(len(trimmed_history), 1)
        self.assertEqual(trimmed_history[0]["content"], "Message 3 (longer text block to allocate)")
        self.assertTrue(original_tokens > 0)

    def test_configurable_isolation_wrapper(self) -> None:
        chunk = RetrievedCodeChunk(
            file_path="core/database.py",
            content="def get_db_session(): pass",
            score=0.95,
            start_line=10,
            end_line=12,
        )

        # 1. Test Default tag wrapper
        settings.context_isolation_start_tag = "<source_context>"
        settings.context_isolation_end_tag = "</source_context>"
        res = ContextIsolationWrapper.wrap_chunk(chunk)
        self.assertTrue(res.startswith('<source_context file="core/database.py" lines="10-12">'))
        self.assertTrue(res.endswith("</source_context>"))
        self.assertIn("def get_db_session(): pass", res)

        # 2. Test Custom tag wrapper configuration settings
        settings.context_isolation_start_tag = "<isolated_block>"
        settings.context_isolation_end_tag = "</isolated_block>"
        res_custom = ContextIsolationWrapper.wrap_chunk(chunk)
        self.assertTrue(res_custom.startswith('<isolated_block file="core/database.py" lines="10-12">'))
        self.assertTrue(res_custom.endswith("</isolated_block>"))

    def test_database_configurator_wal(self) -> None:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        # Run database configuration
        DatabaseConfigurator.configure_connection(mock_connection, "sqlite")

        # Verify WAL mode pragmas are called
        mock_cursor.execute.assert_any_call("PRAGMA journal_mode=WAL")
        mock_cursor.execute("PRAGMA synchronous=NORMAL")
        mock_cursor.execute("PRAGMA foreign_keys=ON")
        mock_cursor.close.assert_called_once()
