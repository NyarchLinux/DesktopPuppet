import subprocess
import json
import re
from .wminterface import WMInterface

class KDEInterface (WMInterface):
    def __init__(self) -> None:
        super().__init__()
        self.x = 0
        self.y = 0

    def get_cursor_position(self) -> tuple[int, int]:
        script = "kdotool getmouselocation"
        mouse_pos = subprocess.check_output(["bash","-c", script]) 
        string = mouse_pos.decode("utf-8")
        match = re.search(r'x:(\d+)\s+y:(\d+)', string)
        if match is None:
            return 0,0
        x = int(match.group(1))
        y = int(match.group(2))
        pos = self._get_relative_coords(x, y)
        return pos 
    
    def get_active_monitor_resolution(self) -> tuple[int, int]:
        return 1920, 1000

    def _get_relative_coords(self, x:int, y:int) -> tuple[int, int]:
        return x-self.x,y-self.y
