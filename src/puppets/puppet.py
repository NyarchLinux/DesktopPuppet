from gi.repository import Gtk

class DesktopPuppet():
    def __init__(self) -> None:
        # Model dimensions
        self.model_x = 0
        self.model_y = 0
        self.model_width = 0
        self.model_height = 0
        # Settings 
        self.settings = {}
        pass
    
    def get_gtk_widget(self) -> Gtk.Widget:
        """Get the GTK Widget to display

        Returns:
            Gtk.Widget: The GTK Widget 
        """
        return Gtk.Box()

    def look(self, x, y):
        """Look in the direction given

        Args:
            x (): x coordinate on the monitor 
            y (): y coordinate on the monitor 
        """
        pass

    def update_area(self):
        """Update the model area, update using the model dimensions properties"""
        pass

    def get_expressions(self) -> list[str]:
        return []

    def set_expression(self, expression: str) -> None:
        pass

    def set_mouth_amplitude(self, amplitude: float) -> None:
        pass
    
    def set_settings(self, settings:dict) -> None:
        for setting in settings:
            self.settings[setting] = settings[setting]

