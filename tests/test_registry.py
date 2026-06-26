import unittest
from pathlib import Path
import tempfile
import sys
import shutil

from core.registry import (
    AgentRegistry, AgentMetadata, register_agent, discover_agents,
    DuplicateAgentError, AgentNotFoundError, AgentRegistrationError
)

# Mock class matching BaseAgent signature
class MockBaseAgent:
    def __init__(self, role: str, memory: Any, custom_arg: str = "default"):
        self.role = role
        self.memory = memory
        self.custom_arg = custom_arg

class MockMemory:
    pass

class TestAgentRegistry(unittest.TestCase):
    def setUp(self):
        # Reset singleton registry state for each test
        self.registry = AgentRegistry()
        self.registry._registry.clear()

    def test_singleton_behavior(self):
        another_registry = AgentRegistry()
        self.assertIs(self.registry, another_registry)

    def test_manual_registration(self):
        metadata = AgentMetadata(
            name="test_agent",
            role="Tester",
            description="Testing agent",
            capabilities=["test"],
            tools=["test_tool"]
        )
        self.registry.register(metadata, MockBaseAgent)
        
        # Verify stored correctly
        self.assertEqual(len(self.registry.list_agents()), 1)
        self.assertEqual(self.registry.get_agent_class("test_agent"), MockBaseAgent)
        self.assertEqual(self.registry.get_agent_metadata("test_agent").role, "Tester")

    def test_duplicate_registration_raises_error(self):
        metadata = AgentMetadata(
            name="duplicate_agent",
            role="First",
            description="First desc"
        )
        self.registry.register(metadata, MockBaseAgent)

        metadata_dup = AgentMetadata(
            name="duplicate_agent",
            role="Second",
            description="Second desc"
        )
        with self.assertRaises(DuplicateAgentError):
            self.registry.register(metadata_dup, MockBaseAgent)

    def test_missing_fields_raises_error(self):
        with self.assertRaises(AgentRegistrationError):
            metadata = AgentMetadata(name="", role="Tester", description="Desc")
            self.registry.register(metadata, MockBaseAgent)
            
        with self.assertRaises(AgentRegistrationError):
            metadata = AgentMetadata(name="test", role="Tester", description="Desc")
            self.registry.register(metadata, None)

    def test_decorator_registration(self):
        @register_agent(
            name="decorator_agent",
            role="Decorator Tester",
            description="Testing decorator",
            capabilities=["decorate"],
            tools=["brush"]
        )
        class DecoratedAgent(MockBaseAgent):
            pass

        self.assertEqual(self.registry.get_agent_class("decorator_agent"), DecoratedAgent)
        meta = self.registry.get_agent_metadata("decorator_agent")
        self.assertEqual(meta.role, "Decorator Tester")
        self.assertIn("decorate", meta.capabilities)
        self.assertIn("brush", meta.tools)

    def test_fresh_instance_creation(self):
        metadata = AgentMetadata(
            name="instance_agent",
            role="Instantiator",
            description="Instance test"
        )
        self.registry.register(metadata, MockBaseAgent)

        memory1 = MockMemory()
        memory2 = MockMemory()

        agent1 = self.registry.create_agent("instance_agent", memory1, custom_arg="first_run")
        agent2 = self.registry.create_agent("instance_agent", memory2, custom_arg="second_run")

        # Assert correct class and values
        self.assertIsInstance(agent1, MockBaseAgent)
        self.assertEqual(agent1.role, "Instantiator")
        self.assertIs(agent1.memory, memory1)
        self.assertEqual(agent1.custom_arg, "first_run")

        # Assert fresh instances are created (different memory addresses)
        self.assertIsNot(agent1, agent2)
        self.assertEqual(agent2.custom_arg, "second_run")

    def test_lookup_by_capability_and_tool(self):
        meta1 = AgentMetadata(
            name="agent_a", role="A", description="A", 
            capabilities=["math", "logic"], tools=["calc"]
        )
        meta2 = AgentMetadata(
            name="agent_b", role="B", description="B", 
            capabilities=["logic", "science"], tools=["lab"]
        )
        
        self.registry.register(meta1, MockBaseAgent)
        self.registry.register(meta2, MockBaseAgent)

        # Query capabilities
        math_agents = self.registry.find_by_capability("math")
        logic_agents = self.registry.find_by_capability("logic")
        
        self.assertEqual(len(math_agents), 1)
        self.assertEqual(math_agents[0][1].name, "agent_a")
        
        self.assertEqual(len(logic_agents), 2)
        logic_names = [a[1].name for a in logic_agents]
        self.assertIn("agent_a", logic_names)
        self.assertIn("agent_b", logic_names)

        # Query tools
        calc_agents = self.registry.find_by_tool("calc")
        self.assertEqual(len(calc_agents), 1)
        self.assertEqual(calc_agents[0][1].name, "agent_a")

    def test_dynamic_discovery(self):
        # Create a temporary directory structure mimicking agents
        temp_dir = tempfile.mkdtemp()
        sys.path.insert(0, temp_dir)
        
        try:
            agents_pkg = Path(temp_dir) / "test_agents"
            agents_pkg.mkdir()
            
            # Write a mock base agent module
            (agents_pkg / "__init__.py").write_text("", encoding="utf-8")
            
            # Write a registerable agent module
            agent_code = """
from core.registry import register_agent

class FakeBase:
    def __init__(self, role, memory):
        self.role = role
        self.memory = memory

@register_agent(
    name="fake_discovered_agent",
    role="Fake Discovered",
    description="Mock discovered agent for unit tests."
)
class DiscoveredAgent(FakeBase):
    pass
"""
            (agents_pkg / "discovered_agent.py").write_text(agent_code, encoding="utf-8")
            
            # Discover agents in the temporary directory
            discover_agents(str(agents_pkg))
            
            # Assert that the decorated agent was dynamically imported and registered
            self.assertIn("fake_discovered_agent", [a.name for a in self.registry.list_agents()])
            agent_instance = self.registry.create_agent("fake_discovered_agent", MockMemory())
            self.assertEqual(agent_instance.role, "Fake Discovered")
            
        finally:
            # Clean up temp directories
            sys.path.remove(temp_dir)
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()
