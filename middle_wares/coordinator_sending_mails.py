# middle_wares/coordinator_sending_mails.py
from controller.sending_mails_controller import SendMailController

class Coordinator:
    def __init__(self, bus):
        self.bus = bus
        self.view = None
        self.controller = SendMailController(bus)

        # Register event listener for logs
        self.bus.subscribe("log", self._on_log_received)

    def set_view(self, view):
        self.view = view

    def _on_log_received(self, message):
        """Receive log messages from controller and forward to view."""
        if self.view:
            self.view.display_log(message)

    def start_sending(self, info):
        """Trigger sending through the event bus."""
        self.bus.publish("start_sending", info)

    def stop_sending(self):
        """Trigger stop through the event bus."""
        self.bus.publish("stop_sending")
