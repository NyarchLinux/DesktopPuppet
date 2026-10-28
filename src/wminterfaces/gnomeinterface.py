import re
import sys
from gi.repository import Gio, GLib
from .wminterface import WMInterface

EXTENSION_UUID = "nyarchpet@nyarchlinux.moe"
_DBUS_ID = re.sub(r"[^a-zA-Z0-9_]", "_", EXTENSION_UUID)
_BUS_NAME = "org.gnome.Shell"
_OBJECT_PATH = f"/org/gnome/Shell/Extensions/{_DBUS_ID}"
_INTERFACE = f"org.gnome.Shell.Extensions.{_DBUS_ID}"
_FALLBACK_RESOLUTION = (1920, 1000)


class GnomeInterface (WMInterface):
    def __init__(self) -> None:
        super().__init__()
        self.x = 0
        self.y = 0
        self._last_cursor = (0, 0)
        self._warned = False
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error as error:
            self._bus = None
            self._warn(error.message)

    def _warn(self, message: str) -> None:
        # The update loop polls the cursor several times per second, so report a missing
        # extension once instead of flooding the log.
        if self._warned:
            return
        self._warned = True
        print(
            f"Cannot reach the {EXTENSION_UUID} GNOME Shell extension: {message}\n"
            f"Install it and enable it with `gnome-extensions enable {EXTENSION_UUID}` "
            "(see the README, Gnome Specific Instructions).",
            file=sys.stderr,
        )

    def _call(self, method: str, parameters: GLib.Variant | None = None, reply_type: str = "(a{sv})"):
        if self._bus is None:
            return None
        try:
            reply = self._bus.call_sync(
                _BUS_NAME, _OBJECT_PATH, _INTERFACE, method, parameters,
                GLib.VariantType(reply_type), Gio.DBusCallFlags.NONE, 1000, None,
            )
        except GLib.Error as error:
            self._warn(error.message)
            return None
        self._warned = False
        return reply.unpack()[0]

    def get_cursor_position(self) -> tuple[int, int]:
        position = self._call("GetPosition")
        if position is None or "x" not in position or "y" not in position:
            return self._last_cursor
        self._last_cursor = self._get_relative_coords(int(position["x"]), int(position["y"]))
        return self._last_cursor

    def get_active_monitor_resolution(self) -> tuple[int, int]:
        monitor = self._call("GetMonitor")
        if monitor is None or not all(key in monitor for key in ("x", "y", "width", "height")):
            return _FALLBACK_RESOLUTION
        self.x = int(monitor["x"])
        self.y = int(monitor["y"])
        return int(monitor["width"]), int(monitor["height"])

    def set_target_monitor(self, connector: str | None, geometry: tuple[int, int, int, int] | None) -> bool:
        super().set_target_monitor(connector, geometry)
        # Always sent, even for the focused monitor, so a connector requested
        # by an earlier puppet does not stick in the extension.
        return bool(self._call("SetMonitor", GLib.Variant("(s)", (connector or "",)), "(b)"))

    def set_overlay_type(self, overlay_type: str) -> bool:
        return bool(self._call("SetOverlay", GLib.Variant("(s)", (overlay_type,)), "(b)"))

    def _get_relative_coords(self, x:int, y:int) -> tuple[int, int]:
        return x-self.x,y-self.y
