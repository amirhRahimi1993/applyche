# events/event_bus.py
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event_name, callback):
        """Register a callback for a specific event."""
        self._subscribers[event_name].append(callback)

    def publish(self, event_name, data=None):
        """Notify all subscribers for the event."""
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                callback(data)
