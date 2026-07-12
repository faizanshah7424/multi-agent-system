from typing import Dict, Type, TypeVar, Any

T = TypeVar("T")

class DIContainer:
    """
    A simple, runtime-safe Dependency Injection container to decouple 
    interfaces from concrete provider implementations.
    """
    _registry: Dict[Type[Any], Any] = {}

    @classmethod
    def register(cls, interface: Type[T], implementation: T) -> None:
        """
        Registers a concrete implementation instance for a given interface type.
        """
        cls._registry[interface] = implementation

    @classmethod
    def get(cls, interface: Type[T]) -> T:
        """
        Retrieves the registered implementation instance for a given interface type.
        
        Raises:
            KeyError: If the interface has not been registered.
        """
        if interface not in cls._registry:
            raise KeyError(f"Interface {interface.__name__} is not registered in DIContainer.")
        return cls._registry[interface]

    @classmethod
    def clear(cls) -> None:
        """
        Clears the registered mappings (useful for test isolation).
        """
        cls._registry.clear()
