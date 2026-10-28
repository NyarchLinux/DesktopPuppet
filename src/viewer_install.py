"""Install the Live2D viewer and its default model when needed."""

import os
import subprocess
import tempfile


VIEWER_URL = "https://github.com/NyarchLinux/live2d-lipsync-viewer.git"


def viewer_path_for_project(project_root):
    """Use the bundled location when writable, or per-user data for packages."""
    bundled = os.path.join(project_root, "avatars", "live2d", "web")
    if os.path.isdir(bundled) or os.access(project_root, os.W_OK):
        return bundled

    data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(data_home, "desktoppuppet", "live2d", "web")


def ensure_viewer_installed(viewer_path):
    """Install into a temporary directory, then expose the complete viewer."""
    if os.path.isdir(viewer_path):
        return False

    parent = os.path.dirname(os.path.abspath(viewer_path))
    os.makedirs(parent, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".viewer-download-", dir=parent) as staging:
        checkout = os.path.join(staging, "web")
        subprocess.run(["git", "clone", VIEWER_URL, checkout], check=True)
        os.rename(checkout, viewer_path)
    return True
