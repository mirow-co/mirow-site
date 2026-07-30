# -*- coding: utf-8 -*-
"""Screenshot de pagina inteira via CDP (Chrome headless), sem dependencias externas.

Uso: python shot.py <url> <saida.png> [largura] [aos-off]
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


class WS:
    def __init__(self, url):
        assert url.startswith("ws://")
        rest = url[5:]
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.s = socket.create_connection((host, int(port)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        req = ("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, hostport, key))
        self.s.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.rest = buf.split(b"\r\n\r\n", 1)[1]

    def _recv(self, n):
        while len(self.rest) < n:
            chunk = self.s.recv(65536)
            if not chunk:
                raise IOError("socket fechado")
            self.rest += chunk
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, obj):
        data = json.dumps(obj).encode()
        hdr = bytearray([0x81])
        n = len(data)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126)
            hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127)
            hdr += struct.pack(">Q", n)
        mask = os.urandom(4)
        hdr += mask
        self.s.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        payload = b""
        while True:
            b0, b1 = self._recv(2)
            fin = b0 & 0x80
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._recv(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._recv(8))[0]
            payload += self._recv(n)
            if fin:
                break
        return json.loads(payload.decode())

    def call(self, mid, method, params=None):
        self.send({"id": mid, "method": method, "params": params or {}})
        while True:
            msg = self.recv()
            if msg.get("id") == mid:
                return msg


def main():
    url, out = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
    aos_off = "aos-off" in sys.argv[4:]
    profile = tempfile.mkdtemp(prefix="cdpshot")
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                             "--remote-debugging-port=9333", "--user-data-dir=" + profile,
                             "--window-size=%d,900" % width, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9333/json", timeout=5))
                for t in tabs:
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if ws_url:
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ws_url:
            raise SystemExit("nao consegui falar com o Chrome")
        ws = WS(ws_url)
        ws.call(1, "Page.enable")
        ws.call(2, "Page.navigate", {"url": url})
        time.sleep(7)
        if aos_off:
            # o tema usa AOS (data-aos) e mantem os elementos invisiveis ate entrarem
            # na viewport — no screenshot de pagina inteira isso esconde titulos e
            # secoes. Esta opcao revela tudo, so para o QA.
            ws.call(4, "Runtime.evaluate", {"expression": (
                "var s=document.createElement('style');"
                "s.textContent='[data-aos]{opacity:1!important;transform:none!important;"
                "visibility:visible!important}';document.head.appendChild(s);"
                "document.querySelectorAll('[data-aos]').forEach(function(e){"
                "e.classList.add('aos-animate')});true")})
            time.sleep(1)
        ev = ws.call(3, "Runtime.evaluate", {
            "expression": "Math.max(document.body.scrollHeight,"
                          "document.documentElement.scrollHeight)",
            "returnByValue": True})
        h = int(ev["result"]["result"]["value"])
        h = max(900, min(h, 20000))
        print("altura da pagina: %d" % h)
        r = ws.call(5, "Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": h, "scale": 1}})
        if "result" not in r:
            raise SystemExit("CDP erro: %s" % r)
        with open(out, "wb") as f:
            f.write(base64.b64decode(r["result"]["data"]))
        print("%s  (%dx%d)" % (out, width, h))
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
