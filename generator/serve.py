#!/usr/bin/env python3
"""Local preview server that mimics GitHub Pages URL resolution:
/path -> /path.html, /dir/ -> /dir/index.html, unknown -> /404.html (status 404).

    python3 generator/serve.py [port]
"""
import http.server
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8130


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def send_head(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        fs = os.path.join(ROOT, path.lstrip("/"))
        if not os.path.exists(fs) or (os.path.isdir(fs) and not path.endswith("/")):
            if os.path.exists(fs.rstrip("/") + ".html"):
                self.path = path.rstrip("/") + ".html"
            elif os.path.isdir(fs) and os.path.exists(os.path.join(fs, "index.html")):
                self.path = path.rstrip("/") + "/index.html"
            elif not os.path.exists(fs):
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                body = open(os.path.join(ROOT, "404.html"), "rb").read()
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return None
        return super().send_head()

    def guess_type(self, path):
        if path.endswith((".txt", ".md")):
            return "text/plain; charset=utf-8"
        return super().guess_type(path)


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
