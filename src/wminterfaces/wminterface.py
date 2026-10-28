class WMInterface:
    def __init__(self) -> None:
        self.target_connector: str | None = None
        self.target_geometry: tuple[int, int, int, int] | None = None

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
        if self.target_geometry is not None:
            return self.target_geometry[2], self.target_geometry[3]
        return 1920, 1080

    def set_target_monitor(self, connector: str | None, geometry: tuple[int, int, int, int] | None) -> bool:
        """Choose the monitor the puppet is shown on. Call before the window is shown.

        Args:
            connector: Connector name such as "DP-1", or None for the focused monitor
            geometry: (x, y, width, height) of that monitor in logical pixels, or None

        Returns:
            bool: True if the desktop accepted the monitor
        """
        self.target_connector = connector
        self.target_geometry = geometry
        return True

    def set_overlay_type(self, overlay_type: str) -> bool:
        """Keep the puppet above ("overlay") or below ("background") other windows
        on desktops without layer shell

        Returns:
            bool: True if the desktop applied the overlay type
        """
        return False
