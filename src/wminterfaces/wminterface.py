class WMInterface:
    def __init__(self) -> None:
        pass

    def get_cursor_position(self) -> tuple[int, int]:
        """Get cursor position relative to the puppet

        Returns:
            tuple [int, int]: (x, y)
        """
        return 0,0

    def get_active_monitor_resolution(self) -> tuple[int, int]:
        """Get the resolution of the monitor on which the puppet is displayed

        Returns:
            tuple [int, int]: (width, height)
        """
        return 1920, 1080
