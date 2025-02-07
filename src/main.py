
from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')
import gi
gi.require_version("Gtk", "4.0")
gi.require_version('Gtk4LayerShell', '1.0')
gi.require_version('WebKit', '6.0')
from cairo import RectangleInt, Region
from gi.repository import Gtk, Gdk
from gi.repository import Gtk4LayerShell as LayerShell
import threading

import time
from model_manager import ModelManager
from puppets import Live2DDesktopPuppet
from wminterfaces import HyprlandInterface
from interaction_server import InteractionServer

def on_activate(app):
    # Create window 
    window = Gtk.Window(application=app)
    window.set_default_size(1920, 1080)
    LayerShell.init_for_window(window)
    LayerShell.set_layer(window, LayerShell.Layer.OVERLAY)
    window.present()
    
    # Apply css for transparency
    css = Gtk.CssProvider()
    css.load_from_string(
        """
        .main-window {
            background-color: transparent;
        }
        """
    )
    Gtk.StyleContext.add_provider_for_display(
        window.get_display(),
        css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    ) 
    window.add_css_class("main-window")
    
    # Remove input area
    surface = window.get_surface()
    if surface is None:
        return
    Gdk.Surface.set_input_region(surface, Region(RectangleInt(0, 0, 0, 0)))

    # Create puppet
    model_manager = ModelManager(Live2DDesktopPuppet(), HyprlandInterface())
    server = InteractionServer(model_manager)
    widget = model_manager.get_gtk_widget() 
    window.set_child(widget)

    server.start_interaction_server()
    threading.Thread(target=update_loop, args=(surface,model_manager)).start()

def update_loop(surface, model_manager):
    while True:
        x,y,w,h = model_manager.get_updated_area()
        Gdk.Surface.set_input_region(surface, Region(RectangleInt(x,y,w,h)))
        model_manager.update_cursor_position()
        time.sleep(0.1)


app = Gtk.Application(application_id='moe.nyarchlinux.desktop-puppet')
app.connect('activate', on_activate)
app.run(None)
