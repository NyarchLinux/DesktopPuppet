import subprocess
import json
from .wminterface import WMInterface

class HyprlandInterface(WMInterface):
    def __init__(self) -> None:
        super().__init__()
        self.x = 0
        self.y = 0

    def get_cursor_position(self) -> tuple[int, int]:
        mouse_pos = subprocess.check_output(["hyprctl", "cursorpos"]) 
        x, y = mouse_pos.decode("utf-8").split(", ")
        x = int(x)
        y = int(y)
        pos = self._get_relative_coords(x, y)
        print(pos)
        return pos 
    def get_active_monitor_resolution(self) -> tuple[int, int]:
        monitors = subprocess.check_output(["hyprctl", "monitors", "-j"])
        monitors = json.loads(monitors.decode("utf-8"))
        for monitor in monitors:
            if monitor["focused"]:
                self.x = monitor["x"]
                self.y = monitor["y"]
                print(self.x, self.y)
                return monitor["width"], monitor["height"]
        return 1920, 1080

    def _get_relative_coords(self, x:int, y:int) -> tuple[int, int]:
        return x-self.x,y-self.y
