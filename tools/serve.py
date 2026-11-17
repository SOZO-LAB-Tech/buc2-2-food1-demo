"""Local preview server that behaves like Cloudflare Pages for this site.

Real files are served as-is (/s/v1/, /overview/, /assets/...). Any other path
(/, /surveys, /surveys/v1, /inbox, ...) gets index.html, the Hub, which reads
the path and shows the matching page. Cloudflare Pages does the same when the
site has no top-level 404.html.

Usage: python3 tools/serve.py [port]   (default 4173)
"""
import functools
import http.server
import os
import sys
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        if not os.path.exists(self.translate_path(self.path)):
            last = urlsplit(self.path).path.rstrip("/").rsplit("/", 1)[-1]
            if "." not in last:  # a route, not a missing asset
                self.path = "/index.html"
        return super().send_head()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4173
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=ROOT))
    print(f"Serving {ROOT} at http://localhost:{port}")
    server.serve_forever()
