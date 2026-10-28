from gi.repository import GLib
from puppets import DesktopPuppet
from wminterfaces import WMInterface

class ModelManager:
    def __init__(self, puppet: DesktopPuppet, wm_interface: WMInterface) -> None:
        self.puppet = puppet
        self.wm_interface = wm_interface
        self._last_cursor: tuple[int, int] | None = None

    def get_gtk_widget(self):
        return self.puppet.get_gtk_widget()

    def get_updated_area(self) -> tuple[int, int, int, int]:
        """Return the last known model area and queue a refresh on the GTK thread."""
        GLib.idle_add(self._update_area)
        return self.puppet.model_x, self.puppet.model_y, self.puppet.model_width, self.puppet.model_height

    def _update_area(self) -> bool:
        self.puppet.update_area()
        return GLib.SOURCE_REMOVE

    def update_cursor_position(self) -> bool:
        """Poll the cursor and make the puppet look at it.

        Safe to call from a worker thread: the puppet is only updated on the
        GTK thread, and only when the cursor moved.

        Returns:
            bool: True if the cursor moved since the last poll
        """
        position = self.wm_interface.get_cursor_position()
        if position == self._last_cursor:
            return False
        self._last_cursor = position
        GLib.idle_add(self._look, *position)
        return True

    def _look(self, x: int, y: int) -> bool:
        # A puppet that is still loading drops the position, so poll it again
        # instead of waiting for the cursor to move.
        if self.puppet.look(x, y) is False:
            self._last_cursor = None
        return GLib.SOURCE_REMOVE

    def get_motions(self) -> list[str]:
        return self.puppet.get_motions()

    def do_motion(self, motion: str) -> None:
        self.puppet.do_motion(motion)

    def get_expressions(self):
        return self.puppet.get_expressions()

    def set_expression(self, expression: str) -> None:
        self.puppet.set_expression(expression)

    def set_mouth_amplitude(self, amplitude: float) -> None:
        self.puppet.set_mouth_amplitude(amplitude)

    def set_settings(self, settings: dict) -> None:
        self.puppet.set_settings(settings)

    def get_monitor_dimensions(self) -> tuple[int, int]:
        return self.wm_interface.get_active_monitor_resolution()
