#!/usr/bin/env python3
import argparse
import json
import os
import sys
import requests
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlencode
from viewer_install import ensure_viewer_installed as install_viewer, viewer_path_for_project

def get_expressions(base_url):
    url = f"{base_url}/expressions"
    try:
        response = requests.get(url)
        response.raise_for_status()
        expressions = response.json()
        print(json.dumps(expressions, indent=2))
    except requests.RequestException as err:
        print(f"Error getting expressions: {err}")
        sys.exit(1)

def set_expression(base_url, expression):
    url = f"{base_url}/expression"
    data = {"expression": expression}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Expression set successfully.")
    except requests.RequestException as err:
        print(f"Error setting expression: {err}")
        sys.exit(1)

def get_motions(base_url):
    url = f"{base_url}/motions"
    try:
        response = requests.get(url)
        response.raise_for_status()
        expressions = response.json()
        print(json.dumps(expressions, indent=2))
    except requests.RequestException as err:
        print(f"Error getting motions: {err}")
        sys.exit(1)

def set_motion(base_url, expression):
    url = f"{base_url}/motion"
    data = {"motion": expression}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Motion set successfully.")
    except requests.RequestException as err:
        print(f"Error setting expression: {err}")
        sys.exit(1)

def set_mouth_amplitude(base_url, amplitude):
    url = f"{base_url}/mouth"
    data = {"amplitude": amplitude}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Mouth amplitude set successfully.")
    except requests.RequestException as err:
        print(f"Error setting mouth amplitude: {err}")
        sys.exit(1)

def set_webserver_url(base_url, url_val):
    url = f"{base_url}/webserver_url"
    data = {"url": url_val}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Webserver URL set successfully.")
    except requests.RequestException as err:
        print(f"Error setting webserver URL: {err}")
        sys.exit(1)

def set_model_path(base_url, model_path):
    url = f"{base_url}/model_path"
    data = {"path": model_path}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Model path set successfully.")
    except requests.RequestException as err:
        print(f"Error setting model path: {err}")
        sys.exit(1)

def set_settings(base_url, settings_str):
    # Try to parse the provided JSON string
    try:
        settings_obj = json.loads(settings_str)
    except json.JSONDecodeError:
        print("Provided settings is not valid JSON.")
        sys.exit(1)
    url = f"{base_url}/set_settings"
    data = {"settings": settings_obj}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Settings updated successfully.")
    except requests.RequestException as err:
        print(f"Error updating settings: {err}")
        sys.exit(1)

def set_overlay(base_url, overlay):
    url = f"{base_url}/overlay"
    data = {"overlay": overlay}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Overlay updated successfully.")
    except requests.RequestException as err:
        print(f"Error updating overlay: {err}")
        sys.exit(1)

def get_available_models(models_dir):
    file_list = []
    for root, _, files in os.walk(models_dir):
        for file in files:
            if file.endswith('.model3.json') or file.endswith('.model.json'):
                file_name = file.rstrip('.model3.json').rstrip('.model.json')
                relative_path = os.path.relpath(os.path.join(root, file), models_dir)
                file_list.append((file_name, relative_path))
    return file_list

def ensure_viewer_installed(viewer_path):
    if not os.path.isdir(viewer_path):
        print("Downloading Live2D viewer and Arch model...")
        install_viewer(viewer_path)
        print("Viewer installed successfully.")
    else:
        print("Viewer already installed.")

def start_viewer_webserver(viewer_path, model, scale, bg, extra_w, extra_h):
    folder_path = viewer_path
    class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            path = super().translate_path(path)
            return os.path.join(folder_path, os.path.relpath(path, os.getcwd()))
    
    httpd = HTTPServer(('127.0.0.1', 0), CustomHTTPRequestHandler)
    port = httpd.server_address[1]
    viewer_url = f"http://localhost:{port}?{urlencode({'model': model, 'bg': bg, 'scale': scale})}"
    
    def run_server():
        httpd.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    print(f"Viewer webserver started on port {port}")
    return httpd, viewer_url

def start_puppet(monitor=None):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lockfile = os.path.join(project_root, "src", "nyarchlinux-desktop-puppet.lock")
    if os.path.isfile(lockfile):
        os.remove(lockfile)
    
    print("Starting DesktopPuppet...")
    command = ["python3", os.path.join(project_root, "src", "main.py")]
    if monitor:
        command += ["--monitor", monitor]
    process = subprocess.Popen(command)
    return process, lockfile

def stop_puppet():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lockfile = os.path.join(project_root, "src", "nyarchlinux-desktop-puppet.lock")
    
    if not os.path.isfile(lockfile):
        print("No puppet process is running (lockfile not found).")
        return False
    
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python3.*main.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(["kill", pid], check=True)
                    print(f"Terminated process {pid}")
                except subprocess.CalledProcessError:
                    pass
        
        os.remove(lockfile)
        print("DesktopPuppet stopped successfully.")
        return True
    except Exception as e:
        print(f"Error stopping puppet: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to interface with the Interaction API."
    )
    parser.add_argument(
        "--host", default="localhost", help="API server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=42943, help="API server port (default: 42943)"
    )

    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Command: get-expressions
    subparsers.add_parser("get-expressions", help="Retrieve expressions from the API.")

    # Command: set-expression
    expr_parser = subparsers.add_parser("set-expression", help="Set an expression.")
    expr_parser.add_argument("expression", help="Expression to set.")

    # Command: get-motions
    subparsers.add_parser("get-motions", help="Retrieve motions from the API.")

    # Command: set-expression
    expr_parser = subparsers.add_parser("set-motion", help="Set a motion.")
    expr_parser.add_argument("motion", help="Motion to set.")
    # Command: set-mouth
    mouth_parser = subparsers.add_parser("set-mouth", help="Set mouth amplitude.")
    mouth_parser.add_argument("amplitude", type=float, help="Mouth amplitude (e.g. 0.5)")

    # Command: set-webserver-url
    web_parser = subparsers.add_parser("set-webserver-url", help="Set the webserver URL.")
    web_parser.add_argument("url", help="Webserver URL.")

    # Command: set-model-path
    model_parser = subparsers.add_parser("set-model-path", help="Set the model path.")
    model_parser.add_argument("path", help="Path to the model.")

    # Command: set-settings
    settings_parser = subparsers.add_parser("set-settings", help="Set configuration settings.")
    settings_parser.add_argument(
        "settings",
        help=(
            "Settings as a JSON string. "
            "Alternatively, provide a path to a JSON file containing the settings."
        ),
    )

    # Command: set-overlay
    overlay_parser = subparsers.add_parser("set-overlay", help="Change overlay type.")
    overlay_parser.add_argument("overlay", help="Overlay type to set.")

    # Command: start
    start_parser = subparsers.add_parser("start", help="Start the desktop puppet.")
    start_parser.add_argument("--model", default="Arch/arch chan model0.model3.json", help="Live2D model to use.")
    start_parser.add_argument("--scale", type=float, default=1.0, help="Zoom scale (default: 1.0).")
    start_parser.add_argument("--extra-w", type=float, default=0.56, help="Extra scaling width (default: 0.56).")
    start_parser.add_argument("--extra-h", type=float, default=1.0, help="Extra scaling height (default: 1.0).")
    start_parser.add_argument("--bg", default="transparent", help="Background color (default: transparent).")
    start_parser.add_argument("--monitor", help="Monitor connector to show the puppet on, such as DP-1 (default: focused monitor).")

    # Command: stop
    subparsers.add_parser("stop", help="Stop the desktop puppet.")

    args = parser.parse_args()

    # Construct the base URL for the API.
    base_url = f"http://{args.host}:{args.port}"

    if args.command == "get-expressions":
        get_expressions(base_url)
    elif args.command == "set-expression":
        set_expression(base_url, args.expression)
    elif args.command == "get-motions":
        get_motions(base_url)
    elif args.command == "set-motion":
        set_motion(base_url, args.motion)
    elif args.command == "set-mouth":
        set_mouth_amplitude(base_url, args.amplitude)
    elif args.command == "set-webserver-url":
        set_webserver_url(base_url, args.url)
    elif args.command == "set-model-path":
        set_model_path(base_url, args.path)
    elif args.command == "set-settings":
        # If the argument is a file path, read its contents.
        if os.path.exists(args.settings):
            with open(args.settings, "r", encoding="utf-8") as f:
                settings_str = f.read()
        else:
            settings_str = args.settings
        set_settings(base_url, settings_str)
    elif args.command == "set-overlay":
        set_overlay(base_url, args.overlay)
    elif args.command == "stop":
        stop_puppet()
    elif args.command == "start":
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        webview_path = viewer_path_for_project(project_root)
        
        ensure_viewer_installed(webview_path)
        
        httpd, viewer_url = start_viewer_webserver(webview_path, args.model, args.scale, args.bg, args.extra_w, args.extra_h)
        
        puppet_process, lockfile = start_puppet(args.monitor)
        
        import time
        try:
            while True:
                try:
                    settings = {
                        "address": viewer_url,
                        "model": args.model,
                        "scale": args.scale * 100,
                        "extra_w": args.extra_w,
                        "extra_h": args.extra_h
                    }
                    requests.post(f'{base_url}/set_settings', json={'settings': settings})
                    print("Settings updated successfully.")
                    break
                except requests.RequestException:
                    print("Waiting for puppet to start...")
                    time.sleep(1)
            
            print("DesktopPuppet is running. Press Ctrl+C to stop.")
            puppet_process.wait()
        except KeyboardInterrupt:
            print("\nStopping...")
            puppet_process.terminate()
            httpd.shutdown()
            if os.path.isfile(lockfile):
                os.remove(lockfile)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
