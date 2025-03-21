from model_manager import ModelManager
from interaction_handler import start_interaction_api, stop_interaction_api


class InteractionServer:
    def __init__(self, model_manager: ModelManager, window) -> None:
        self.model_manager = model_manager
        self.window = None 
        self.changefunc = None
        pass

    def get_expressions(self) -> list[str]:
        return self.model_manager.get_expressions()

    def set_expression(self, expression: str) -> None:
        return self.model_manager.set_expression(expression)

    def get_motions(self) -> list[str]:
        return self.model_manager.get_motions()

    def set_motion(self, motion: str) -> None:
        return self.model_manager.do_motion(motion)
    
    def set_mouth_amplitude(self, amplitude: float) -> None:
        return self.model_manager.set_mouth_amplitude(amplitude)

    def set_settings(self, settings: dict) -> None:
        return self.model_manager.set_settings(settings)

    def start_interaction_server(self, address:str="localhost") -> None:
        self.httpd, self.server_thread = start_interaction_api(self, address, 42943)

    def kill_interaction_server(self) -> None:
        stop_interaction_api(self.httpd)

    def change_overlay_type(self, overlay_type: str) -> None:
        if self.changefunc is not None and self.window is not None:
            self.changefunc(overlay_type, self.window)
    
    def set_change_func(self, changefunc, window):
        self.changefunc = changefunc
        self.window = window

