import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.models.interface import IModelProvider, ModelParameters
from core.models.providers import (
    GeminiProvider, OpenAIProvider, AnthropicProvider,
    ModelProviderRegistry, ModelCapabilities, calculate_usd_cost,
    on_usage_tracked
)
from core.models.session import (
    Conversation, Message, ToolCall, ToolResult, Usage, Cost, SessionMetadata
)
from core.models.profiles import AgentProfile, AgentProfileRegistry
from core.registry.interface import IToolRegistry, ISkillRegistry, IPromptLibrary, ToolDefinition
from core.registry.tool_registry import ToolRegistry
from core.registry.skill_registry import SkillRegistry
from core.registry.prompt_library import PromptLibrary

class TestAIOrchestration(unittest.TestCase):
    def setUp(self) -> None:
        ModelProviderRegistry.clear()
        bootstrap_di()
        self.prompts_dir = Path(__file__).parent.parent.parent / "core" / "prompts"
        self.test_skill_path = Path(__file__).parent.parent / "resources" / "skills" / "test_skill.md"

    def tearDown(self) -> None:
        ModelProviderRegistry.clear()
        on_usage_tracked.clear()

    def test_di_registrations(self) -> None:
        # Check that container registers all Sprint 3 implementations
        self.assertTrue(isinstance(DIContainer.get(IModelProvider), GeminiProvider))
        self.assertTrue(isinstance(DIContainer.get(IToolRegistry), ToolRegistry))
        self.assertTrue(isinstance(DIContainer.get(ISkillRegistry), SkillRegistry))
        self.assertTrue(isinstance(DIContainer.get(IPromptLibrary), PromptLibrary))

    def test_model_provider_registry(self) -> None:
        gemini = GeminiProvider("gemini-2.5-flash")
        openai = OpenAIProvider("gpt-4o")
        anthropic = AnthropicProvider("claude-3-5-sonnet")
        
        caps_gemini = ModelCapabilities(
            model_name="gemini-2.5-flash",
            max_context_window=1000000,
            supports_structured_json=True,
            supports_streaming=True
        )
        
        ModelProviderRegistry.register("gemini", gemini, caps_gemini)
        ModelProviderRegistry.register("openai", openai, ModelCapabilities(model_name="gpt-4o"))
        ModelProviderRegistry.register("anthropic", anthropic, ModelCapabilities(model_name="claude-3-5-sonnet"))
        
        self.assertEqual(ModelProviderRegistry.get_provider("gemini"), gemini)
        self.assertEqual(ModelProviderRegistry.get_capabilities("gemini"), caps_gemini)
        self.assertIn("openai", ModelProviderRegistry.list_providers())

    def test_cost_calculation_and_hooks(self) -> None:
        # Test Cost math
        cost = calculate_usd_cost("gemini-2.5-flash", 1000, 2000)
        # input: 0.075 / 1M = 0.000075, output: 0.30 / 1M = 0.0006. Total = 0.000675
        self.assertAlmostEqual(cost, 0.000675)

        # Hook tracking
        hook_run = []
        def my_hook(model, p_tokens, c_tokens, cost_val):
            hook_run.append((model, p_tokens, c_tokens))
            
        on_usage_tracked.append(my_hook)
        
        # Trigger hooks (mimic generate completion callback)
        for h in on_usage_tracked:
            h("gemini-2.5-flash", 100, 200, 0.0001)
            
        self.assertEqual(len(hook_run), 1)
        self.assertEqual(hook_run[0], ("gemini-2.5-flash", 100, 200))

    def test_prompt_library(self) -> None:
        lib = PromptLibrary(str(self.prompts_dir))
        
        # Load developer_v1 and test substitution
        vars_dict = {
            "task_description": "Implement authentication routing",
            "target_files": "api/routes.py",
            "conventions": "Use snake_case for filenames"
        }
        prompt = lib.get_prompt("developer_v1", vars_dict)
        self.assertIn("Implement authentication routing", prompt)
        self.assertIn("Use snake_case for filenames", prompt)

        # Mismatch validation check (missing variables)
        with self.assertRaises(ValueError):
            lib.get_prompt("developer_v1", {"task_description": "incomplete"})

    def test_tool_registry(self) -> None:
        registry = ToolRegistry()
        
        class MockTool:
            pass
            
        tool_inst = MockTool()
        
        # Register a tool restricted to developer role and write capability
        registry.register_tool(
            name="write_file",
            tool_instance=tool_inst,
            capabilities=["write"],
            permission_level="WRITE",
            allowed_roles=["Developer"]
        )
        
        # 1. Developer with write capability can get it
        tools = registry.get_agent_tools("Developer", ["read", "write"])
        self.assertIn(tool_inst, tools)
        
        # 2. Researcher without write capability cannot get it
        tools2 = registry.get_agent_tools("Researcher", ["read"])
        self.assertNotIn(tool_inst, tools2)
        
        # 3. Developer without write capability cannot get it
        tools3 = registry.get_agent_tools("Developer", ["read"])
        self.assertNotIn(tool_inst, tools3)

    def test_skill_registry(self) -> None:
        registry = SkillRegistry()
        registry.register_skill("test_skill", str(self.test_skill_path))
        
        # Verify instructions content
        instructions = registry.get_skill_instructions("test_skill")
        self.assertIn("This is a test procedure", instructions)
        
        # Verify frontmatter parsing
        meta = registry.get_skill_metadata("test_skill")
        self.assertEqual(meta["version"], "1.0.2")
        self.assertEqual(meta["category"], "tests")
        self.assertEqual(meta["description"], "Test skill markdown document.")

    def test_agent_profiles(self) -> None:
        # Load from config on disk
        config_path = Path(__file__).parent.parent.parent / "core" / "config" / "agent_profiles.json"
        registry = AgentProfileRegistry(str(config_path))
        
        profile = registry.get_profile("planner")
        self.assertEqual(profile.role, "Planner")
        self.assertIn("read_only", profile.permissions)
        self.assertEqual(profile.temperature, 0.2)
        self.assertEqual(profile.model, "gemini-2.5-flash")

    def test_session_serialization(self) -> None:
        # Create Conversation Session Objects and verify serialization properties
        msg = Message(role="user", content="Hello Model")
        meta = SessionMetadata(
            session_id="session-123-uuid",
            model_name="gemini-2.5-flash",
            provider_name="Gemini",
            temperature=0.2,
            max_tokens=2048
        )
        conv = Conversation(
            session_id="session-123-uuid",
            messages=[msg],
            metadata=meta,
            total_usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            total_cost=Cost(input_cost_usd=0.0001, output_cost_usd=0.0002, total_cost_usd=0.0003)
        )
        
        # Dump to dict
        conv_dict = conv.model_dump()
        self.assertEqual(conv_dict["session_id"], "session-123-uuid")
        self.assertEqual(conv_dict["messages"][0]["role"], "user")
        self.assertEqual(conv_dict["total_usage"]["total_tokens"], 15)
        
        # Reload
        reloaded = Conversation(**conv_dict)
        self.assertEqual(reloaded.total_cost.total_cost_usd, 0.0003)
