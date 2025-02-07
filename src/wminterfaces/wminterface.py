class WMInterface:
    def __init__(self) -> None:
        pass

    def get_cursor_position(self) -> tuple[int, int]:
        return 0,0

    def get_active_monitor_resolution(self) -> tuple[int, int]:
        return 1920, 1080
