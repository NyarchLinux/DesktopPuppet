import json
import os
import socket
import subprocess
import sys
from .wminterface import WMInterface


def _find_socket() -> str | None:
    signature = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
    if not signature:
        return None
    # Hyprland moved its sockets from /tmp to the runtime dir in 0.40.
    for base in (os.getenv("XDG_RUNTIME_DIR", ""), "/tmp"):
        path = os.path.join(base, "hypr", signature, ".socket.sock")
        if os.path.exists(path):
            return path
    return None


class HyprlandInterface(WMInterface):
    def __init__(self) -> None:
        super().__init__()
        self.x = 0
        self.y = 0
        self._last_cursor = (0, 0)
        self._socket_path = _find_socket()

    def _request(self, command: str, as_json: bool = False) -> str:
        """Run a hyprctl command over the IPC socket.

        The cursor is polled several times per second, and spawning hyprctl
        costs a process per poll, so the socket is used whenever it exists.
        """
        if self._socket_path is not None:
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    sock.connect(self._socket_path)
                    sock.sendall(f"{'j/' if as_json else ''}{command}".encode())
                    chunks = []
                    while chunk := sock.recv(8192):
                        chunks.append(chunk)
                return b"".join(chunks).decode("utf-8")
            except OSError:
                pass
        args = ["hyprctl", command] + (["-j"] if as_json else [])
        return subprocess.check_output(args).decode("utf-8")

    def get_cursor_position(self) -> tuple[int, int]:
        try:
            x, y = self._request("cursorpos").split(",")
            self._last_cursor = self._get_relative_coords(int(x), int(y))
        except (OSError, subprocess.CalledProcessError, ValueError):
            pass
        return self._last_cursor

    def get_active_monitor_resolution(self) -> tuple[int, int]:
        try:
            monitors = json.loads(self._request("monitors", as_json=True))
        except (OSError, subprocess.CalledProcessError, ValueError) as error:
            print(f"Cannot read Hyprland monitors: {error}", file=sys.stderr)
            return 1920, 1080
        for monitor in monitors:
            if self.target_connector is not None:
                selected = monitor["name"] == self.target_connector
            else:
                selected = monitor["focused"]
            if selected:
                self.x = monitor["x"]
                self.y = monitor["y"]
                return monitor["width"], monitor["height"]
        return 1920, 1080

    def _get_relative_coords(self, x:int, y:int) -> tuple[int, int]:
        return x-self.x,y-self.y
