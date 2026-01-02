import pytest
from unittest.mock import MagicMock
from src.core.event_manager import EventManager
from src.models.enums import EventType

def test_subscribe_and_notify():
    """Testet das Abonnieren und Benachrichtigen von Events."""
    manager = EventManager()
    callback = MagicMock()

    manager.subscribe(EventType.UPDATE, callback)
    manager.notify(EventType.UPDATE, "test_data")

    callback.assert_called_once_with("test_data")

def test_unsubscribe():
    """Testet das Abbestellen von Events."""
    manager = EventManager()
    callback = MagicMock()

    manager.subscribe(EventType.UPDATE, callback)
    manager.unsubscribe(EventType.UPDATE, callback)
    manager.notify(EventType.UPDATE, "test_data")

    callback.assert_not_called()

def test_multiple_subscribers():
    """Testet mehrere Subscriber für dasselbe Event."""
    manager = EventManager()
    callback1 = MagicMock()
    callback2 = MagicMock()

    manager.subscribe(EventType.LOG, callback1)
    manager.subscribe(EventType.LOG, callback2)
    manager.notify(EventType.LOG, "log_message")

    callback1.assert_called_once_with("log_message")
    callback2.assert_called_once_with("log_message")

def test_notify_with_error():
    """Testet, dass ein Fehler in einem Callback andere nicht blockiert."""
    manager = EventManager()

    def error_callback(*args):
        raise ValueError("Boom")

    callback2 = MagicMock()

    manager.subscribe(EventType.UPDATE, error_callback)
    manager.subscribe(EventType.UPDATE, callback2)

    # Sollte nicht crashen
    manager.notify(EventType.UPDATE)

    callback2.assert_called_once()

