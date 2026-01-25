#!/usr/bin/env python3

import os
import subprocess
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlencode

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, GLib, Gio

import requests


class PuppetController:
    """Handles communication with the puppet API."""

    def __init__(self, host="localhost", port=42943):
        self.base_url = f"http://{host}:{port}"
        self._connected = False

    def is_connected(self):
        """Check if the puppet API is reachable."""
        try:
            response = requests.get(f"{self.base_url}/expressions", timeout=1)
            self._connected = response.status_code == 200
            return self._connected
        except requests.RequestException:
            self._connected = False
            return False

    def get_expressions(self):
        """Get available expressions from the puppet."""
        try:
            response = requests.get(f"{self.base_url}/expressions", timeout=2)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return []

    def set_expression(self, expression):
        """Set an expression on the puppet."""
        try:
            response = requests.post(
                f"{self.base_url}/expression",
                json={"expression": expression},
                timeout=2
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def get_motions(self):
        """Get available motions from the puppet."""
        try:
            response = requests.get(f"{self.base_url}/motions", timeout=2)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {}

    def set_motion(self, motion):
        """Set a motion on the puppet."""
        try:
            response = requests.post(
                f"{self.base_url}/motion",
                json={"motion": motion},
                timeout=2
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def set_settings(self, settings):
        """Update puppet settings."""
        try:
            response = requests.post(
                f"{self.base_url}/set_settings",
                json={"settings": settings},
                timeout=2
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def set_overlay(self, overlay_type):
        """Set the overlay type."""
        try:
            response = requests.post(
                f"{self.base_url}/overlay",
                json={"overlay": overlay_type},
                timeout=2
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False


class PuppetLauncher:
    """Handles launching the puppet process."""

    def __init__(self):
        self.process = None
        self.httpd = None
        self.lockfile = None
        self.webview_path = None
        self.models_dir = None
        self.log_file = None

        # Set paths
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.webview_path = os.path.join(project_root, "avatars", "live2d", "web")
        self.models_dir = os.path.join(self.webview_path, "models")
        self.main_py = os.path.join(project_root, "src", "main.py")
        self.cli_sh = os.path.join(project_root, "src", "cli.sh")
        self.lockfile = os.path.join(project_root, "src", "nyarchlinux-desktop-puppet.lock")

    def get_available_models(self):
        """Get list of available models from the models directory."""
        models = []
        if not os.path.isdir(self.models_dir):
            return models

        for root, _, files in os.walk(self.models_dir):
            for file in files:
                if file.endswith('.model3.json') or file.endswith('.model.json'):
                    file_name = file.rstrip('.model3.json').rstrip('.model.json')
                    relative_path = os.path.relpath(os.path.join(root, file), self.models_dir)
                    models.append((file_name, relative_path))
        return models

    def ensure_viewer_installed(self):
        """Ensure the Live2D viewer is installed."""
        viewer_path = self.webview_path
        if not os.path.isdir(viewer_path):
            return False, "Viewer directory not found"
        return True, "Viewer installed"

    def start_viewer_webserver(self, model, scale, bg, extra_w, extra_h):
        """Start the viewer webserver."""
        folder_path = self.webview_path

        class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
            def translate_path(self, path):
                path = super().translate_path(path)
                return os.path.join(folder_path, os.path.relpath(path, os.getcwd()))
            def log_message(self, format, *args):
                pass  # Suppress HTTP logs

        self.httpd = HTTPServer(('127.0.0.1', 0), CustomHTTPRequestHandler)
        port = self.httpd.server_address[1]

        def run_server():
            self.httpd.serve_forever()

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()

        viewer_url = f"http://localhost:{port}?{urlencode({'model': model, 'bg': bg, 'scale': scale})}"
        return viewer_url

    def start_puppet(self):
        """Start the puppet main process."""
        # Remove lockfile if exists
        if os.path.isfile(self.lockfile):
            os.remove(self.lockfile)

        # Get the src directory for proper module imports
        src_dir = os.path.dirname(self.main_py)
        project_root = os.path.dirname(src_dir)

        # Open a log file to capture output (keep it open)
        log_path = os.path.join(project_root, "puppet.log")
        self.log_file = open(log_path, "w")

        # Start the main.py process directly (cli.sh logic is handled in GUI)
        env = os.environ.copy()
        env['PYTHONPATH'] = src_dir

        self.process = subprocess.Popen(
            ["python", self.main_py],
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=src_dir
        )
        return self.process

    def stop_puppet(self):
        """Stop the puppet process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None

        if os.path.isfile(self.lockfile):
            os.remove(self.lockfile)

        # Close and clean up log file
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None

        log_path = self.get_log_path()
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
            except Exception:
                pass

    def is_running(self):
        """Check if puppet process is running."""
        return self.process is not None and self.process.poll() is None

    def get_log_path(self):
        """Get the path to the puppet log file."""
        project_root = os.path.dirname(os.path.dirname(self.main_py))
        return os.path.join(project_root, "puppet.log")

    def flush_log(self):
        """Flush the log file to ensure all output is written."""
        if self.log_file:
            try:
                self.log_file.flush()
            except Exception:
                pass


class DesktopPuppetWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, app):
        super().__init__(application=app, title="DesktopPuppet Controller")
        self.set_default_size(900, 700)

        self.launcher = PuppetLauncher()
        self.controller = PuppetController()
        self.viewer_url = None
        self.current_model_path = None
        self._monitor_thread = None
        self._stop_monitor = False

        self._setup_ui()
        self._load_models()

    def _setup_ui(self):
        """Setup the user interface."""
        # Main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(self.main_box)

        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)

        # Status bar
        self.status_bar = Adw.Banner()
        self.status_bar.set_revealed(False)
        self.main_box.append(self.status_bar)

        # Main content - ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        self.main_box.append(scrolled)

        # Content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        scrolled.set_child(content_box)

        # ===== Model Selection Section =====
        model_group = Adw.PreferencesGroup(title="Model Selection")
        content_box.append(model_group)

        # Model folder row
        self.folder_row = Adw.ActionRow(
            title="Models Folder",
            subtitle=self.launcher.models_dir
        )
        self.folder_row.add_suffix(Gtk.Image.new_from_icon_name("folder-open-symbolic"))
        self.folder_row.set_activatable(True)
        self.folder_row.connect("activated", self._on_browse_folder)
        model_group.add(self.folder_row)

        # Model dropdown
        model_row = Adw.ComboRow(
            title="Select Model",
            subtitle="Choose a Live2D model to load"
        )
        model_row.set_model(Gtk.StringList.new([]))
        self.model_dropdown = model_row
        model_group.add(model_row)

        # ===== Launch Parameters Section =====
        params_group = Adw.PreferencesGroup(title="Launch Parameters")
        content_box.append(params_group)

        # Scale/Zoom
        self.scale_row = Adw.SpinRow(
            title="Zoom Scale",
            subtitle="Overall zoom level",
            adjustment=Gtk.Adjustment.new(1.0, 0.1, 5.0, 0.1, 0.5, 0)
        )
        self.scale_row.set_digits(2)
        params_group.add(self.scale_row)

        # Extra Width
        self.extra_w_row = Adw.SpinRow(
            title="Extra Width Scale",
            subtitle="Additional horizontal scaling",
            adjustment=Gtk.Adjustment.new(0.56, 0.0, 2.0, 0.01, 0.1, 0)
        )
        self.extra_w_row.set_digits(2)
        params_group.add(self.extra_w_row)

        # Extra Height
        self.extra_h_row = Adw.SpinRow(
            title="Extra Height Scale",
            subtitle="Additional vertical scaling",
            adjustment=Gtk.Adjustment.new(1.0, 0.0, 2.0, 0.01, 0.1, 0)
        )
        self.extra_h_row.set_digits(2)
        params_group.add(self.extra_h_row)

        # Background color
        bg_row = Adw.ComboRow(
            title="Background",
            subtitle="Background color for the viewer"
        )
        bg_list = Gtk.StringList.new(["transparent", "white", "black", "#000000", "#FFFFFF"])
        bg_row.set_model(bg_list)
        bg_row.set_selected(0)
        self.bg_row = bg_row
        params_group.add(bg_row)

        # ===== Launch Control Section =====
        launch_group = Adw.PreferencesGroup(title="Puppet Control")
        content_box.append(launch_group)

        # Launch button
        self.launch_button = Gtk.Button(label="Launch Puppet")
        self.launch_button.add_css_class("suggested-action")
        self.launch_button.set_halign(Gtk.Align.START)
        self.launch_button.connect("clicked", self._on_launch_clicked)
        launch_group.add(self.launch_button)

        # ===== Expression Control Section =====
        self.expression_group = Adw.PreferencesGroup(title="Expression Control")
        self.expression_group.set_sensitive(False)
        content_box.append(self.expression_group)

        # Expression dropdown
        self.expression_row = Adw.ComboRow(
            title="Set Expression",
            subtitle="Choose a facial expression"
        )
        self.expression_row.set_model(Gtk.StringList.new([]))
        self.expression_row.connect("notify::selected", self._on_expression_selected)
        self.expression_group.add(self.expression_row)

        # ===== Motion Control Section =====
        self.motion_group = Adw.PreferencesGroup(title="Motion Control")
        self.motion_group.set_sensitive(False)
        content_box.append(self.motion_group)

        # Motion group selector
        self.motion_group_selector = Adw.ComboRow(
            title="Motion Group",
            subtitle="Select motion category"
        )
        self.motion_group_selector.set_model(Gtk.StringList.new([]))
        self.motion_group_selector.connect("notify::selected", self._on_motion_group_selected)
        self.motion_group.add(self.motion_group_selector)

        # Motion selector
        self.motion_selector = Adw.ComboRow(
            title="Select Motion",
            subtitle="Choose a motion to play"
        )
        self.motion_selector.set_model(Gtk.StringList.new([]))
        self.motion_selector.connect("notify::selected", self._on_motion_selected)
        self.motion_group.add(self.motion_selector)

        # ===== Overlay Control Section =====
        self.overlay_group = Adw.PreferencesGroup(title="Display Mode")
        self.overlay_group.set_sensitive(False)
        content_box.append(self.overlay_group)

        # Overlay selector
        overlay_row = Adw.ComboRow(
            title="Overlay Type",
            subtitle="How the puppet is displayed"
        )
        overlay_list = Gtk.StringList.new(["overlay", "background"])
        overlay_row.set_model(overlay_list)
        overlay_row.set_selected(0)
        overlay_row.connect("notify::selected", self._on_overlay_selected)
        self.overlay_row = overlay_row
        self.overlay_group.add(overlay_row)

    def _load_models(self):
        """Load available models."""
        models = self.launcher.get_available_models()
        model_list = Gtk.StringList.new([m[0] for m in models])
        self.model_dropdown.set_model(model_list)

        # Store model paths
        self._model_paths = {m[0]: m[1] for m in models}

    def _on_browse_folder(self, widget):
        """Handle folder browse button."""
        import platform
        folder_path = self.launcher.models_dir
        
        if folder_path and not os.path.exists(folder_path):
            self._show_status("Models folder does not exist", "error")
            return
        
        if not folder_path:
            self._show_status("No models folder set", "error")
            return
        
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", folder_path], check=True)
            else:
                subprocess.run(["xdg-open", folder_path], check=True)
        except Exception as e:
            self._show_status(f"Failed to open folder: {e}", "error")

    def _on_launch_clicked(self, button):
        """Handle launch button click."""
        if self.launcher.is_running():
            self._stop_puppet()
        else:
            self._launch_puppet()

    def _launch_puppet(self):
        """Launch the puppet."""
        # Check viewer installation
        installed, message = self.launcher.ensure_viewer_installed()
        if not installed:
            self._show_status(message, "error")
            return

        # Get selected model
        model_name = self.model_dropdown.get_selected_item()
        if not model_name:
            self._show_status("Please select a model first", "error")
            return

        model_path = self._model_paths.get(model_name.get_string())
        if not model_path:
            self._show_status("Invalid model selected", "error")
            return

        # Store current model path for settings
        self.current_model_path = model_path

        # Get parameters
        scale = self.scale_row.get_value()
        extra_w = self.extra_w_row.get_value()
        extra_h = self.extra_h_row.get_value()
        bg = self.bg_row.get_selected_item().get_string()

        # Disable launch button
        self.launch_button.set_label("Launching...")
        self.launch_button.set_sensitive(False)

        # Start webserver
        try:
            self.viewer_url = self.launcher.start_viewer_webserver(
                model_path, scale, bg, extra_w, extra_h
            )
        except Exception as e:
            self._show_status(f"Failed to start webserver: {e}", "error")
            self.launch_button.set_label("Launch Puppet")
            self.launch_button.set_sensitive(True)
            return

        # Start puppet process
        try:
            self.launcher.start_puppet()
        except Exception as e:
            self._show_status(f"Failed to start puppet: {e}", "error")
            self.launch_button.set_label("Launch Puppet")
            self.launch_button.set_sensitive(True)
            return

        # Update UI
        self.launch_button.set_label("Stop Puppet")
        self.launch_button.add_css_class("destructive-action")
        self.launch_button.remove_css_class("suggested-action")
        self.launch_button.set_sensitive(True)

        self._show_status("Puppet launched, waiting for connection...", "info")

        # Start monitoring thread
        self._start_monitor()

    def _stop_puppet(self):
        """Stop the puppet."""
        self._stop_monitor = True

        self.launcher.stop_puppet()
        self.viewer_url = None
        self.current_model_path = None

        # Update UI
        self.launch_button.set_label("Launch Puppet")
        self.launch_button.remove_css_class("destructive-action")
        self.launch_button.add_css_class("suggested-action")

        # Disable controls
        self.expression_group.set_sensitive(False)
        self.motion_group.set_sensitive(False)
        self.overlay_group.set_sensitive(False)

        self._show_status("Puppet stopped", "info")

    def _start_monitor(self):
        """Start monitoring thread for puppet connection."""
        self._stop_monitor = False

        def monitor():
            connected = False
            while not self._stop_monitor and self.launcher.is_running():
                if self.controller.is_connected():
                    if not connected:
                        GLib.idle_add(self._on_connected)
                        connected = True
                else:
                    connected = False
                time.sleep(1)

            if self._stop_monitor:
                return

            # Process died
            if self.launcher.is_running() is False:
                GLib.idle_add(self._on_process_died)

        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()

    def _on_connected(self):
        """Handle successful connection to puppet."""
        self._show_status("Connected to puppet!", "success")

        # Enable controls
        self.expression_group.set_sensitive(True)
        self.motion_group.set_sensitive(True)
        self.overlay_group.set_sensitive(True)

        # Apply initial settings
        settings = {
            "address": self.viewer_url,
            "model": self.current_model_path,
            "scale": self.scale_row.get_value() * 100,
            "extra_w": self.extra_w_row.get_value(),
            "extra_h": self.extra_h_row.get_value()
        }
        self.controller.set_settings(settings)

        # Load expressions and motions after 5 seconds
        GLib.timeout_add_seconds(5, self._load_expressions_and_motions)

    def _load_expressions_and_motions(self):
        """Load expressions and motions from puppet."""
        self._load_expressions()
        self._load_motions()
        return False

    def _on_process_died(self):
        """Handle puppet process death."""
        # Flush log before stopping
        self.launcher.flush_log()
        self._stop_puppet()

        # Try to read log file for error details
        log_path = self.launcher.get_log_path()
        error_msg = "Puppet process died unexpectedly"
        try:
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    log_content = f.read()
                    if log_content:
                        # Show last few lines of log
                        lines = log_content.strip().split('\n')
                        last_lines = lines[-5:] if len(lines) > 5 else lines
                        error_msg = f"Puppet died. Log: {' '.join(last_lines)}"
        except Exception:
            pass

        self._show_status(error_msg, "error")

    def _load_expressions(self):
        """Load expressions from puppet."""
        expressions = self.controller.get_expressions()
        if expressions:
            expr_list = Gtk.StringList.new(expressions)
            self.expression_row.set_model(expr_list)

    def _load_motions(self):
        """Load motions from puppet."""
        motions = self.controller.get_motions()
        if motions:
            groups = list(motions.keys())
            group_list = Gtk.StringList.new(groups)
            self.motion_group_selector.set_model(group_list)

            # Store motion data
            self._motion_data = motions

            # Load first group's motions
            if groups:
                self._load_motion_group(groups[0])

    def _load_motion_group(self, group_name):
        """Load motions for a specific group."""
        if group_name in self._motion_data:
            motions = self._motion_data[group_name]
            motion_list = Gtk.StringList.new(motions)
            self.motion_selector.set_model(motion_list)

    def _on_motion_group_selected(self, row, pspec):
        """Handle motion group selection change."""
        selected = row.get_selected_item()
        if selected:
            self._load_motion_group(selected.get_string())

    def _on_expression_selected(self, row, pspec):
        """Apply selected expression."""
        expression = self.expression_row.get_selected_item()
        if expression:
            expr = expression.get_string()
            if self.controller.set_expression(expr):
                self._show_status(f"Applied expression: {expr}", "success")
            else:
                self._show_status(f"Failed to apply expression", "error")

    def _on_motion_selected(self, row, pspec):
        """Play selected motion."""
        group = self.motion_group_selector.get_selected_item()
        motion = self.motion_selector.get_selected_item()

        if group and motion:
            # Format: group/motion
            motion_path = f"{group.get_string()}/{motion.get_string()}"
            if self.controller.set_motion(motion_path):
                self._show_status(f"Playing motion: {motion_path}", "success")
            else:
                self._show_status(f"Failed to play motion", "error")

    def _on_overlay_selected(self, row, pspec):
        """Apply overlay type."""
        overlay = self.overlay_row.get_selected_item()
        if overlay:
            overlay_type = overlay.get_string()
            if self.controller.set_overlay(overlay_type):
                self._show_status(f"Set overlay to: {overlay_type}", "success")
            else:
                self._show_status("Failed to set overlay", "error")

    def _show_status(self, message, message_type="info"):
        """Show status message."""
        self.status_bar.set_title(message)
        self.status_bar.set_revealed(True)

        # Auto-hide after 5 seconds for non-errors
        if message_type != "error":
            GLib.timeout_add_seconds(5, lambda: self.status_bar.set_revealed(False))

    def close_request(self):
        """Handle window close request."""
        self._stop_monitor = True
        self.launcher.stop_puppet()
        return False


class DesktopPuppetApp(Adw.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id="moe.nyarchlinux.desktop-puppet-gui",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        """Activate the application."""
        win = DesktopPuppetWindow(self)
        win.present()


def main():
    """Main entry point."""
    app = DesktopPuppetApp()
    app.run(None)


if __name__ == "__main__":
    main()
