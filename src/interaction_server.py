from model_manager import ModelManager
from interaction_handler import start_interaction_api, stop_interaction_api


class InteractionServer:
    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager
        pass

    def get_expressions(self) -> list[str]:
        return self.model_manager.get_expressions()

    def set_expression(self, expression: str) -> None:
        return self.model_manager.set_expression(expression)

    def set_mouth_amplitude(self, amplitude: float) -> None:
        return self.model_manager.set_mouth_amplitude(amplitude)

    def set_webserser_url(self, url: str) -> None:
        pass

    def set_model_path(self, path: str) -> None:
        pass

    def set_settings(self, settings: dict) -> None:
        return self.model_manager.set_settings(settings)

    def start_interaction_server(self, address:str="localhost") -> None:
        self.httpd, self.server_thread = start_interaction_api(self, address, 42943)

    def kill_interaction_server(self) -> None:
        stop_interaction_api(self.httpd)
