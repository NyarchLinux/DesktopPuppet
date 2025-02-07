from .puppet import DesktopPuppet
from urllib.parse import urlencode, urljoin
from gi.repository import WebKit, Gdk, Gtk,  GLib
import threading 
import json


class Live2DDesktopPuppet(DesktopPuppet):
    _wait_js : threading.Event
    def __init__(self) -> None:
        super().__init__()
        self._wait_js = threading.Event()
        self._expressions_raw = []
        self.loaded = False
        # Extra settings
        self.address = "http://127.0.0.1:8000"
        self.extra_scale_w = 0.56
        self.extra_scale_h = 1
        self.model = None 
        self.scale = 1 

    def get_gtk_widget(self):
        self.box = Gtk.Box()
        return self.box

    def load_webview(self):
        webview = WebKit.WebView()
        scale = int(self.scale)/100
        q = urlencode({"model": self.model, "bg": "transparent", "scale": scale})
        print(q)
        webview.load_uri(urljoin(self.address, f"?{q}"))
        webview.set_hexpand(True)
        webview.set_vexpand(True)
        webview.set_background_color(Gdk.RGBA())
        def monitor_loading(wb, event):
            if event == WebKit.LoadEvent.FINISHED:
                self.loaded = True
        webview.connect("load-changed", monitor_loading)
        self.webview = webview

    def change_address(self):
        if hasattr(self, "webview"):
            self.box.remove(self.webview)
        self.load_webview()
        self.box.append(self.webview) 

    def look(self, x, y):
        if not self.loaded:
            return
        script = "model_proxy.focus({x}, {y});"
        script = script.format(x=x, y=y)
        self.webview.evaluate_javascript(script, len(script))

    def update_area(self):
        if not self.loaded:
            return
        script = """model_proxy.internalModel.width+ "," +  model_proxy.internalModel.height + "," + model_proxy.position._x + "," + model_proxy.position._y + "," + model_proxy.scale._x"""
        def update_position(obj, result):
            global model_x, model_y, model_width, model_height
            coord = self.webview.evaluate_javascript_finish(result)
            coord = coord.to_string().split(",")
            self.model_height = int(coord[1])
            self.model_width = int(coord[0])
            self.model_x = int(coord[2].split(".")[0])
            self.model_y = int(coord[3].split(".")[0])
            # Apply model scaling
            scale = float(coord[4])
            model_width2 = int(scale * self.model_width)
            model_height2 = int(scale * self.model_height)
            # Apply extra scale to fix model extra dimensions
            self.model_width = int(model_width2 * self.extra_scale_w)
            self.model_height = int(model_height2 * self.extra_scale_h)
            # Fix offset caused by the rescaling
            self.model_x = int(self.model_x + (model_width2 - self.model_width) / 2)
            self.model_y = int(self.model_y - (model_height2 - self.model_height) / 2)
       
        self.webview.evaluate_javascript(script, len(script), callback=update_position)

    def wait_emotions(self, object, result):
        if not self.loaded:
            return
        value = self.webview.evaluate_javascript_finish(result)
        self._expressions_raw = json.loads(value.to_string())
        self._wait_js.set()
    
    def get_expressions(self) -> list[str]:
        if not self.loaded:
            return []
        if len(self._expressions_raw) > 0:
            return self._expressions_raw
        self._expressions_raw = []
        script = "get_expressions_json()"
        self.webview.evaluate_javascript(script, len(script), callback=self.wait_emotions)
        self._wait_js.wait(3)
        print("EMOTIONS: " + str(self._expressions_raw))
        return self._expressions_raw 

    def set_expression(self, expression : str):
        if not self.loaded:
            return
        script = "set_expression('{}')".format(expression)
        self.webview.evaluate_javascript(script, len(script))

    def set_mouth_amplitude(self, amplitude: float) -> None:    
        if not self.loaded:
            return
        script = "set_mouth_y({})".format(amplitude)
        self.webview.evaluate_javascript(script, len(script))

    def set_settings(self, settings: dict) -> None:
        super().set_settings(settings)
        if "extra_scale_w" in settings:
            self.extra_scale_w = settings["extra_scale_w"]
        if "extra_scale_h" in settings:
            self.extra_scale_h = settings["extra_scale_h"]
        if "model" in settings:
            self.model = settings["model"]
        if "scale" in settings:
            self.scale = settings["scale"]
        if "extra_w" in settings:
            self.extra_scale_w = settings["extra_w"]
        if "extra_h" in settings:
            self.extra_scale_h = settings["extra_h"]
        if "address" in settings:
            self.address = settings["address"]
            GLib.idle_add(self.change_address)
