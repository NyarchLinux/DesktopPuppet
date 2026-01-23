from .wminterface import WMInterface
from .hyprlandinterface import HyprlandInterface
from .gnomeinterface import GnomeInterface
from .kdeinterface import KDEInterface
import os

def get_wm_interface() -> WMInterface:
    print(os.getenv("XDG_CURRENT_DESKTOP"))
    if os.getenv("XDG_CURRENT_DESKTOP") == "Hyprland":
        return HyprlandInterface()
    elif os.getenv("XDG_CURRENT_DESKTOP") == "GNOME":
        return GnomeInterface()
    elif os.getenv("XDG_CURRENT_DESKTOP") == "KDE":
        return KDEInterface()
    else:
        return WMInterface()



__all__ = ["WMInterface", "HyprlandInterface", "get_wm_interface"]
