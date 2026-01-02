from typing import Dict, List, Callable, Any
from src.models.enums import EventType
from src.utils.logger import setup_logging

logger = setup_logging()

class EventManager:
    """
    Verwaltet Abonnements und Benachrichtigungen für Events.
    """
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable[..., None]]] = {}

    def subscribe(self, event_type: EventType, callback: Callable[..., None]) -> None:
        """Registriert einen Callback für ein bestimmtes Event."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        if callback not in self.listeners[event_type]:
            self.listeners[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[..., None]) -> None:
        """Entfernt einen Callback für ein bestimmtes Event."""
        if event_type in self.listeners and callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)

    def notify(self, event_type: EventType, *args: Any, **kwargs: Any) -> None:
        """Benachrichtigt alle Listener eines Events."""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Fehler beim Ausführen des Listeners für {event_type}: {e}")

