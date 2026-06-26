import importlib
import pkgutil
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, Field

from core.logging import get_logger

logger = get_logger("AgentRegistry")

# =====================================================================
# Custom Exception Definitions
# =====================================================================

class RegistryError(Exception):
    """Base exception class for all Agent Registry operations."""
    pass

class AgentNotFoundError(RegistryError):
    """Raised when looking up or creating an agent that is not registered."""
    pass

class DuplicateAgentError(RegistryError):
    """Raised when registering an agent with a name that already exists."""
    pass

class AgentRegistrationError(RegistryError):
    """Raised when registration details or inputs validation fail."""
    pass

# =====================================================================
# Models
# =====================================================================

class AgentMetadata(BaseModel):
    """
    Structured data describing an agent's identity, role, and capabilities.
    """
    name: str = Field(..., description="Unique code name for the agent registry index.")
    role: str = Field(..., description="Display role name (e.g. Senior Software Engineer).")
    description: str = Field(..., description="Description of the agent's responsibilities.")
    capabilities: List[str] = Field(
        default_factory=list, 
        description="Functional capability tags (e.g. ['research', 'scrapers'])."
    )
    tools: List[str] = Field(
        default_factory=list, 
        description="Explicit tools names this agent can access."
    )
    input_schema: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional input schema for structured execution."
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional output schema for structured execution."
    )

# =====================================================================
# AgentRegistry Singleton Class
# =====================================================================

class AgentRegistry:
    """
    Thread-safe registry for agent metadata and class definitions.
    Prevents circular imports and dynamic state leakage by instantiating
    fresh agent instances on demand.
    """
    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "AgentRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self) -> None:
        # Prevent re-initialization of self._registry dictionary in singleton instances
        if hasattr(self, "_initialized"):
            return
            
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._initialized = True
        self._registry_lock = threading.Lock()
        logger.debug("AgentRegistry singleton initialized.")

    def register(self, metadata: AgentMetadata, class_ref: Type[Any]) -> None:
        """
        Registers an agent class definition with its metadata description.
        
        Args:
            metadata: Pydantic metadata schema.
            class_ref: Python class reference of the agent.
            
        Raises:
            DuplicateAgentError: If an agent with the same name is already registered.
            AgentRegistrationError: If class_ref is missing or metadata is invalid.
        """
        if not metadata.name:
            raise AgentRegistrationError("Agent registry name key cannot be empty.")
        if not class_ref:
            raise AgentRegistrationError(f"Class reference for agent '{metadata.name}' cannot be None.")

        with self._registry_lock:
            if metadata.name in self._registry:
                raise DuplicateAgentError(
                    f"Failed to register agent '{metadata.name}': Name is already in use by "
                    f"class {self._registry[metadata.name]['class'].__name__}."
                )

            self._registry[metadata.name] = {
                "metadata": metadata,
                "class": class_ref,
                "registered_at": datetime.now(timezone.utc).replace(tzinfo=None)
            }
            logger.info(f"Agent '{metadata.name}' ({class_ref.__name__}) successfully registered.")

    def unregister(self, name: str) -> None:
        """
        Unregisters an agent by its unique code name.
        """
        with self._registry_lock:
            if name in self._registry:
                del self._registry[name]
                logger.info(f"Agent '{name}' was unregistered.")
            else:
                logger.warning(f"Unregister failed: Agent '{name}' was not found.")

    def get_agent_class(self, name: str) -> Type[Any]:
        """
        Retrieves the registered class reference of an agent.
        
        Raises:
            AgentNotFoundError: If name is not registered.
        """
        with self._registry_lock:
            entry = self._registry.get(name)
            if not entry:
                raise AgentNotFoundError(f"Agent '{name}' is not registered in the system.")
            return entry["class"]

    def get_agent_metadata(self, name: str) -> AgentMetadata:
        """
        Retrieves the registered metadata definition of an agent.
        
        Raises:
            AgentNotFoundError: If name is not registered.
        """
        with self._registry_lock:
            entry = self._registry.get(name)
            if not entry:
                raise AgentNotFoundError(f"Agent '{name}' is not registered in the system.")
            return entry["metadata"]

    def create_agent(self, name: str, memory: Any, **kwargs: Any) -> Any:
        """
        Instantiates a fresh agent instance from the registered class reference.
        Passes the metadata role and memory directly to the constructor.
        
        Args:
            name: Dynamic registration name.
            memory: SharedMemory context reference.
            **kwargs: Additional parameters passed to constructor.
            
        Returns:
            The instantiated agent object.
            
        Raises:
            AgentNotFoundError: If agent name is not found in registry.
        """
        with self._registry_lock:
            entry = self._registry.get(name)
            if not entry:
                raise AgentNotFoundError(f"Agent '{name}' is not registered in the system.")
            
            agent_class = entry["class"]
            metadata = entry["metadata"]
            
        logger.debug(f"Instantiating fresh instance of agent '{name}' ({agent_class.__name__}).")
        
        # Instantiate agent using registered class constructor
        try:
            return agent_class(
                role=metadata.role,
                memory=memory,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to instantiate agent '{name}': {str(e)}")
            raise RegistryError(f"Failed to instantiate agent '{name}': {str(e)}") from e

    def list_agents(self) -> List[AgentMetadata]:
        """
        Lists metadata for all registered agents.
        """
        with self._registry_lock:
            return [entry["metadata"] for entry in self._registry.values()]

    def find_by_capability(self, capability: str) -> List[Tuple[Type[Any], AgentMetadata]]:
        """
        Finds all registered agents supporting a specific capability tag.
        """
        with self._registry_lock:
            results = []
            for entry in self._registry.values():
                metadata = entry["metadata"]
                if capability in metadata.capabilities:
                    results.append((entry["class"], metadata))
            return results

    def find_by_tool(self, tool_name: str) -> List[Tuple[Type[Any], AgentMetadata]]:
        """
        Finds all registered agents carrying access permissions for a specific tool.
        """
        with self._registry_lock:
            results = []
            for entry in self._registry.values():
                metadata = entry["metadata"]
                if tool_name in metadata.tools:
                    results.append((entry["class"], metadata))
            return results

# =====================================================================
# Decorator Function
# =====================================================================

def register_agent(
    name: str,
    role: str,
    description: str,
    capabilities: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    input_schema: Optional[Dict[str, Any]] = None,
    output_schema: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Class decorator to automatically register an agent class with AgentRegistry.
    
    Example:
        @register_agent(
            name="researcher",
            role="Research Specialist",
            description="Performs filesystem and web research.",
            capabilities=["research", "scanning"],
            tools=["dir_scanner", "web_search"],
            input_schema={"type": "object", "properties": {"task": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"result": {"type": "string"}}}
        )
        class ResearchAgent(BaseAgent):
            ...
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        metadata = AgentMetadata(
            name=name,
            role=role,
            description=description,
            capabilities=capabilities or [],
            tools=tools or [],
            input_schema=input_schema,
            output_schema=output_schema
        )
        AgentRegistry().register(metadata, cls)
        return cls
    return decorator

# =====================================================================
# Autodiscovery Loader
# =====================================================================

def discover_agents(directory_path: Optional[str] = None) -> None:
    """
    Recursively scans the agents directory, dynamically loading module files
    to execute their decorators and populate the AgentRegistry.
    
    Args:
        directory_path: Absolute directory containing agent modules.
                        Defaults to project standard 'agents/' directory.
    """
    if directory_path is None:
        # Determine standard agents folder relative to this file
        directory_path = str(Path(__file__).parent.parent / "agents")

    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        logger.error(f"Discovery skipped: Directory '{directory_path}' is invalid.")
        return

    logger.info(f"Scanning folder for agent autodiscovery: '{path.resolve()}'")

    # Add parent folder of agents package to sys.path to enable standard module loading
    parent_str = str(path.parent.resolve())
    if parent_str not in sys.path:
        sys.path.insert(0, parent_str)

    modules_imported = 0
    package_name = path.name
    # Iterate through all packages and python files in the directory
    for _, module_name, is_pkg in pkgutil.iter_modules([str(path.resolve())]):
        # Skip pycache and standard base files
        if module_name.startswith("__") or module_name in ("base_agent", "manager"):
            continue
            
        full_module_path = f"{package_name}.{module_name}"
        try:
            logger.debug(f"Importing discovered agent module: {full_module_path}")
            # Import triggers module parsing, which executes register_agent decorators
            importlib.import_module(full_module_path)
            modules_imported += 1
        except Exception as e:
            logger.error(f"Failed to load discovered module {full_module_path}: {str(e)}")
            
    logger.info(f"Autodiscovery complete. Loaded {modules_imported} module files.")
