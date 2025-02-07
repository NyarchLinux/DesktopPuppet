import subprocess
import json
from .wminterface import WMInterface

class HyprlandInterface(WMInterface):
    def __init__(self) -> None:
        super().__init__()

    def get_cursor_position(self) -> tuple[int, int]:
        mouse_pos = subprocess.check_output(["hyprctl", "cursorpos"]) 
        x, y = mouse_pos.decode("utf-8").split(", ")
        x = int(x)
        y = int(y)
        return x,y

    def get_active_monitor_resolution(self) -> tuple[int, int]:
        monitors = subprocess.check_output(["hyprctl", "monitors", "-j"])
        monitors = json.loads(monitors.decode("utf-8"))
        for monitor in monitors:
            if monitor["active"]:
                return monitor["width"], monitor["height"]
        return 1920, 1080
