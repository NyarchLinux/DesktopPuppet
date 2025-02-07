from puppets import DesktopPuppet
from wminterfaces import WMInterface

class ModelManager:
    def __init__(self, puppet: DesktopPuppet, wm_interface: WMInterface) -> None:
        self.puppet = puppet
        self.wm_interface = wm_interface

    def get_gtk_widget(self):
        return self.puppet.get_gtk_widget()

    def get_updated_area(self) -> tuple[int, int, int, int]:
        self.puppet.update_area()
        return self.puppet.model_x, self.puppet.model_y, self.puppet.model_width, self.puppet.model_height

    def update_cursor_position(self):
        x, y = self.wm_interface.get_cursor_position()
        self.puppet.look(x, y)

    def get_expressions(self):
        return self.puppet.get_expressions()

    def set_expression(self, expression: str) -> None:
        self.puppet.set_expression(expression)

    def set_mouth_amplitude(self, amplitude: float) -> None:
        self.puppet.set_mouth_amplitude(amplitude)

    def set_settings(self, settings: dict) -> None:
        self.puppet.set_settings(settings)
