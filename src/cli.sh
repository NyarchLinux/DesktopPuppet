#!/usr/bin/env python3
import argparse
import json
import os
import sys
import requests

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

    args = parser.parse_args()

    # Construct the base URL for the API.
    base_url = f"http://{args.host}:{args.port}"

    if args.command == "get-expressions":
        get_expressions(base_url)
    elif args.command == "set-expression":
        set_expression(base_url, args.expression)
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
