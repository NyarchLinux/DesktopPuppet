#!/bin/bash
# Launcher script for DesktopPuppet GUI Controller

cd "$(dirname "$0")"
python3 src/gui_controller.py "$@"
