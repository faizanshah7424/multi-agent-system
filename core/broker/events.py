import threading
from typing import Any, Dict, List
from core.broker.interface import IEventBroker
from core.logging import get_logger

logger = get_logger("EventBroker")


class WebSocketEventBroker(IEventBroker):
    """
    Concrete Thread-Safe Event Broker facilitating real-time WebSocket messaging
    and in-memory pub/sub topic channels.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Any]] = {}
        self._lock = threading.Lock()

    def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publishes a message to all active subscribers on a channel.
        """
        logger.info(f"Publishing to channel '{channel}': {message}")
        with self._lock:
            callbacks = list(self._subscribers.get(channel, []))

        for callback in callbacks:
            try:
                # Trigger callback dynamically
                # Run callback asynchronously in a daemon thread to prevent blocking publishers
                t = threading.Thread(
                    target=self._safe_execute_callback,
                    args=(callback, message),
                    name="BrokerCallbackThread",
                )
                t.daemon = True
                t.start()
            except Exception as e:
                logger.error(f"Failed to trigger callback for channel '{channel}': {e}")

    def _safe_execute_callback(self, callback: Any, message: Dict[str, Any]) -> None:
        try:
            callback(message)
        except Exception as e:
            logger.error(f"Error in subscriber callback execution: {e}")

    def subscribe(self, channel: str, callback: Any) -> None:
        """
        Registers a callback handler for messages on a channel.
        """
        with self._lock:
            if channel not in self._subscribers:
                self._subscribers[channel] = []
            if callback not in self._subscribers[channel]:
                self._subscribers[channel].append(callback)
        logger.info(f"Subscribed callback to channel '{channel}'")

    def unsubscribe(self, channel: str, callback: Any) -> None:
        """
        Removes a callback handler registration.
        """
        with self._lock:
            if channel in self._subscribers and callback in self._subscribers[channel]:
                self._subscribers[channel].remove(callback)
        logger.info(f"Unsubscribed callback from channel '{channel}'")
