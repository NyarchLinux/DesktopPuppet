import argparse
import os
import sys
import urllib.error
import urllib.request
from ctypes import CDLL

from wminterfaces.wminterface import WMInterface
CDLL('libgtk4-layer-shell.so')
import gi
gi.require_version("Gtk", "4.0")
gi.require_version('Gtk4LayerShell', '1.0')
gi.require_version('WebKit', '6.0')
from cairo import RectangleInt, Region
from gi.repository import Gtk, Gdk, GLib
from gi.repository import Gtk4LayerShell as LayerShell
import threading
from functools import partial

import time
from model_manager import ModelManager
from puppets import Live2DDesktopPuppet
from wminterfaces import HyprlandInterface, get_wm_interface
from interaction_server import InteractionServer

# Cursor polling runs fast while the pointer moves and backs off once it has
# been still for IDLE_AFTER seconds, so an idle desktop costs little.
POLL_INTERVAL = 0.1
IDLE_POLL_INTERVAL = 0.5
IDLE_AFTER = 2.0
INPUT_REGION_REFRESH = 3.0

def find_monitor(display, connector):
    monitors = display.get_monitors()
    for i in range(monitors.get_n_items()):
        monitor = monitors.get_item(i)
        if monitor.get_connector() == connector:
            return monitor
    return None

def select_monitor(window, wm_interface, connector):
    monitor = find_monitor(window.get_display(), connector) if connector else None
    if connector and monitor is None:
        print(f"Monitor {connector} not found, using the focused monitor", file=sys.stderr)
    if monitor is None:
        wm_interface.set_target_monitor(None, None)
        return
    geometry = monitor.get_geometry()
    if not wm_interface.set_target_monitor(
        connector, (geometry.x, geometry.y, geometry.width, geometry.height)
    ):
        print(f"The desktop did not accept monitor {connector}", file=sys.stderr)
    if LayerShell.is_layer_window(window):
        LayerShell.set_monitor(window, monitor)

def changefunc(overlay_type, window, wm_interface):
    if not LayerShell.is_layer_window(window):
        if not wm_interface.set_overlay_type(overlay_type):
            print(f"Could not set overlay type: {overlay_type}", file=sys.stderr)
        return
    if overlay_type == "background":
        LayerShell.set_layer(window, LayerShell.Layer.BACKGROUND)
        print("background")
    elif overlay_type == "overlay":
        LayerShell.set_layer(window, LayerShell.Layer.OVERLAY)
        print("overlay")

def on_activate(app):
    # Configure the complete surface before mapping it. Presenting the window
    # earlier lets GTK draw its default opaque background for the first frame
    # and means the initial 1x1 default size may be kept by the compositor.
    window = Gtk.Window(application=app, title="nyarchpet")
    # GNOME has no layer shell; the pet stays a regular toplevel there and the
    # Shell extension keeps it on top and sized to the work area.
    if LayerShell.is_supported():
        LayerShell.init_for_window(window)
        LayerShell.set_layer(window, LayerShell.Layer.OVERLAY)
    window.set_decorated(False)

    # A user GTK stylesheet can contain a global `window` background at
    # GTK_STYLE_PROVIDER_PRIORITY_USER. Transparency is functional here, not
    # cosmetic, so install this narrowly-scoped rule just above that priority.
    # Fully transparent (`alpha: 0`) makes Hyprland discard the layer surface,
    # leaving a 200x200 invisible window. One percent is not visible and keeps
    # the surface mapped so the model can draw.
    css = Gtk.CssProvider()
    css.load_from_string(
        """
        window.main-window {
            background: rgba(0, 0, 0, 0.01);
            background-color: rgba(0, 0, 0, 0.01);
        }
        """
    )
    Gtk.StyleContext.add_provider_for_display(
        window.get_display(),
        css,
        Gtk.STYLE_PROVIDER_PRIORITY_USER + 1
    )
    window.add_css_class("main-window")

    # Create puppet
    wm_interface = get_wm_interface()
    select_monitor(window, wm_interface, ARGS.monitor)
    model_manager = ModelManager(Live2DDesktopPuppet(), wm_interface)
    server = InteractionServer(model_manager, window)
    server.set_change_func(partial(changefunc, wm_interface=wm_interface), window)
    widget = model_manager.get_gtk_widget()
    # Get monitor resolution
    dim = model_manager.get_monitor_dimensions() 
    w = dim[0] 
    h = dim[1]
    window.set_default_size(w, h)
    window.set_child(widget)
    window.present()

    # Remove input area until the model reports its visible bounds.
    surface = window.get_surface()
    if surface is None:
        return
    Gdk.Surface.set_input_region(surface, Region(RectangleInt(0, 0, 0, 0)))

    server.start_interaction_server()
    threading.Thread(target=update_loop, args=(surface,model_manager)).start()

def set_input_region(surface, area):
    Gdk.Surface.set_input_region(surface, Region(RectangleInt(*area)))
    return GLib.SOURCE_REMOVE

def update_loop(surface, model_manager):
    last_input_region = None
    last_region_time = 0.0
    last_motion_time = time.monotonic()
    while os.path.exists(LOCKFILE):
        now = time.monotonic()
        if model_manager.update_cursor_position():
            last_motion_time = now
        area = model_manager.get_updated_area()
        if area != last_input_region or now - last_region_time >= INPUT_REGION_REFRESH:
            GLib.idle_add(set_input_region, surface, area)
            last_input_region = area
            last_region_time = now
        idle = now - last_motion_time >= IDLE_AFTER
        time.sleep(IDLE_POLL_INTERVAL if idle else POLL_INTERVAL)
    GLib.idle_add(app.quit)


parser = argparse.ArgumentParser(description="Show the desktop puppet.")
parser.add_argument(
    "--monitor",
    help="Connector name of the monitor to show the puppet on, such as DP-1. "
         "Defaults to the focused monitor.",
)
ARGS = parser.parse_args()

# Create lock file
LOCKFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nyarchlinux-desktop-puppet.lock")
f = open(LOCKFILE, "w+")
f.close()
app = Gtk.Application(application_id='moe.nyarchlinux.desktop-puppet')
app.connect('activate', on_activate)
status = app.run(None)
# A second launch registers the same application id. GTK then returns without
# activating this process, so an empty exit looks like a crash to the GUI.
if not app.get_is_registered():
    try:
        urllib.request.urlopen("http://localhost:42943/expressions", timeout=1)
    except (OSError, urllib.error.URLError):
        print(
            "Puppet exited before showing a window. "
            "Another application may already own moe.nyarchlinux.desktop-puppet.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("A puppet is already running.", file=sys.stderr)
    sys.exit(0)
sys.exit(status)
