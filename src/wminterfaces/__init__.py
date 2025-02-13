from .wminterface import WMInterface
from .hyprlandinterface import HyprlandInterface
import os

def get_wm_interface() -> WMInterface:
    if os.getenv("XDG_CURRENT_DESKTOP") == "hyprland":
        return HyprlandInterface()
    else:
        return WMInterface()



__all__ = ["WMInterface", "HyprlandInterface", "get_wm_interface"]
