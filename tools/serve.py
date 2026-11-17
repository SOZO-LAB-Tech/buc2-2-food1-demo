"""Local preview server that behaves like GitHub Pages for this site.

Real files are served as-is (/s/v1/, /overview/, /assets/...). Any other path
(/surveys, /surveys/v1, /inbox, ...) gets 404.html, a copy of the Hub, which
reads the path and shows the matching page. GitHub Pages does the same, with
HTTP status 404; visitors don't see a difference.

Usage: python3 tools/serve.py [port]   (default 4173)
"""
import functools
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        if os.path.exists(self.translate_path(self.path)):
            return super().send_head()
        try:
            f = open(os.path.join(ROOT, "404.html"), "rb")
        except OSError:
            return super().send_head()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(os.fstat(f.fileno()).st_size))
        self.end_headers()
        return f


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4173
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=ROOT))
    print(f"Serving {ROOT} at http://localhost:{port}")
    server.serve_forever()
