#!/usr/bin/env python3
"""Serves this folder over plain HTTP with HEAD and Range support (what ESPHome's Nextion uploader needs).
Run from the folder holding thermostat_us.tft:   python3 tft_serve.py      (Ctrl+C to stop)"""
import http.server, os, re, socket

PORT = 80

class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"          # keep-alive across the uploader's chunk requests
    def send_head(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            self.send_error(404); return None
        size = os.path.getsize(path)
        f = open(path, "rb")
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            start = int(m.group(1)) if m.group(1) else size - int(m.group(2))
            end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
            end = min(end, size - 1)
            if start > end:
                f.close(); self.send_error(416); return None
            f.seek(start)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            length = end - start + 1
        else:
            self.send_response(200)
            length = size
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._left = length
        return f

    def copyfile(self, src, dst):
        while self._left > 0:
            chunk = src.read(min(65536, self._left))
            if not chunk:
                break
            dst.write(chunk)
            self._left -= len(chunk)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()}  {self.command} {self.path}  Range={self.headers.get('Range', '-')}  -> {args[1] if len(args) > 1 else ''}")

class Server(http.server.ThreadingHTTPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1)); ip = s.getsockname()[0]
    except OSError:
        ip = "<this-mac-ip>"
    finally:
        s.close()
    print(f"tft_url: \"http://{ip}:{PORT}/thermostat_us.tft\"")
    Server(("", PORT), Handler).serve_forever()