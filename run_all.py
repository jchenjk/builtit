"""One-shot dev runner: serves the frontend on :5173 and proxies /api to FastAPI on :8000.

Usage:
    cd diy-builder
    pip install -r backend/requirements.txt
    python run_all.py

Then open http://localhost:5173/ in your browser.
"""
import os
import sys
import threading
import time
import http.server
import socketserver
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "frontend")
BACKEND_DIR = os.path.join(ROOT, "backend")

API_PORT = 8000
WEB_PORT = 5173


def start_backend():
    """Start uvicorn in a background thread."""
    sys.path.insert(0, BACKEND_DIR)
    import uvicorn
    from app.main import app
    config = uvicorn.Config(app, host="127.0.0.1", port=API_PORT, log_level="info")
    server = uvicorn.Server(config)
    server.run()


class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=FRONTEND_DIR, **kw)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._proxy("GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self._proxy("POST")
        return self.send_error(405)

    def _proxy(self, method):
        url = f"http://127.0.0.1:{API_PORT}{self.path}"
        body = None
        if method == "POST":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
        req = urllib.request.Request(url, data=body, method=method)
        for h in ("Content-Type", "Accept"):
            v = self.headers.get(h)
            if v: req.add_header(h, v)
        try:
            with urllib.request.urlopen(req) as r:
                self.send_response(r.status)
                for k, v in r.getheaders():
                    if k.lower() in {"transfer-encoding", "connection"}: continue
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(r.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Backend unreachable: {e}".encode())

    def log_message(self, fmt, *args):
        pass  # quieter


def main():
    # Inject a hint that the frontend should call /api on the same origin
    # (the static handler already does that by default — API_BASE defaults to "")
    print(f"→ Starting backend on http://127.0.0.1:{API_PORT}")
    t = threading.Thread(target=start_backend, daemon=True)
    t.start()

    # Wait for backend
    for _ in range(40):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{API_PORT}/api/health", timeout=0.5)
            break
        except Exception:
            time.sleep(0.25)
    else:
        print("Backend did not start in time. Exiting.")
        sys.exit(1)
    print("→ Backend is up.")

    print(f"→ Serving frontend on http://localhost:{WEB_PORT}")
    print(f"→ Open: http://localhost:{WEB_PORT}/")
    with socketserver.TCPServer(("", WEB_PORT), FrontendHandler) as httpd:
        httpd.allow_reuse_address = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nBye.")


if __name__ == "__main__":
    main()
