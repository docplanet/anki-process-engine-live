#!/usr/bin/env python3
"""Receives captured slide images from the browser and writes them to disk.

capture_views.js reads each field of view off the viewer's canvas and POSTs it here as a base64
data-URL, so the image bytes go straight to a file instead of back through whatever is driving the
browser.

Two details make the POST work from a page served over https:
  - 127.0.0.1 counts as a potentially-trustworthy origin, so it is exempt from mixed-content blocking
  - a text/plain body is a CORS-simple request, so the browser sends no preflight

    python3 tools/capture_server.py [output_dir] [port]

Scope: it binds 127.0.0.1 and `basename`s the filename, so nothing can be written outside
output_dir. But `Access-Control-Allow-Origin: *` is what lets the viewer page post at all, which
means any page open in the browser can also write a file into output_dir while this is running.
Start it for a capture run and stop it after.
"""
import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8799
os.makedirs(OUTPUT_DIR, exist_ok=True)


class CaptureHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        # Private Network Access: a page on a public origin reaching 127.0.0.1 is preflighted even
        # when the request is otherwise CORS-simple, and the browser drops it unless this comes back.
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Liveness check, so a caller can confirm the server is up before capturing."""
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        try:
            request = json.loads(self.rfile.read(content_length))
            filename = os.path.basename(request["name"])       # basename: never write outside OUTPUT_DIR
            image_bytes = base64.b64decode(request["dataurl"].split(",", 1)[1])
            with open(os.path.join(OUTPUT_DIR, filename), "wb") as out:
                out.write(image_bytes)
            reply = {"ok": True, "name": filename, "bytes": len(image_bytes)}
        except Exception as error:
            reply = {"ok": False, "error": repr(error)}
        body = json.dumps(reply).encode()
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        """Silence the per-request log; the JSON reply already reports each capture."""


if __name__ == "__main__":
    print(f"writing captures to {OUTPUT_DIR} on :{PORT}", flush=True)
    HTTPServer(("127.0.0.1", PORT), CaptureHandler).serve_forever()
