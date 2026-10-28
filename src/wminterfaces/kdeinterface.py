import subprocess
import re
from .wminterface import WMInterface

class KDEInterface (WMInterface):
    def __init__(self) -> None:
        super().__init__()
        self.x = 0
        self.y = 0
        self._last_cursor = (0, 0)

    def get_cursor_position(self) -> tuple[int, int]:
        try:
            mouse_pos = subprocess.check_output(["kdotool", "getmouselocation"])
        except (OSError, subprocess.CalledProcessError):
            return self._last_cursor
        string = mouse_pos.decode("utf-8")
        match = re.search(r'x:(\d+)\s+y:(\d+)', string)
        if match is None:
            return self._last_cursor
        x = int(match.group(1))
        y = int(match.group(2))
        self._last_cursor = self._get_relative_coords(x, y)
        return self._last_cursor
    
    def get_active_monitor_resolution(self) -> tuple[int, int]:
        if self.target_geometry is not None:
            self.x, self.y, width, height = self.target_geometry
            return width, height
        return 1920, 1000

    def _get_relative_coords(self, x:int, y:int) -> tuple[int, int]:
        return x-self.x,y-self.y
