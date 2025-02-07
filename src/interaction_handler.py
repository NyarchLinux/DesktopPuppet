from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

class InteractionHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/expressions':
            expressions = self.server.interaction_server.get_expressions()
            response = json.dumps(expressions).encode('utf-8')

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        # Read the request body.
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # Route POST requests based on the URL path.
        if self.path == '/expression':
            expr = data.get('expression')
            print("Expression", expr)
            if expr is None:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing "expression" field')
                return
            self.server.interaction_server.set_expression(expr)
            self.send_response(200)
            self.end_headers()

        elif self.path == '/mouth':
            amplitude = data.get('amplitude')
            if amplitude is None:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing "amplitude" field')
                return
            self.server.interaction_server.set_mouth_amplitude(amplitude)
            self.send_response(200)
            self.end_headers()

        elif self.path == '/webserver_url':
            url = data.get('url')
            if url is None:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing "url" field')
                return
            self.server.interaction_server.set_webserser_url(url)
            self.send_response(200)
            self.end_headers()

        elif self.path == '/model_path':
            path = data.get('path')
            if path is None:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing "path" field')
                return
            self.server.interaction_server.set_model_path(path)
            self.send_response(200)
            self.end_headers()
        elif self.path == '/set_settings':
            settings = data.get('settings')
            print(settings)
            if settings is None:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing "settings" field')
                return
            self.server.interaction_server.set_settings(settings)
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def start_interaction_api(interaction_server, host='localhost', port=8000):
    """
    Starts the HTTP API on a separate thread.

    Returns:
        httpd: The HTTPServer instance.
        server_thread: The thread running the server.
    """
    httpd = HTTPServer((host, port), InteractionHandler)
    httpd.interaction_server = interaction_server
    def serve():
        print(f"Starting server on {host}:{port}")
        httpd.serve_forever()

    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    return httpd, server_thread

def stop_interaction_api(httpd):
    """
    Stops the HTTP server.
    """
    print("Shutting down server...")
    httpd.shutdown()      # Stop serve_forever()
    httpd.server_close()  # Close the underlying socket
    print("Server stopped.")

