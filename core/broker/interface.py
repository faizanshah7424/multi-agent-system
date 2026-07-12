from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class IEventBroker(Protocol):
    """
    Interface for real-time WebSocket messaging and Pub/Sub event streams.
    """

    def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publishes a message to all active subscribers on a channel.
        """
        ...

    def subscribe(self, channel: str, callback: Any) -> None:
        """
        Registers a callback handler for messages on a channel.
        """
        ...

    def unsubscribe(self, channel: str, callback: Any) -> None:
        """
        Removes a callback handler registration.
        """
        ...
